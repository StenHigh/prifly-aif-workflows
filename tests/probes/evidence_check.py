#!/usr/bin/env python3
"""Complete W1 Runs on released CLI; synthetic host, real program evaluator/Git."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify
from run_check import clean, git_out
from test_review_evidence import config, report

CASES = ('pass', 'required-unavailable', 'missing', 'duplicate', 'unknown', 'browser-substitution',
         'optional-ignore', 'optional-stop', 'excluded', 'not-applicable', 'failed',
         'stale-dirty', 'stale-index', 'stale-untracked', 'stale-delete', 'stale-mode',
         'stale-request', 'session-unavailable', 'blocked-resume', 'cancel-resume', 'chained-resume', 'upgrade', 'upgrade-refusal')


def read(task, name):
    return json.loads((Path(task['workspace']) / task['context']['inputs'][name]['path']).read_text())


def submit_report(binary, authority, run_id, task, report):
    template = verify.run(binary, '--project', authority, 'session', 'submit', '--template', '--run', run_id, '--attempt', task['attempt_id'])
    raw = json.dumps(report).encode()
    path = Path(task['workspace']) / task['context']['outputs']['report']['path']
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    template['result']['outputs']['report']['digest'] = 'sha256:' + hashlib.sha256(raw).hexdigest()
    template['result']['verdict'] = 'pass'
    template['result']['summary'] = 'Synthetic reviewer; no LLM/session independence claimed.'
    template['answered_questions'] = []
    template['model_profile'] = {'outcome':'unavailable','reason':'Synthetic host; model/session independence unavailable.'}
    submission = Path(task['workspace']) / 'submission.json'
    submission.write_text(json.dumps(template))
    verify.run(binary, '--project', authority, 'session', 'submit', '--file', submission)


def run_case(binary, case, host='codex-cli'):
    with tempfile.TemporaryDirectory(prefix='w1-run-') as directory:
        root = Path(directory)
        repository, authority = verify.prepare_repository(binary, root)
        runs = []
        try:
            package = repository / '.prifly/workflows/aif-review-evidence'
            shutil.copytree(verify.ROOT / 'aif-review-evidence', package, dirs_exist_ok=True)
            profile = repository / '.prifly/project.yaml'

            (repository / 'tracked.txt').write_text('original\n')
            verify.git('-C', repository, 'add', '.')
            verify.git('-C', repository, 'commit', '-qm', 'Evidence fixture')
            base = git_out(repository, 'rev-parse', 'HEAD')
            configuration = config(base, method='browser' if case == 'browser-substitution' else 'code',
                                   required=not case.startswith('optional'),
                                   optional_policy='stop' if case == 'optional-stop' else 'ignore',
                                   require_separate_session=case == 'session-unavailable')
            if case in ('excluded', 'not-applicable'):
                configuration['checks'][0]['enabled' if case == 'excluded' else 'applicable'] = False
            request_path = root / 'request.json'
            request_path.write_text(json.dumps(configuration))
            verify.run(binary, '--project', authority, 'project', 'local', 'set', '--repository', repository,
                       '--allow-executable', 'python=' + str(Path(sys.executable).resolve()))
            arguments = ('--project', authority, 'project', 'start', '--repository', repository,
                         '--launch', 'aif-review-evidence', '--host', host, '--workspace', 'worktree',
                         '--input', 'request=' + str(request_path), '--allow-execution')
            prepared = verify.run(binary, *arguments[:3], 'questionnaire', *arguments[4:], '--prepare')
            started = verify.run(binary, *arguments, '--expected-launch-digest', prepared['review_digest'])
            source = started['run']['run']['id']
            runs.append(source)
            rounds, bases, claims, tree = [], [], set(), None

            def drive(run_id, iteration):
                nonlocal tree
                for _ in range(12):
                    verify.run(binary, '--project', authority, 'run', 'drive', run_id)
                    tasks = verify.run(binary, '--project', authority, 'session', 'task', '--run', run_id, '--all')['tasks']
                    if not tasks:
                        state = verify.run(binary, '--project', authority, 'run', 'status', run_id)['run']
                        if state['status'] in ('completed', 'failed', 'cancelled'):
                            return state
                        raise AssertionError(('No task in nonterminal Run', state['status']))
                    for task in tasks:
                        assert task['skill_refs'][0]['id'] == 'aif-evidence:context/review-bridge', task.keys()
                        tree = Path(task['repository_workspace'])
                        claims.add(task['claim_id'])
                        cfg, captured = read(task, 'request'), read(task, 'candidate')
                        bases.append(captured['base_commit'])
                        rounds.append(captured['digest'])
                        item = report(cfg, captured)
                        if case == 'cancel-resume' and iteration == 0:
                            verify.run(binary, '--project', authority, 'run', 'cancel', run_id, '--reason', 'Synthetic read-only host cancelled')
                            verify.run(binary, '--project', authority, 'run', 'drive', run_id)
                            return verify.run(binary, '--project', authority, 'run', 'status', run_id)['run']
                        unavailable = case == 'required-unavailable' or case.startswith('optional') or case in ('blocked-resume', 'upgrade', 'upgrade-refusal') and iteration == 0 or case == 'chained-resume' and iteration < 2
                        if unavailable:
                            item = report(cfg, captured, 'unavailable', 'not_run')
                        elif case in ('excluded', 'not-applicable'):
                            item = report(cfg, captured, 'excluded' if case == 'excluded' else 'not_applicable', 'not_run')
                        elif case == 'stale-request': item['request_digest'] = 'sha256:' + 'a' * 64
                        elif case == 'missing': item['checks'] = []
                        elif case == 'duplicate': item['checks'] *= 2
                        elif case == 'unknown': item['checks'][0]['id'] = 'unknown'
                        elif case == 'browser-substitution': item['checks'][0]['evidence'][0]['method'] = 'code'
                        elif case == 'failed': item = report(cfg, captured, result='failed')
                        if case == 'session-unavailable': item['session'] = 'unavailable'
                        # Only static observations are invented by this synthetic host;
                        # the program's candidate measurement/evaluation are real.
                        submit_report(binary, authority, run_id, task, item)
                        if case.startswith('stale-') and case != 'stale-request':
                            action = case.removeprefix('stale-')
                            path = tree / 'tracked.txt'
                            if action == 'dirty': path.write_text('dirty\n')
                            elif action == 'index':
                                path.write_text('staged\n'); git_out(tree, 'add', 'tracked.txt'); path.write_text('original\n')
                            elif action == 'untracked': (tree / 'new.txt').write_text('new\n')
                            elif action == 'delete': path.unlink()
                            elif action == 'mode': path.chmod(0o755)
                raise AssertionError('Evidence Run did not finish')

            state = drive(source, 0)
            if case in ('blocked-resume', 'cancel-resume', 'chained-resume', 'upgrade', 'upgrade-refusal'):
                assert state.get('outcome') == 'partial' or state['status'] == 'cancelled', state
                (tree / 'tracked.txt').write_text('preserved owner edit\n')
                if case == 'upgrade':
                    bridge = package / 'contexts/review-bridge.yaml'
                    before=bridge.read_text();assert 'version: 1.1.0' in before
                    bridge.write_text(before.replace('version: 1.1.0', 'version: 1.1.1', 1))
                    instruction=package/'instructions/review-bridge.md'
                    before=instruction.read_bytes()
                    instruction.write_bytes(b'For this revised quality contract, report current evidence only. '+before)
                    assert instruction.read_bytes()!=before
                    for relative in ('steps/review.yaml', 'workflows/quality.yaml', 'workflow.yaml'):
                        p = package / relative
                        p.write_text(p.read_text().replace('version: 1.1.0', 'version: 1.1.1').replace('version: 1.0.0', 'version: 1.0.1'))
                if case == 'upgrade-refusal':
                    for relative in ('steps/configure.yaml', 'workflow.yaml'):
                        p = package / relative
                        p.write_text(p.read_text().replace('version: 1.1.0', 'version: 1.1.1').replace('version: 1.0.0', 'version: 1.0.1'))
                    p = package / 'steps/configure.yaml'
                    p.write_text(p.read_text().replace('retry_class: never', 'retry_class: pure', 1))
                for iteration in range(1, 3 if case == 'chained-resume' else 2):
                    args = ('--project', authority, 'project', 'continue', '--repository', repository,
                            '--launch', 'aif-review-evidence', '--source-run', runs[-1], '--host', host, '--allow-execution')
                    if case == 'upgrade-refusal':
                        source_before = verify.run(binary, '--project', authority, 'run', 'status', runs[-1])
                        refused = verify.run(binary, *args, '--prepare', expect_ok=False)
                        assert 'recover_prefix_changed' in refused and 'configure' in refused, refused
                        source_after = verify.run(binary, '--project', authority, 'run', 'status', runs[-1])
                        assert source_after['run_version'] == source_before['run_version']
                        assert source_after['run']['output_artifacts'] == source_before['run']['output_artifacts']
                        assert (tree / 'tracked.txt').read_text() == 'preserved owner edit\n'
                        replay = verify.run(binary, *args, '--from-stage', 'configure', '--prepare', expect_ok=False)
                        assert 'resume_prefix_empty' in replay, replay
                        assert (tree / 'tracked.txt').read_text() == 'preserved owner edit\n'
                        return {'case': case, 'host': host, 'outcome': state['outcome'], 'runs': len(runs),
                                'reader_deliveries': len(rounds), 'candidate_changed': False,
                                'prepare_refusal': 'recover_prefix_changed', 'explicit_replay_refusal': 'resume_prefix_empty'}
                    summary = verify.run(binary, *args, '--prepare')
                    resumed = verify.run(binary, *args, '--expected-launch-digest', summary['review_digest'])
                    run_id = resumed['run']['run']['id']; runs.append(run_id)
                    state = drive(run_id, iteration)
                assert state['outcome'] == 'succeeded', state
                assert (tree / 'tracked.txt').read_text() == 'preserved owner edit\n'
                assert rounds[0] != rounds[-1], 'resume reused stale candidate capture'
            expected = 'succeeded' if case in ('pass', 'optional-ignore', 'excluded', 'not-applicable', 'blocked-resume', 'cancel-resume', 'chained-resume', 'upgrade', 'upgrade-refusal') else 'partial'
            assert state.get('outcome') == expected, {k:state.get(k) for k in ('status','outcome','diagnostics')}
            assert {'gate', 'report'} <= state['output_artifacts'].keys()
            assert len(claims) == 1 and set(bases) == {base}
            assert not any(a.get('step_id','').endswith(('/repair','/commit')) for a in state['attempts'].values())
            return {'case':case,'host':host,'outcome':state['outcome'],'runs':len(runs),'reader_deliveries':len(rounds),'candidate_changed':len(set(rounds))>1}
        finally:
            clean(binary, authority, runs)
            assert not any(c['status']=='active' for c in verify.run(binary,'--project',authority,'claim','list')['claims'])
            verify.forget_authority(authority)


def main():
    if not __debug__:
        raise RuntimeError('Verification requires enabled Python assertions')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',type=Path,required=True)
    parser.add_argument('--case',choices=CASES)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args(); results=[]
    for case in (args.case,) if args.case else CASES:
        result=run_case(args.binary,case);results.append(result);print(json.dumps(result),flush=True)
    if not args.case:
        for host in ('codex-app','claude-code'):
            result=run_case(args.binary,'pass',host);results.append(result);print(json.dumps(result),flush=True)
    if args.report:
        args.report.write_text(json.dumps({'prifly':verify.run(args.binary,'version')['version'],
            'binary_sha256':hashlib.sha256(args.binary.read_bytes()).hexdigest(),
            'host':'synthetic; real evaluator and Git; no LLM/browser attestation','cases':results},indent=2)+'\n')


if __name__=='__main__':main()
