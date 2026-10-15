"""Owned Git fixtures and explicit W1 handoff for the standalone W4 example."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys

import verify

EXAMPLE = verify.ROOT / 'examples/verified-integration'
sys.path.insert(0, str(EXAMPLE / 'files'))
import integration as i
import publication


def install(repository):
    shutil.copytree(EXAMPLE, repository / '.prifly/workflows/verified-integration')
    path = repository / '.prifly/project.yaml'
    value = path.read_text().replace('packages:\n', 'packages:\n  verified-integration:\n    source: .prifly/workflows/verified-integration\n', 1)
    value = value.replace('launches:\n', 'launches:\n  verified-integration:\n    title: Verified integration example\n    description: Assess the exact merged code before a separate explicit integration.\n    kind: workflow\n    workflow: .prifly/workflows/verified-integration/workflow.yaml\n', 1)
    path.write_text(value)


def report(config, basis, request_digest=None, failed=False):
    return {'round': config['round'], 'request_digest': request_digest or i.w1.digest(i.w1.encoded(config) + b'\n'),
            'candidate': basis, 'session': 'shared', 'model_profile': 'unavailable', 'model': None,
            'checks': [{'id': c['id'], 'status': 'executed', 'result': 'failed' if failed else 'passed',
                        'reason': 'Synthetic final-reader defect' if failed else '',
                        'evidence': [{'method': c['method'], 'tool': 'synthetic-fixture', 'locator': 'consumer.py',
                                      'observation': 'Synthetic reader report; no real model qualification.', 'exit_code': None}]} for c in config['checks']]}


def fixture(root, repository=None, case='ready'):
    repository = repository or root / 'candidate'
    if not repository.exists():
        repository.mkdir()
        verify.git('-C', repository, 'init', '-q', '-b', 'main')
    (repository / '.gitignore').write_text('__pycache__/\n')
    (repository / 'value.py').write_text('VALUE = 1\n')
    (repository / 'consumer.py').write_text('from value import VALUE\n\ndef effective():\n    return VALUE\n')
    (repository / 'owner.txt').write_text('Owner work remains intact\n')
    verify.git('-C', repository, 'add', '.')
    verify.git('-C', repository, 'commit', '-qm', 'Integration base')
    base = i.git(repository, 'rev-parse', 'HEAD')
    verify.git('-C', repository, 'checkout', '-qb', 'target')
    if case == 'semantic-regression':
        (repository / 'consumer.py').write_text('from value import VALUE\n\ndef effective():\n    return VALUE * 2\n')
    elif case == 'conflict':
        (repository / 'value.py').write_text('VALUE = 3\n')
    else:
        (repository / 'target-note.txt').write_text('Target work remains intact\n')
    verify.git('-C', repository, 'add', '.')
    verify.git('-C', repository, 'commit', '-qm', 'Target advance')
    target = i.git(repository, 'rev-parse', 'HEAD')
    verify.git('-C', repository, 'checkout', '-q', 'main')
    (repository / 'value.py').write_text('VALUE = 2\n')
    (repository / 'acceptance.py').write_text('from consumer import effective\nassert effective() == 2, effective()\nprint("accepted integrated behavior")\n')
    if case == 'risk':
        (repository / 'migrations').mkdir()
        (repository / 'migrations/001.sql').write_text('-- owner migration decision required\n')
    verify.git('-C', repository, 'add', '.')
    verify.git('-C', repository, 'commit', '-qm', 'Candidate feature')
    candidate = i.git(repository, 'rev-parse', 'HEAD')
    bare = root / 'local-origin.git'
    verify.git('init', '--bare', '-q', bare)
    i.git(bare, 'fetch', '--no-tags', str(repository), target)
    i.git(bare, 'update-ref', 'refs/heads/main', target)
    if case == 'unrelated-target':
        other = root / 'unrelated'
        other.mkdir()
        verify.git('-C', other, 'init', '-q', '-b', 'main')
        (other / 'unrelated.txt').write_text('Separate project history\n')
        verify.git('-C', other, 'add', '.')
        verify.git('-C', other, 'commit', '-qm', 'Unrelated target')
        target = i.git(other, 'rev-parse', 'HEAD')
        i.git(bare, 'fetch', '--no-tags', str(other), target)
        i.git(bare, 'update-ref', 'refs/heads/main', target)
    config = {'base_commit': base, 'round': 1, 'checks': [{'id': 'source-command', 'description': 'Run acceptance.py on the committed feature.',
               'method': 'command', 'required': True, 'enabled': True, 'applicable': True}],
              'optional_policy': 'ignore', 'require_separate_session': False}
    before = i.w1.snapshot(repository, base)
    run = subprocess.run([sys.executable, '-B', 'acceptance.py'], cwd=repository, capture_output=True, check=True)
    source_report = {'round': 1, 'request_digest': i.w1.digest(i.w1.encoded(config) + b'\n'), 'candidate': before,
                     'session': 'shared', 'model_profile': 'unavailable', 'model': None,
                     'checks': [{'id': 'source-command', 'status': 'executed', 'result': 'passed', 'reason': '',
                                 'evidence': [{'method': 'command', 'tool': 'Python', 'locator': sys.executable + ' -B acceptance.py',
                                               'observation': run.stdout.decode().strip(), 'exit_code': run.returncode}]}]}
    handoff = json.loads((EXAMPLE / 'configuration.example.json').read_text())
    handoff.update(candidate_commit=candidate, target={'repository': str(bare), 'ref': 'refs/heads/main', 'commit': target},
                   acceptance=[{'role': 'source-command', 'request_text': (i.w1.encoded(config) + b'\n').decode(), 'report': source_report}])
    handoff['integrated_checks'][0]['argv'] = [sys.executable, '-B', 'acceptance.py']
    handoff['spot_checks'][0]['description'] = 'Inspect the merged consumer and value: effective() must return 2, preserving existing target work.'
    return repository, handoff, before


def accepted(source, handoff):
    assessment, request, basis = i.prepare(source, handoff, 'owned-unit-fixture')
    assert assessment['status'] == 'ready', assessment['findings']
    return i.evaluate(source, handoff, assessment, request, report(request, basis), i.w1.digest(i.w1.encoded(request) + b'\n'))


class FakeGitLab:
    """Offline provider: models glab --draft prefix and conditional owned writes."""
    def __init__(self, target, lose_ack=False, duplicate=False):
        self.target, self.branch, self.mrs = target, None, []
        self.lose_ack, self.duplicate, self.create_calls = lose_ack, duplicate, 0

    def inspect(self, spec):
        return copy.deepcopy({'target_commit': self.target, 'source_branch': self.branch, 'mrs': self.mrs})

    def ensure_source_branch(self, spec, old):
        if self.branch is not None and (self.branch['identity'] != spec['identity'] or self.branch['commit'] != old):
            raise ValueError('Source branch CAS refused')
        self.branch = {'identity': spec['identity'], 'commit': spec['candidate_commit']}

    def create(self, spec, title, draft):
        self.create_calls += 1
        # glab 1.119.0 always adds Draft when --draft is supplied.
        value = ('Draft: ' if draft else '') + ('Draft: ' if self.duplicate else '') + title
        mr = {**{k: spec[k] for k in ('identity', 'candidate_commit', 'target_commit', 'source_branch', 'target_branch')},
              'title': value, 'body': spec['body'], 'revision': 1, 'url': 'https://gitlab.example.invalid/project/-/merge_requests/1'}
        self.mrs.append(mr)
        if self.lose_ack:
            raise TimeoutError('Acknowledgement lost after MR creation')
        return copy.deepcopy(mr)

    def update_title(self, url, title, expected_revision):
        mr = self.mrs[0]
        if mr['url'] != url or mr['revision'] != expected_revision:
            raise ValueError('MR revision CAS refused')
        mr['title'] = title
        mr['revision'] += 1


def publication_spec(handoff, assessment):
    return {**handoff['publication'], 'candidate_commit': handoff['candidate_commit'],
            'target_commit': handoff['target']['commit'], 'handoff_digest': assessment['handoff_digest']}
