"""Complete standalone/extension audit Runs; real Git/programs, synthetic reader."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify
from test_test_audit import a, report, settings
from evidence_check import read
from run_check import clean, git_out

CASES = ('pass', 'skip', 'untracked', 'failed', 'unavailable', 'missing', 'stale-request',
         'stale-production', 'needs-revision', 'reader-blocked', 'session-unavailable',
         'partial-resume', 'cancel-resume', 'extension-pass', 'extension-failed', 'extension-skip')


def submit(binary, authority, run_id, task, value, verdict):
    template = verify.run(binary, '--project', authority, 'session', 'submit', '--template',
                          '--run', run_id, '--attempt', task['attempt_id'])
    raw = json.dumps(value).encode()
    workspace = Path(task['workspace'])
    path = workspace / task['context']['outputs']['report']['path']
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    template['result']['outputs']['report']['digest'] = a.digest(raw)
    template['result']['verdict'] = verdict
    template['result']['summary'] = 'Synthetic test audit; no LLM judgement or model independence claimed.'
    template['model_profile'] = {'outcome': 'unavailable', 'reason': 'Synthetic host; no actual model.'}
    template['answered_questions'] = []
    submission = workspace / 'submission.json'
    submission.write_text(json.dumps(template))
    verify.run(binary, '--project', authority, 'session', 'submit', '--file', submission)


def run_case(binary, case, host='codex-cli'):
    with tempfile.TemporaryDirectory(prefix='test-audit-run-') as directory:
        root = Path(directory)
        repository, authority = verify.prepare_repository(binary, root)
        runs = []
        try:
            if case.startswith('extension-'):
                for name in ('workflow.yaml', 'extend.yaml'):
                    shutil.copyfile(verify.ROOT / 'examples/test-audit-extension' / name,
                                    repository / '.prifly/workflows/openclaw-test-audit' / name)
            (repository / 'tests').mkdir()
            (repository / 'tests/test_greeting.py').write_text('def test_greeting():\n    assert greet() == "Hello"\n')
            (repository / 'greeting.py').write_text('def greet():\n    return "Hello"\n')
            verify.git('-C', repository, 'add', '.')
            verify.git('-C', repository, 'commit', '-qm', 'Original fixture base')
            base = git_out(repository, 'rev-parse', 'HEAD')
            config = settings(base)
            if case == 'session-unavailable':
                config['require_separate_session'] = True
            if case in ('skip', 'extension-skip'):
                (repository / 'greeting.py').write_text('def greet():\n    return "Hello Ada"\n')
            else:
                with (repository / 'tests/test_greeting.py').open('a') as stream:
                    stream.write('def test_named_greeting():\n    assert greet("Ada") == "Hello Ada"\n')
            verify.git('-C', repository, 'add', '.')
            verify.git('-C', repository, 'commit', '-qm', 'Changed fixture candidate')
            before = a.snapshot(repository, base)
            request_path = root / 'config.json'
            request_path.write_text(json.dumps(config))
            verify.run(binary, '--project', authority, 'project', 'local', 'set', '--repository', repository,
                       '--allow-executable', 'python=' + str(Path(sys.executable).resolve()))
            args = ('--project', authority, 'project', 'start', '--repository', repository,
                    '--launch', 'openclaw-test-audit', '--host', host, '--workspace', 'worktree',
                    '--input', 'config=' + str(request_path), '--allow-execution')
            prepared = verify.run(binary, *args[:3], 'questionnaire', *args[4:], '--prepare')
            run_id = verify.run(binary, *args, '--expected-launch-digest', prepared['review_digest'])['run']['run']['id']
            runs.append(run_id)
            delivered, claims, tree = [], set(), None

            def drive(run_id, iteration):
                nonlocal tree
                for _ in range(10):
                    verify.run(binary, '--project', authority, 'run', 'drive', run_id)
                    tasks = verify.run(binary, '--project', authority, 'session', 'task', '--run', run_id, '--all')['tasks']
                    state = verify.run(binary, '--project', authority, 'run', 'status', run_id)['run']
                    if not tasks:
                        assert state['status'] in ('completed', 'failed', 'cancelled'), state['status']
                        return state
                    for task in tasks:
                        assert task['skill_refs'][0]['id'] == 'openclaw:context/audit-bridge'
                        assert set(task['context']['inputs']) == {'request'}
                        tree = Path(task['repository_workspace'])
                        claims.add(task['claim_id'])
                        request = read(task, 'request')
                        assert request['config']['base_commit'] == base
                        expected_paths = ['tests/new.py', 'tests/test_greeting.py'] if case == 'untracked' and iteration else ['tests/test_greeting.py']
                        assert request['paths'] == expected_paths, request['paths']
                        delivered.append(request['candidate']['digest'])
                        if case == 'cancel-resume' and iteration == 0:
                            verify.run(binary, '--project', authority, 'run', 'cancel', run_id, '--reason', 'Synthetic reviewer cancelled')
                            verify.run(binary, '--project', authority, 'run', 'drive', run_id)
                            return verify.run(binary, '--project', authority, 'run', 'status', run_id)['run']
                        status = 'unavailable' if case in ('unavailable', 'reader-blocked') or case == 'partial-resume' and iteration == 0 else 'failed' if case in ('failed', 'needs-revision', 'extension-failed') else 'passed'
                        value = report(request, status)
                        value['request_digest'] = task['context']['inputs']['request']['ref']['digest']
                        if case == 'missing': value['files'] = []
                        if case == 'stale-request': value['request_digest'] = 'sha256:' + '1' * 64
                        verdict = 'needs_revision' if case == 'needs-revision' else 'blocked' if case == 'reader-blocked' else 'pass'
                        submit(binary, authority, run_id, task, value, verdict)
                        if case == 'untracked' and iteration == 0:
                            # A new test after inspection invalidates the report;
                            # continuation must include it in a fresh selection.
                            (tree / 'tests/new.py').write_text('assert greet() == "Hello"\n')
                        if case == 'stale-production':
                            (tree / 'greeting.py').write_text('Intervening owner edit\n')
                raise AssertionError('Audit did not terminate')

            state = drive(run_id, 0)
            if case in ('partial-resume', 'cancel-resume', 'untracked'):
                assert state.get('outcome') == 'partial' or state['status'] == 'cancelled', state['status']
                (tree / 'greeting.py').write_text('Preserved owner change before continuation\n')
                args = ('--project', authority, 'project', 'continue', '--repository', repository,
                        '--launch', 'openclaw-test-audit', '--source-run', run_id, '--host', host, '--allow-execution')
                prepared = verify.run(binary, *args, '--prepare')
                run_id = verify.run(binary, *args, '--expected-launch-digest', prepared['review_digest'])['run']['run']['id']
                runs.append(run_id)
                state = drive(run_id, 1)
                assert len(delivered) == 2 and delivered[0] != delivered[1], delivered
                assert len(claims) == 1
                assert (tree / 'greeting.py').read_text() == 'Preserved owner change before continuation\n'
            values = {}
            for name in ('gate', 'report'):
                reference = root / (name + '-ref.json')
                reference.write_text(json.dumps(state['output_artifacts'][name]))
                exported = root / (name + '.json')
                verify.run(binary, '--project', authority, 'artifact', 'export', '--ref', reference, '--output', exported)
                values[name] = json.loads(exported.read_bytes())
            expected = 'skipped' if case in ('skip', 'extension-skip') else 'failed' if case in ('failed', 'needs-revision', 'extension-failed') else 'passed' if case in ('pass', 'untracked', 'partial-resume', 'cancel-resume', 'extension-pass') else 'blocked'
            assert values['gate']['status'] == expected, values
            assert state['outcome'] == ('succeeded' if expected in ('passed', 'skipped') else 'partial'), state['outcome']
            assert len(delivered) == (0 if expected == 'skipped' else 2 if case in ('partial-resume', 'cancel-resume', 'untracked') else 1)
            if expected == 'skipped':
                assert values['report']['session'] == 'not_run' and values['report']['skip_reason']
            assert a.snapshot(repository, base) == before, 'Workflow changed original repository'
            return {'case': case, 'host': host, 'outcome': state['outcome'], 'gate': expected,
                    'reader_deliveries': len(delivered), 'runs': len(runs), 'original_repository_unchanged': True}
        finally:
            clean(binary, authority, runs)
            verify.forget_authority(authority)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--case', choices=CASES)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    results = []
    for case in (args.case,) if args.case else CASES:
        item = run_case(binary, case)
        results.append(item)
        print(json.dumps(item), flush=True)
    if not args.case:
        for host in ('codex-app', 'claude-code'):
            results.append(run_case(binary, 'pass', host))
    value = {'prifly': verify.run(binary, 'version')['version'],
             'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
             'host': 'synthetic, no LLM judgement qualification', 'cases': results}
    if args.report:
        args.report.write_text(json.dumps(value, indent=2) + '\n')


if __name__ == '__main__':
    main()
