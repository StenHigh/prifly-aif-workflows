"""Review coverage evaluator and read-only Git candidate basis; Python stdlib only."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

DIGEST = re.compile(r'sha256:[0-9a-f]{64}\Z')
COMMIT = re.compile(r'[0-9a-f]{40}\Z')


class Invalid(ValueError):
    pass


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def digest(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def git(tree, *args):
    env = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0', 'GIT_NO_LAZY_FETCH': '1', 'GIT_TERMINAL_PROMPT': '0'}
    result = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false', '-C', str(tree), *args],
                            env=env, capture_output=True, timeout=60)
    if result.returncode:
        raise Invalid('Git candidate operation failed: ' + args[0])
    return result.stdout


def snapshot(tree, base):
    """Hash HEAD, logical index and tracked/nonignored untracked bytes/modes.

    Never follows symlinks; refuses gitlinks, unresolved index and unstable reads.
    Ignored build caches/dependencies and .git metadata are outside this basis.
    """
    tree = Path(tree).resolve(strict=True)
    if not COMMIT.fullmatch(base):
        raise Invalid('Expected a full SHA-1 base commit')
    git(tree, 'cat-file', '-e', base + '^{commit}')
    if Path(os.fsdecode(git(tree, 'rev-parse', '--show-toplevel').strip())).resolve() != tree:
        raise Invalid('Expected the claimed repository root')

    def once():
        head = git(tree, 'rev-parse', 'HEAD').decode().strip()
        if not COMMIT.fullmatch(head):
            raise Invalid('Unsupported Git object format')
        index = git(tree, 'ls-files', '--stage', '-z')
        paths = set()
        for entry in index.split(b'\0'):
            if not entry:
                continue
            metadata, path = entry.split(b'\t', 1)
            mode, blob, stage = metadata.split()
            if stage != b'0' or mode == b'160000':
                raise Invalid('Unmerged index or submodule requires separate candidate policy')
            paths.add(path)
        paths.update(p for p in git(tree, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0') if p)
        if len(paths) > 10000:
            raise Invalid('Candidate exceeds 10000 paths')
        records = []
        for raw in sorted(paths):
            relative = Path(os.fsdecode(raw))
            if relative.is_absolute() or '..' in relative.parts or '.git' in relative.parts:
                raise Invalid('Unsafe candidate path')
            current = tree
            for part in relative.parts[:-1]:
                current = current / part
                try:
                    if not stat.S_ISDIR(current.lstat().st_mode):
                        raise Invalid('Candidate parent is not a real directory')
                except FileNotFoundError:
                    # Removed directory: the tracked path below is missing.
                    break
            path = tree / relative
            record = {'path': base64.b64encode(raw).decode()}
            try:
                mode = path.lstat().st_mode
                record['mode'] = stat.S_IMODE(mode)
                if stat.S_ISLNK(mode):
                    record.update(kind='symlink', digest=digest(os.fsencode(os.readlink(path))))
                elif stat.S_ISREG(mode):
                    # O_NOFOLLOW closes the lstat/open symlink race on supported hosts.
                    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
                    with os.fdopen(fd, 'rb') as stream:
                        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                            raise Invalid('Candidate file changed kind')
                        hashed = hashlib.sha256()
                        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                            hashed.update(chunk)
                    record.update(kind='file', digest='sha256:' + hashed.hexdigest())
                else:
                    raise Invalid('Unsupported candidate file kind')
            except FileNotFoundError:
                record.update(kind='missing')
            records.append(record)
        return {'base_commit': base, 'head_commit': head, 'index_digest': digest(index), 'files_digest': digest(encoded(records))}

    first, second = once(), once()
    if first != second:
        raise Invalid('Candidate changed during snapshot')
    return {'algorithm': 'git-candidate/1', **first, 'digest': digest(encoded(first))}


def obj(value, fields, where):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise Invalid(where + ': missing or unknown fields')


def text(value, where):
    if not isinstance(value, str) or not value.strip() or len(value) > 4000:
        raise Invalid(where + ': expected nonempty text')


def candidate(value):
    obj(value, ('algorithm', 'base_commit', 'head_commit', 'index_digest', 'files_digest', 'digest'), 'candidate')
    if value['algorithm'] != 'git-candidate/1':
        raise Invalid('Unknown candidate algorithm')
    for field in ('base_commit', 'head_commit'):
        if not isinstance(value[field], str) or not COMMIT.fullmatch(value[field]):
            raise Invalid('Invalid candidate commit')
    for field in ('index_digest', 'files_digest', 'digest'):
        if not isinstance(value[field], str) or not DIGEST.fullmatch(value[field]):
            raise Invalid('Invalid candidate digest')
    basis = {k: value[k] for k in ('base_commit', 'head_commit', 'index_digest', 'files_digest')}
    if value['digest'] != digest(encoded(basis)):
        raise Invalid('Candidate digest does not bind its basis')


def request(value):
    obj(value, ('base_commit', 'round', 'checks', 'optional_policy', 'require_separate_session'), 'request')
    if not isinstance(value['base_commit'], str) or not COMMIT.fullmatch(value['base_commit']):
        raise Invalid('Invalid request base commit')
    if type(value['round']) is not int or not 1 <= value['round'] <= 10000:
        raise Invalid('Invalid round')
    if value['optional_policy'] not in ('ignore', 'stop') or type(value['require_separate_session']) is not bool:
        raise Invalid('Invalid review policy')
    if not isinstance(value['checks'], list) or not 1 <= len(value['checks']) <= 80:
        raise Invalid('Expected 1..80 checks')
    ids = set()
    for check in value['checks']:
        obj(check, ('id', 'description', 'method', 'required', 'enabled', 'applicable'), 'check')
        if not isinstance(check['id'], str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,79}', check['id']) or check['id'] in ids:
            raise Invalid('Invalid or duplicate declared check ID')
        ids.add(check['id'])
        text(check['description'], 'description')
        if check['method'] not in ('code', 'command', 'browser') or any(type(check[k]) is not bool for k in ('required', 'enabled', 'applicable')):
            raise Invalid('Invalid check method or policy')


def gate(status, findings, blocking=False, owner=False):
    return {'gate': 'review', 'status': status, 'blocking': blocking, 'blocking_owner_only': owner,
            'findings': findings, 'suggested_next': '/aif-fix' if blocking and not owner else 'continue'}


def evaluate(config, before, report, current, request_digest=None):
    """Check sealed composition and snapshots; observations remain host claims."""
    problems, warnings, defects = [], [], []
    try:
        request(config)
        candidate(before)
        candidate(current)
        if before['base_commit'] != config['base_commit'] or current != before:
            raise Invalid('Stale candidate: current HEAD/index/bytes/modes differ from captured basis')
        obj(report, ('round', 'request_digest', 'candidate', 'session', 'model_profile', 'model', 'checks'), 'report')
        expected_request = request_digest or digest(encoded(config) + b'\n')
        if report['request_digest'] != expected_request:
            raise Invalid('Report belongs to a different declared check composition/request')
        candidate(report['candidate'])
        if report['round'] != config['round'] or type(report['round']) is not int or report['candidate'] != before:
            raise Invalid('Report belongs to a different round or candidate')
        if report['session'] not in ('separate', 'shared', 'unavailable') or report['model_profile'] not in ('honoured', 'unavailable', 'declined'):
            raise Invalid('Invalid session/model report')
        if report['model_profile'] == 'honoured':
            text(report['model'], 'actual model')
        elif report['model'] is not None:
            raise Invalid('Unavailable/declined model must not claim an actual model')
        if config['require_separate_session'] and report['session'] != 'separate':
            problems.append('Required separate reader session unavailable; model choice is a distinct property')
        if report['model_profile'] != 'honoured':
            warnings.append('Model profile ' + report['model_profile'] + '; independent model not established')
        if not isinstance(report['checks'], list) or len(report['checks']) > 80:
            raise Invalid('Invalid reported check list')
        entries = {}
        for entry in report['checks']:
            obj(entry, ('id', 'status', 'result', 'reason', 'evidence'), 'reported check')
            if not isinstance(entry['id'], str) or entry['id'] in entries:
                raise Invalid('Duplicate reported check ID')
            entries[entry['id']] = entry
        if set(entries) != {x['id'] for x in config['checks']}:
            raise Invalid('Missing or unknown reported checks')
        for spec in config['checks']:
            check = entries[spec['id']]
            status = check['status']
            if status not in ('executed', 'unavailable', 'excluded', 'not_applicable') or check['result'] not in ('passed', 'failed', 'warnings', 'not_run'):
                raise Invalid('Invalid check status/result')
            if not isinstance(check['evidence'], list) or len(check['evidence']) > 40 or not isinstance(check['reason'], str):
                raise Invalid('Invalid reason/evidence')
            expected = 'excluded' if not spec['enabled'] else 'not_applicable' if not spec['applicable'] else None
            if expected and status != expected or not expected and status in ('excluded', 'not_applicable'):
                raise Invalid('Reader changed applicability/enabled policy: ' + spec['id'])
            if status != 'executed':
                text(check['reason'], 'skip reason')
                if check['result'] != 'not_run' or check['evidence']:
                    raise Invalid('Unrun check claims a result or execution evidence')
                if status == 'unavailable':
                    destination = problems if spec['required'] else warnings
                    destination.append(spec['id'] + ': ' + check['reason'])
                continue
            if check['result'] == 'not_run' or not check['evidence']:
                raise Invalid('Executed check lacks result/evidence')
            for evidence in check['evidence']:
                obj(evidence, ('method', 'tool', 'locator', 'observation', 'exit_code'), 'evidence')
                if evidence['method'] != spec['method']:
                    raise Invalid('Evidence method differs from declared check: ' + spec['id'])
                for field in ('tool', 'locator', 'observation'):
                    text(evidence[field], field)
                if spec['method'] == 'command':
                    if type(evidence['exit_code']) is not int:
                        raise Invalid('Command evidence lacks exit code')
                    if check['result'] == 'passed' and evidence['exit_code'] != 0:
                        raise Invalid('Passing command has nonzero exit code')
                elif evidence['exit_code'] is not None:
                    raise Invalid('Non-command evidence claims exit code')
            if check['result'] == 'failed':
                text(check['reason'], 'failure reason')
                defects.append(spec['id'] + ': ' + check['reason'])
            elif check['result'] == 'warnings':
                text(check['reason'], 'warning reason')
                warnings.append(spec['id'] + ': ' + check['reason'])
    except (Invalid, KeyError, TypeError) as error:
        problems.append(str(error))
    if problems:
        result = gate('blocked', problems + defects + warnings)
    elif defects:
        result = gate('failed', defects + warnings, blocking=True)
    elif warnings:
        stop = config['optional_policy'] == 'stop'
        result = gate('warnings', warnings, blocking=stop, owner=stop)
    else:
        result = gate('passed', [])
    return result


def worker(operation):
    envelope = json.load(sys.stdin)
    context = json.loads(Path(os.environ['PRIFLY_CONTEXT_FILE']).read_text())
    result = {'schema_version': '1', **{k: envelope[k] for k in ('run_id', 'step_instance_id', 'attempt_id')},
              'envelope_digest': os.environ['PRIFLY_ENVELOPE_DIGEST'], 'verdict': 'pass',
              'outputs': {}, 'evidence_refs': [], 'effect_receipt_refs': [], 'summary': ''}
    def read(port):
        return json.loads(Path(context['inputs'][port]['path']).read_text())
    def output(port, value):
        slot = context['outputs'][port]
        data = encoded(value) + b'\n'
        Path(slot['path']).write_bytes(data)
        result['outputs'][port] = {k: slot[k] for k in ('artifact_id', 'revision')}
        result['outputs'][port]['digest'] = digest(data)
    try:
        config = read('request')
        request(config)
        if operation == 'configure':
            output('request', config)
        elif operation == 'capture':
            output('candidate', snapshot(os.environ['PRIFLY_REPOSITORY_WORKSPACE'], config['base_commit']))
        elif operation == 'evaluate':
            try:
                current = snapshot(os.environ['PRIFLY_REPOSITORY_WORKSPACE'], config['base_commit'])
                assessment = evaluate(config, read('candidate'), read('report'), current,
                                      digest(Path(context['inputs']['request']['path']).read_bytes()))
            except (Invalid, OSError, subprocess.SubprocessError) as error:
                assessment = gate('blocked', ['Candidate cannot be assessed: ' + str(error)])
            output('gate', assessment)
        else:
            raise Invalid('Unknown worker operation')
        result['summary'] = 'Review evidence ' + operation
    except (Invalid, OSError, KeyError, subprocess.SubprocessError, ValueError) as error:
        result.update(verdict='fail', outputs={}, summary=str(error))
    os.write(3, encoded(result) + b'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='operation', required=True)
    snap = subs.add_parser('snapshot')
    snap.add_argument('--repository', type=Path, required=True)
    snap.add_argument('--base', required=True)
    for op in ('configure', 'capture', 'evaluate'):
        subs.add_parser(op)
    args = parser.parse_args()
    if args.operation == 'snapshot':
        print(json.dumps(snapshot(args.repository, args.base), sort_keys=True))
    else:
        worker(args.operation)


if __name__ == '__main__':
    main()
