"""Project integration example: pinned Git merge, acceptance and explicit writes."""
import argparse
import copy
import fnmatch
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import evidence as w1

CATEGORIES = ('auth_money', 'migrations', 'dependencies', 'deploy', 'business_assumptions')
STATUSES = ('ready', 'needs_revision', 'owner_required', 'unavailable', 'reconcile_required')
# A program's TMPDIR belongs to that Attempt. The integration session has to
# outlive prepare and remain accessible to evaluate/release and the operator.
# This POSIX example uses the shared OS temp root, never an Attempt scratch dir.
SESSION_ROOT = Path('/tmp')


def command(tree, *args, input=None, env=None):
    environment = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GIT_NO_LAZY_FETCH': '1',
                   **(env or {})}
    return subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false',
                           '-c', 'commit.gpgsign=false', '-c', 'protocol.file.allow=always',
                           '-C', str(tree), *args], input=input, capture_output=True,
                          timeout=60, env=environment)


def git(tree, *args, **kwargs):
    result = command(tree, *args, **kwargs)
    if result.returncode:
        raise w1.Invalid('Git operation failed: ' + args[0] + ': ' + result.stderr.decode(errors='replace')[:1000])
    return result.stdout.decode().strip()


def validate(handoff):
    w1.obj(handoff, ('owner', 'candidate_commit', 'target', 'mode', 'acceptance',
                    'integrated_checks', 'spot_checks', 'policy', 'risk_approval',
                    'require_separate_session', 'optional_policy', 'publication'), 'handoff')
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,79}', handoff['owner']):
        raise w1.Invalid('Invalid project owner identity')
    if not w1.COMMIT.fullmatch(handoff['candidate_commit']):
        raise w1.Invalid('Candidate must be a full commit')
    target = handoff['target']
    w1.obj(target, ('repository', 'ref', 'commit'), 'target')
    if not Path(target['repository']).is_absolute() or not w1.COMMIT.fullmatch(target['commit']):
        raise w1.Invalid('Expected absolute local bare target and exact commit')
    if not target['ref'].startswith('refs/heads/') or command(Path.cwd(), 'check-ref-format', target['ref']).returncode:
        raise w1.Invalid('Expected a valid target branch ref')
    if handoff['mode'] not in ('assess', 'local_merge', 'gitlab_draft'):
        raise w1.Invalid('Unknown explicit integration mode')
    if type(handoff['require_separate_session']) is not bool or handoff['optional_policy'] not in ('ignore', 'stop'):
        raise w1.Invalid('Invalid final reader policy')
    if not isinstance(handoff['acceptance'], list) or not 1 <= len(handoff['acceptance']) <= 10:
        raise w1.Invalid('Supply explicit W1 acceptance artifacts')
    roles, has_required_source_check = set(), False
    for entry in handoff['acceptance']:
        w1.obj(entry, ('role', 'request_text', 'report'), 'source acceptance')
        w1.text(entry['role'], 'acceptance role')
        if entry['role'] in roles:
            raise w1.Invalid('Duplicate acceptance role')
        roles.add(entry['role'])
        config = json.loads(entry['request_text'])
        w1.request(config)
        has_required_source_check |= any(c['required'] and c['enabled'] and c['applicable'] for c in config['checks'])
    if not has_required_source_check:
        raise w1.Invalid('Source acceptance needs at least one enabled applicable required check')
    checks = handoff['integrated_checks']
    if not isinstance(checks, list) or not 1 <= len(checks) <= 20:
        raise w1.Invalid('At least one actual integrated command is required')
    ids = set()
    for check in checks:
        w1.obj(check, ('id', 'description', 'argv', 'timeout_seconds'), 'integrated check')
        w1.text(check['description'], 'check description')
        if not re.fullmatch(r'[a-z][a-z0-9_-]{0,79}', check['id']) or check['id'] in ids:
            raise w1.Invalid('Duplicate/invalid integrated command ID')
        ids.add(check['id'])
        if not isinstance(check['argv'], list) or not 1 <= len(check['argv']) <= 40:
            raise w1.Invalid('Expected reviewed command argv, not shell text')
        for argument in check['argv']:
            if not isinstance(argument, str) or not argument or len(argument) > 4000 or '\0' in argument:
                raise w1.Invalid('Invalid command argument')
        if type(check['timeout_seconds']) is not int or not 1 <= check['timeout_seconds'] <= 120:
            raise w1.Invalid('Command timeout must be 1..120 seconds')
    final_request = {'base_commit': target['commit'], 'round': 1, 'checks': handoff['spot_checks'],
                     'require_separate_session': handoff['require_separate_session'],
                     'optional_policy': handoff['optional_policy']}
    w1.request(final_request)
    if not any(c['required'] and c['enabled'] and c['applicable'] for c in final_request['checks']):
        raise w1.Invalid('At least one required final spot check is required')
    if any(c['method'] != 'code' for c in final_request['checks']):
        raise w1.Invalid('This example uses code spot checks; browser acceptance remains a separate project contract')
    policy = handoff['policy']
    w1.obj(policy, ('escalation_paths', 'declared_risks'), 'project policy')
    w1.obj(policy['escalation_paths'], CATEGORIES, 'escalation categories')
    for paths in policy['escalation_paths'].values():
        if not isinstance(paths, list) or any(not isinstance(p, str) or not p or p.startswith('/') or '..' in p.split('/') for p in paths):
            raise w1.Invalid('Invalid project escalation paths')
    for risk in policy['declared_risks']:
        w1.obj(risk, ('category', 'reason'), 'declared risk')
        if risk['category'] not in CATEGORIES:
            raise w1.Invalid('Unknown escalation category')
        w1.text(risk['reason'], 'risk reason')
    approval = handoff['risk_approval']
    if approval is not None:
        w1.obj(approval, ('candidate_commit', 'target_commit', 'policy_digest', 'categories', 'reference', 'reason'), 'owner risk approval')
        w1.text(approval['reference'], 'owner decision reference')
        w1.text(approval['reason'], 'owner decision reason')
        if any(c not in CATEGORIES for c in approval['categories']):
            raise w1.Invalid('Unknown approved category')
    publication = handoff['publication']
    if handoff['mode'] == 'gitlab_draft':
        if publication is None:
            raise w1.Invalid('External mode requires an explicit project publication contract')
        w1.obj(publication, ('project', 'source_branch', 'target_branch', 'title', 'body', 'identity'), 'publication')
        for key, value in publication.items():
            w1.text(value, 'publication.' + key)
    elif publication is not None:
        raise w1.Invalid('Publication contract belongs only to gitlab_draft mode')
    return final_request


def target_head(handoff):
    target = handoff['target']
    repository = Path(target['repository']).resolve(strict=True)
    if git(repository, 'rev-parse', '--is-bare-repository') != 'true':
        raise w1.Invalid('Target must be a local bare Git repository; working checkouts are not mutated')
    return git(repository, 'rev-parse', '--verify', target['ref'] + '^{commit}')


def source_basis(source, handoff):
    bases = {json.loads(a['request_text'])['base_commit'] for a in handoff['acceptance']}
    if len(bases) != 1:
        raise w1.Invalid('Source acceptance reports have different original bases')
    basis = w1.snapshot(source, bases.pop())
    if basis['head_commit'] != handoff['candidate_commit']:
        raise w1.Invalid('Candidate commit moved')
    if git(source, 'status', '--porcelain', '--untracked-files=all'):
        raise w1.Invalid('Commit and review the actual dirty/staged/untracked work before integration')
    return basis


def fresh(source, handoff, assessment):
    if assessment['handoff_digest'] != w1.digest(w1.encoded(handoff)):
        raise w1.Invalid('Acceptance criteria, mode or project policy changed after assessment')
    if source_basis(source, handoff) != assessment['source_candidate']:
        raise w1.Invalid('Source acceptance is stale')
    if target_head(handoff) != handoff['target']['commit']:
        raise w1.Invalid('Target moved after acceptance')
    session = owned(assessment)
    current = w1.snapshot(session / 'tree', handoff['target']['commit'])
    if current != assessment['integration_candidate']:
        raise w1.Invalid('Integration tree moved after its checks')
    return current


def owned(assessment):
    info = assessment['session']
    if info is None:
        raise w1.Invalid('No owned integration session')
    path = Path(info['path'])
    if path.is_symlink() or path.parent.resolve() != SESSION_ROOT.resolve() or not path.name.startswith('prifly-integration-'):
        raise w1.Invalid('Refuse cleanup/access outside the exact owned integration session')
    if json.loads((path / 'owner.json').read_text()) != info['marker']:
        raise w1.Invalid('Integration session ownership mismatch')
    return path


def risks(handoff, tree):
    changed = git(tree, 'diff', '--name-only', '-z', handoff['target']['commit'], 'HEAD').split('\0')
    found = []
    for category, patterns in handoff['policy']['escalation_paths'].items():
        matched = [p for p in changed if p and any(fnmatch.fnmatchcase(p, pattern) for pattern in patterns)]
        if matched:
            found.append({'category': category, 'reason': 'Project escalation paths changed', 'paths': matched})
    found.extend({**risk, 'paths': []} for risk in handoff['policy']['declared_risks'])
    required = {r['category'] for r in found}
    approval = handoff['risk_approval']
    approved = approval is not None and approval['candidate_commit'] == handoff['candidate_commit'] and approval['target_commit'] == handoff['target']['commit'] and approval['policy_digest'] == w1.digest(w1.encoded(handoff['policy'])) and required <= set(approval['categories'])
    return found, bool(required and not approved)


def diagnostic(assessment, status, reason):
    assessment['status'] = status
    assessment['findings'].append(reason)
    return assessment


def prepare(source, handoff, identity):
    request = validate(handoff)
    assessment = {'status': 'ready', 'handoff_digest': w1.digest(w1.encoded(handoff)),
                  'owner': handoff['owner'], 'source_candidate': None,
                  'target_commit': handoff['target']['commit'], 'integration_candidate': None,
                  'integration_head': None, 'session': None, 'source_gates': [], 'checks': [],
                  'risks': [], 'findings': [], 'final_report': None, 'final_gate': None,
                  'operation': None, 'cleanup': 'not_needed'}
    try:
        before = source_basis(source, handoff)
        assessment['source_candidate'] = before
        if target_head(handoff) != handoff['target']['commit']:
            raise w1.Invalid('Target differs from the declared commit')
        for entry in handoff['acceptance']:
            config = json.loads(entry['request_text'])
            gate = w1.evaluate(config, before, entry['report'], before,
                               w1.digest(entry['request_text'].encode()))
            assessment['source_gates'].append({'role': entry['role'], 'gate': gate,
                                               'report_digest': w1.digest(w1.encoded(entry['report']))})
            if gate['status'] == 'blocked' or gate['blocking']:
                return diagnostic(assessment, 'owner_required' if gate['blocking_owner_only'] else 'needs_revision' if gate['status'] == 'failed' else 'unavailable',
                                  'Source acceptance is not ready: ' + entry['role']), request, None
        # The same accepted handoff owns one durable session. A retained unknown
        # write must block a fresh prepare/continue, even if the provider lookup
        # is temporarily inconclusive. There is no lease expiry or blind retry.
        session = SESSION_ROOT / ('prifly-integration-' + assessment['handoff_digest'][7:])
        try:
            session.mkdir(mode=0o700)
        except FileExistsError:
            if session.is_symlink():
                raise w1.Invalid('Existing integration session is not an owned directory')
            previous = json.loads((session / 'owner.json').read_text())
            w1.obj(previous, ('owner', 'handoff_digest', 'attempt'), 'existing session owner')
            if previous['owner'] != handoff['owner'] or previous['handoff_digest'] != assessment['handoff_digest']:
                raise w1.Invalid('Existing integration session ownership differs; no write/cleanup')
            assessment['session'] = {'path': str(session), 'marker': previous}
            assessment['cleanup'] = 'reconcile_required'
            return diagnostic(assessment, 'reconcile_required', 'Previous owned integration session remains; inspect/reconcile/release it before re-entry'), request, None
        marker = {'owner': handoff['owner'], 'handoff_digest': assessment['handoff_digest'], 'attempt': identity}
        (session / 'owner.json').write_bytes(w1.encoded(marker))
        assessment['session'] = {'path': str(session), 'marker': marker}
        assessment['cleanup'] = 'required'
        print(json.dumps({'owned_integration_session': str(session), 'marker': marker}), flush=True)
        git(session, 'clone', '--no-local', '--no-hardlinks', '--no-checkout', str(source), 'tree')
        tree = session / 'tree'
        git(tree, 'fetch', '--no-tags', handoff['target']['repository'], handoff['target']['commit'])
        merged = command(tree, 'merge-tree', '--write-tree', handoff['target']['commit'], handoff['candidate_commit'])
        if merged.returncode == 1:
            return diagnostic(assessment, 'needs_revision', 'Merge conflict: ' + merged.stdout.decode(errors='replace')[:3000]), request, None
        if merged.returncode:
            return diagnostic(assessment, 'unavailable', 'Merge assessment could not run: ' + merged.stderr.decode(errors='replace')[:3000]), request, None
        tree_oid = merged.stdout.decode().splitlines()[0]
        if not w1.COMMIT.fullmatch(tree_oid):
            raise w1.Invalid('Merge did not return one exact tree')
        stamp = max(int(git(tree, 'show', '-s', '--format=%ct', commit)) for commit in (handoff['target']['commit'], handoff['candidate_commit'])) + 1
        environment = {'GIT_AUTHOR_NAME': 'Pri-Fly integration example', 'GIT_AUTHOR_EMAIL': 'integration@example.invalid',
                       'GIT_COMMITTER_NAME': 'Pri-Fly integration example', 'GIT_COMMITTER_EMAIL': 'integration@example.invalid',
                       'GIT_AUTHOR_DATE': f'@{stamp} +0000', 'GIT_COMMITTER_DATE': f'@{stamp} +0000'}
        head = git(tree, 'commit-tree', tree_oid, '-p', handoff['target']['commit'], '-p', handoff['candidate_commit'],
                   input=b'Verified local integration example\n', env=environment)
        git(tree, 'checkout', '--detach', head)
        basis = w1.snapshot(tree, handoff['target']['commit'])
        assessment.update(integration_head=head, integration_candidate=basis)
        failed, unavailable = False, False
        for check in handoff['integrated_checks']:
            item = {'id': check['id'], 'argv': check['argv'], 'exit_code': None,
                    'stdout': '', 'stderr': '', 'stdout_digest': None, 'stderr_digest': None,
                    'truncated': False, 'result': 'unavailable', 'reason': ''}
            try:
                run = subprocess.run(check['argv'], cwd=tree, capture_output=True, timeout=check['timeout_seconds'],
                                     env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
                item.update(exit_code=run.returncode, stdout=run.stdout.decode(errors='replace')[:4000],
                            stderr=run.stderr.decode(errors='replace')[:4000],
                            stdout_digest=w1.digest(run.stdout), stderr_digest=w1.digest(run.stderr),
                            truncated=len(run.stdout.decode(errors='replace')) > 4000 or len(run.stderr.decode(errors='replace')) > 4000,
                            result='passed' if run.returncode == 0 else 'unavailable' if run.returncode == 77 else 'failed',
                            reason='' if run.returncode == 0 else 'Declared command exited ' + str(run.returncode))
            except (OSError, subprocess.TimeoutExpired) as error:
                item['reason'] = str(error)[:4000]
            failed |= item['result'] == 'failed'
            unavailable |= item['result'] == 'unavailable'
            assessment['checks'].append(item)
        fresh(source, handoff, assessment)
        found, needs_owner = risks(handoff, tree)
        assessment['risks'] = found
        if unavailable:
            diagnostic(assessment, 'unavailable', 'An integrated command could not judge the result')
        elif needs_owner:
            diagnostic(assessment, 'owner_required', 'Project risk decision required for: ' + ', '.join(sorted({r['category'] for r in found})))
        elif failed:
            diagnostic(assessment, 'needs_revision', 'Integrated behavior failed despite a successful Git merge')
        return assessment, request, basis
    except (w1.Invalid, OSError, subprocess.SubprocessError, ValueError) as error:
        return diagnostic(assessment, 'unavailable', str(error)[:4000]), request, assessment['integration_candidate']


def evaluate(source, handoff, assessment, request, report, request_digest):
    assessment = copy.deepcopy(assessment)
    assessment['final_report'] = report
    try:
        if assessment['handoff_digest'] != w1.digest(w1.encoded(handoff)) or assessment['status'] != 'ready' or request != validate(handoff):
            raise w1.Invalid('Final reader is bound to a different or unready assessment')
        current = fresh(source, handoff, assessment)
        gate = w1.evaluate(request, assessment['integration_candidate'], report, current, request_digest)
        assessment['final_gate'] = gate
        if gate['status'] == 'blocked':
            diagnostic(assessment, 'unavailable', '; '.join(gate['findings'])[:4000])
        elif gate['blocking_owner_only']:
            diagnostic(assessment, 'owner_required', '; '.join(gate['findings'])[:4000])
        elif gate['blocking']:
            diagnostic(assessment, 'needs_revision', '; '.join(gate['findings'])[:4000])
    except (w1.Invalid, OSError, subprocess.SubprocessError) as error:
        diagnostic(assessment, 'unavailable', str(error)[:4000])
    return assessment


def local_merge(source, handoff, assessment):
    assessment = copy.deepcopy(assessment)
    if handoff['mode'] != 'local_merge' or assessment['status'] != 'ready' or assessment['final_gate'] is None:
        return diagnostic(assessment, 'owner_required', 'Local merge requires the explicitly reviewed mode and final acceptance')
    try:
        fresh(source, handoff, assessment)
        session = owned(assessment)
        target = handoff['target']
        operation = {'kind': 'local_merge', 'status': 'intent', 'target_repository': target['repository'],
                     'target_ref': target['ref'], 'before': target['commit'], 'after': assessment['integration_head'],
                     'handoff_digest': assessment['handoff_digest'], 'reason': ''}
        journal = session / 'operation.json'
        journal.write_bytes(w1.encoded(operation))
        assessment['operation'] = operation
        # Only add the inspected immutable object. The live branch is changed by CAS.
        git(Path(target['repository']), 'fetch', '--no-tags', str(session / 'tree'), assessment['integration_head'])
        fresh(source, handoff, assessment)
        result = command(Path(target['repository']), 'update-ref', target['ref'],
                         assessment['integration_head'], target['commit'])
        if result.returncode:
            operation.update(status='not_applied', reason='Target compare-and-swap refused; inspect target before a new assessment')
            diagnostic(assessment, 'owner_required', operation['reason'])
        else:
            operation['status'] = 'applied'
        journal.write_bytes(w1.encoded(operation))
        if operation['status'] == 'applied' and target_head(handoff) != assessment['integration_head']:
            diagnostic(assessment, 'reconcile_required', 'Target moved after acknowledged local integration; inspect without another write')
    except (w1.Invalid, OSError, subprocess.SubprocessError) as error:
        # A lost acknowledgement may follow the write. Never infer not_applied.
        diagnostic(assessment, 'reconcile_required' if assessment['operation'] else 'unavailable', str(error)[:4000])
    return assessment


def reconcile(assessment):
    session = owned(assessment)
    operation = json.loads((session / 'operation.json').read_text())
    if operation['handoff_digest'] != assessment['handoff_digest'] or operation['kind'] != 'local_merge':
        raise w1.Invalid('Operation journal identity mismatch')
    actual = git(Path(operation['target_repository']), 'rev-parse', operation['target_ref'])
    status = operation['status'] if operation['status'] in ('applied', 'not_applied') else 'applied' if actual == operation['after'] else 'not_applied' if actual == operation['before'] else 'unknown'
    return {**operation, 'status': status,
            'observed_commit': actual}


def publication_result(source, handoff, assessment, receipt):
    assessment = copy.deepcopy(assessment)
    expected = {'handoff_digest': assessment['handoff_digest'], 'candidate_commit': handoff['candidate_commit'],
                'target_commit': handoff['target']['commit'], 'identity': handoff['publication']['identity']}
    assessment['operation'] = receipt
    try:
        fresh(source, handoff, assessment)
        if any(receipt.get(k) != v for k, v in expected.items()):
            raise w1.Invalid('Publication receipt identity mismatch; inspect external state')
        if receipt['status'] not in ('created', 'reused'):
            raise w1.Invalid('External publication requires reconciliation: ' + receipt['reason'])
        if not receipt['url'] or receipt['observed_target_commit'] != handoff['target']['commit']:
            raise w1.Invalid('Missing MR identity or external target moved')
    except (w1.Invalid, OSError, subprocess.SubprocessError, KeyError) as error:
        diagnostic(assessment, 'reconcile_required', str(error)[:4000])
    return assessment


def release(assessment):
    assessment = copy.deepcopy(assessment)
    if assessment['session'] is None:
        return assessment
    if assessment['status'] == 'reconcile_required':
        assessment['cleanup'] = 'reconcile_required'
        return assessment
    try:
        session = owned(assessment)
        if (session / 'operation.json').exists():
            operation = reconcile(assessment)
            if operation['status'] == 'unknown':
                raise w1.Invalid('Cannot release a session with an uncertain local write')
        shutil.rmtree(session)
        assessment['cleanup'] = 'released'
    except (w1.Invalid, OSError, subprocess.SubprocessError) as error:
        assessment['cleanup'] = 'reconcile_required'
        diagnostic(assessment, 'reconcile_required', str(error)[:4000])
    return assessment


def worker(operation):
    envelope = json.load(sys.stdin)
    context = json.loads(Path(os.environ['PRIFLY_CONTEXT_FILE']).read_text())
    result = {'schema_version': '1', **{k: envelope[k] for k in ('run_id', 'step_instance_id', 'attempt_id')},
              'envelope_digest': os.environ['PRIFLY_ENVELOPE_DIGEST'], 'verdict': 'pass',
              'outputs': {}, 'evidence_refs': [], 'effect_receipt_refs': [], 'summary': operation}
    def read(port):
        return json.loads(Path(context['inputs'][port]['path']).read_text())
    def output(port, value):
        slot = context['outputs'][port]
        data = w1.encoded(value) + b'\n'
        Path(slot['path']).write_bytes(data)
        result['outputs'][port] = {**{k: slot[k] for k in ('artifact_id', 'revision')}, 'digest': w1.digest(data)}
    source = Path(os.environ['PRIFLY_REPOSITORY_WORKSPACE'])
    try:
        if operation == 'configure':
            handoff = read('handoff')
            validate(handoff)
            output('handoff', handoff)
        elif operation == 'prepare':
            assessment, request, candidate = prepare(source, read('handoff'), envelope['attempt_id'])
            output('assessment', assessment)
            output('request', request)
            output('candidate', candidate)
        elif operation == 'evaluate':
            output('assessment', evaluate(source, read('handoff'), read('assessment'), read('request'), read('report'),
                                          w1.digest(Path(context['inputs']['request']['path']).read_bytes())))
        elif operation == 'local-merge':
            output('assessment', local_merge(source, read('handoff'), read('assessment')))
        elif operation == 'publication-result':
            output('assessment', publication_result(source, read('handoff'), read('assessment'), read('receipt')))
        elif operation in ('reader-unavailable', 'publication-unknown'):
            value = read('assessment')
            output('assessment', diagnostic(value, 'unavailable' if operation == 'reader-unavailable' else 'reconcile_required',
                                            'Final reader produced no usable report' if operation == 'reader-unavailable' else 'Publication host produced no receipt; inspect external identity before any retry'))
        elif operation == 'release':
            output('assessment', release(read('assessment')))
        elif operation == 'extension':
            validate(read('handoff'))
        else:
            raise w1.Invalid('Unknown operation')
    except (w1.Invalid, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        result.update(verdict='fail', outputs={}, summary=str(error)[:4000])
    os.write(3, w1.encoded(result) + b'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('configure', 'prepare', 'evaluate', 'local-merge', 'publication-result', 'release', 'extension', 'reconcile', 'reader-unavailable', 'publication-unknown'))
    parser.add_argument('--assessment', type=Path)
    args = parser.parse_args()
    if args.operation == 'reconcile':
        if args.assessment is None:
            parser.error('--assessment is required')
        print(json.dumps(reconcile(json.loads(args.assessment.read_text())), indent=2))
    else:
        worker(args.operation)


if __name__ == '__main__':
    main()
