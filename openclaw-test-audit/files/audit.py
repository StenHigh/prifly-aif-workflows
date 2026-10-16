"""Select changed tests and validate a read-only audit; Python stdlib only."""
import argparse
import fnmatch
import json
import os
from pathlib import Path
import subprocess
import sys

from candidate import COMMIT, Invalid, digest, encoded, git, snapshot


def exact(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise Invalid(label + ': missing or unknown fields')


def text(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 4000:
        raise Invalid(label + ': expected nonempty text (at most 4000 characters)')


def config(value):
    exact(value, ('base_commit', 'round', 'test_patterns', 'require_separate_session'), 'config')
    if not isinstance(value['base_commit'], str) or not COMMIT.fullmatch(value['base_commit']):
        raise Invalid('Expected original full SHA-1 base commit')
    if type(value['round']) is not int or not 1 <= value['round'] <= 10000:
        raise Invalid('Expected round in 1..10000')
    if type(value['require_separate_session']) is not bool:
        raise Invalid('Expected explicit session policy')
    patterns = value['test_patterns']
    if not isinstance(patterns, list) or not 1 <= len(patterns) <= 80:
        raise Invalid('Expected 1..80 project test patterns')
    for pattern in patterns:
        text(pattern, 'test pattern')
        if pattern.startswith('/') or '..' in pattern.split('/') or '\\' in pattern:
            raise Invalid('Expected repository-relative slash-separated test patterns')


def changed_tests(tree, settings):
    """Union committed/worktree, index and nonignored new paths, no rename folding.

    fnmatchcase semantics: * includes slashes; tests/* covers all of tests/.
    Including the index prevents an unstaged reversal hiding a staged test edit.
    """
    base = settings['base_commit']
    commands = (
        ('diff', '--no-ext-diff', '--no-textconv', '--no-renames', '--name-only', '-z', base, '--'),
        ('diff', '--cached', '--no-ext-diff', '--no-textconv', '--no-renames', '--name-only', '-z', base, '--'),
        ('ls-files', '--others', '--exclude-standard', '-z'),
    )
    paths = {path for command in commands for path in git(tree, *command).split(b'\0') if path}
    if len(paths) > 10000:
        raise Invalid('Change set exceeds 10000 paths')
    selected = []
    for path in sorted(paths):
        try:
            name = path.decode('utf-8', errors='strict')
        except UnicodeError as error:
            raise Invalid('Change set contains a non-UTF-8 path') from error
        if any(fnmatch.fnmatchcase(name, pattern) for pattern in settings['test_patterns']):
            selected.append(name)
    if len(selected) > 200:
        raise Invalid('Audit exceeds 200 changed test paths; split the task')
    return selected


def prepare(tree, settings):
    config(settings)
    before = snapshot(tree, settings['base_commit'])
    paths = changed_tests(tree, settings)
    if snapshot(tree, settings['base_commit']) != before:
        raise Invalid('Candidate changed while selecting tests')
    return {'config': settings, 'candidate': before, 'paths': paths}


def gate(status, findings):
    return {'gate': 'test-audit', 'status': status, 'blocking': status in ('failed', 'blocked'),
            'findings': findings}


def skipped(request):
    report = {'request_digest': digest(encoded(request) + b'\n'), 'candidate': request['candidate'],
              'round': request['config']['round'], 'session': 'not_run', 'model': None,
              'files': [], 'skip_reason': 'No changed paths match the declared project test patterns.'}
    return report


def evaluate(tree, request, report, request_digest):
    """Verify freshness and complete path coverage; semantic judgements are reader claims."""
    try:
        exact(request, ('config', 'candidate', 'paths'), 'audit request')
        current = prepare(tree, request['config'])
        if current != request:
            raise Invalid('Stale audit: candidate or selected test paths changed')
        if not request['paths']:
            raise Invalid('Reader report supplied for an empty audit')
        exact(report, ('request_digest', 'candidate', 'round', 'session', 'model', 'files', 'skip_reason'), 'report')
        if report['request_digest'] != request_digest or report['candidate'] != request['candidate']:
            raise Invalid('Report is for another request or candidate')
        if type(report['round']) is not int or report['round'] != request['config']['round']:
            raise Invalid('Report is for another round')
        if report['skip_reason'] != '' or report['session'] not in ('separate', 'shared', 'unavailable'):
            raise Invalid('Reader cannot skip a nonempty audit or invent session availability')
        if report['model'] is not None:
            text(report['model'], 'actual model')
        if request['config']['require_separate_session'] and report['session'] != 'separate':
            raise Invalid('Required separate audit session unavailable')
        if not isinstance(report['files'], list) or len(report['files']) != len(request['paths']):
            raise Invalid('Missing or extra audited test paths')
        seen, defects, unavailable = set(), [], []
        for item in report['files']:
            exact(item, ('path', 'status', 'behavior', 'regression', 'existing_proof', 'evidence', 'findings'), 'file audit')
            path = item['path']
            if not isinstance(path, str) or path not in request['paths'] or path in seen:
                raise Invalid('Unknown or duplicate audited test path')
            seen.add(path)
            if item['status'] not in ('passed', 'failed', 'unavailable'):
                raise Invalid('Invalid file audit status')
            for field in ('behavior', 'regression', 'existing_proof'):
                text(item[field], field)
            evidence, findings = item['evidence'], item['findings']
            if not isinstance(evidence, list) or not 1 <= len(evidence) <= 40:
                raise Invalid('File audit needs concrete inspection evidence')
            for entry in evidence:
                exact(entry, ('locator', 'observation'), 'audit evidence')
                text(entry['locator'], 'evidence locator')
                text(entry['observation'], 'evidence observation')
            if not isinstance(findings, list) or len(findings) > 40:
                raise Invalid('Invalid audit findings')
            for finding in findings:
                text(finding, 'finding')
            if item['status'] == 'passed' and findings or item['status'] != 'passed' and not findings:
                raise Invalid('Audit status contradicts findings')
            if item['status'] == 'failed':
                defects.extend(path + ': ' + finding for finding in findings)
            if item['status'] == 'unavailable':
                unavailable.extend(path + ': ' + finding for finding in findings)
        if unavailable:
            return gate('blocked', unavailable + defects)
        return gate('failed' if defects else 'passed', defects)
    except (Invalid, KeyError, TypeError, ValueError, OSError, subprocess.SubprocessError) as error:
        return gate('blocked', [str(error)])


def worker(operation):
    envelope = json.load(sys.stdin)
    context = json.loads(Path(os.environ['PRIFLY_CONTEXT_FILE']).read_text())
    result = {'schema_version': '1', **{key: envelope[key] for key in ('run_id', 'step_instance_id', 'attempt_id')},
              'envelope_digest': os.environ['PRIFLY_ENVELOPE_DIGEST'], 'verdict': 'pass',
              'outputs': {}, 'evidence_refs': [], 'effect_receipt_refs': [], 'summary': ''}

    def read(port):
        return json.loads(Path(context['inputs'][port]['path']).read_bytes())

    def output(port, value):
        slot = context['outputs'][port]
        raw = encoded(value) + b'\n'
        Path(slot['path']).write_bytes(raw)
        result['outputs'][port] = {key: slot[key] for key in ('artifact_id', 'revision')}
        result['outputs'][port]['digest'] = digest(raw)

    try:
        if operation == 'configure':
            settings = read('config')
            config(settings)
            output('config', settings)
        elif operation == 'prepare':
            request = prepare(os.environ['PRIFLY_REPOSITORY_WORKSPACE'], read('config'))
            if request['paths']:
                output('request', request)
            else:
                # Last freshness check before issuing a skip, with no AI session.
                if prepare(os.environ['PRIFLY_REPOSITORY_WORKSPACE'], request['config']) != request:
                    raise Invalid('Candidate changed before skip')
                result['verdict'] = 'no_work'
                report = skipped(request)
                output('report', report)
                output('gate', gate('skipped', [report['skip_reason']]))
        elif operation == 'evaluate':
            output('gate', evaluate(os.environ['PRIFLY_REPOSITORY_WORKSPACE'], read('request'), read('report'),
                                    digest(Path(context['inputs']['request']['path']).read_bytes())))
        else:
            raise Invalid('Unknown operation')
        result['summary'] = 'Test audit ' + operation
    except (Invalid, KeyError, ValueError, OSError, subprocess.SubprocessError) as error:
        result.update(verdict='fail', outputs={}, summary=str(error))
    os.write(3, encoded(result) + b'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('configure', 'prepare', 'evaluate'))
    worker(parser.parse_args().operation)
