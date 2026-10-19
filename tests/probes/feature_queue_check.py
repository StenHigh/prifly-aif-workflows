#!/usr/bin/env python3
"""Released native queue -> aif-feature -> evidence -> reviewed continuation.

Synthetic assisted actors, real CLI/programs/Git/monitor HTTP. Linux only:
private HOME and task-owned monitor processes are removed on exit.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request


def digest(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def stop_monitors(binary, home):
    """Only our exact executable + private HOME; never touch the owner's monitor."""
    stopped = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            argv = (proc / 'cmdline').read_bytes().split(b'\0')
            environment = (proc / 'environ').read_bytes().split(b'\0')
            if (proc / 'exe').resolve() != binary or b'monitor' not in argv:
                continue
            if ('HOME=' + str(home)).encode() not in environment:
                continue
            os.kill(int(proc.name), signal.SIGTERM)
            stopped.append(int(proc.name))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    # Verify every process we signalled exited (or is an unreaped child).
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        alive = []
        for pid in stopped:
            try:
                status = (Path('/proc') / str(pid) / 'status').read_text()
                if 'State:\tZ' not in status:
                    alive.append(pid)
            except FileNotFoundError:
                pass
        if not alive:
            return stopped
        time.sleep(.05)
    raise AssertionError(('Owned monitors did not exit', alive))


def qualify(binary, case, root, record):
    # Import after private HOME is installed, including verify.REGISTRY.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import verify
    from feature_check import FeatureHost, task_input
    from run_check import clean, git_out

    repository, authority = verify.prepare_repository(binary, root)
    commands, runs, snapshots = [], [], {}
    record.update(case=case, result='RUNNING', commands=commands, runs=runs, snapshots=snapshots)
    h = FeatureHost(binary, authority, case, root, False)
    monitor = None

    def cli(*args, refusal=None):
        process = subprocess.run([str(binary), '--json', '--project', str(authority), *map(str, args)],
                                 capture_output=True, text=True, timeout=120)
        output = process.stdout if process.returncode == 0 else process.stderr
        value = json.loads(output.strip().splitlines()[-1])
        commands.append({'args': list(map(str, args)), 'exit_code': process.returncode, 'response': value})
        if refusal:
            assert process.returncode != 0 and value['code'] == refusal, value
        else:
            assert process.returncode == 0, value
            assert not (value.get('receipt') or {}).get('rejection'), value
        return value

    def queue(operation, *args, **kwargs):
        return cli('project', 'queue', operation, '--repository', repository, *args, **kwargs)

    def inventory():
        return {name: cli(name, 'list')[key] for name, key in [('run', 'runs'), ('claim', 'claims')]}

    def snapshot(label, task_id):
        snapshots[label] = {'queue': queue('show', '--task-id', task_id), 'inventory': inventory()}
        return snapshots[label]['queue']['task']

    def export(reference, name):
        ref_path, out_path = root / (name + '.ref.json'), root / (name + '.json')
        ref_path.write_text(json.dumps(reference))
        cli('artifact', 'export', '--ref', ref_path, '--output', out_path)
        raw = out_path.read_bytes()
        assert digest(raw) == reference['digest'], (name, reference)
        return json.loads(raw)

    try:
        (repository / 'owner.txt').write_text('Preserve owner work\n')
        (repository / '.prifly/workflows/aif-feature/extend.yaml').write_text(
            'profile: backend\nsettings:\n  quality: {limit: 3}\n  feature: {review_mode: sequential}\nexclude: []\nextensions: []\n')
        verify.git('-C', repository, 'add', '.')
        verify.git('-C', repository, 'commit', '-qm', 'Isolated feature queue fixture')
        typed = json.loads((verify.ROOT / 'examples/small-feature/backend.task.json').read_text())
        assert typed == task_input(), 'Shipped example and deterministic actor must agree'
        typed_path = root / 'feature.task.json'
        typed_path.write_text(json.dumps(typed, indent=2) + '\n')
        request = json.loads((verify.ROOT / 'examples/native-queue/queue.task.json').read_text())
        assert request['title'] == typed['title'] and request['raw_text'] == typed['description']
        assert request['in_scope'] == typed['scope']
        request['id'] = 'task:feature-queue-' + case
        request['source']['external_id'] = 'fixture:' + case
        request_path = root / 'queue.task.json'
        request_raw = (json.dumps(request, ensure_ascii=False, indent=2) + '\n').encode()
        request_path.write_bytes(request_raw)
        assert inventory() == {'run': [], 'claim': []}
        add_args = ('--input', request_path, '--priority', '10', '--command-id', 'command:add')
        added = queue('add', *add_args)
        task_id = added['result']['id']
        assert queue('add', *add_args)['duplicate'] is True
        assert len(queue('list')['tasks']) == 1
        ready = snapshot('ready', task_id)
        assert ready['state'] == 'ready' and not ready['associations']
        claim_args = ('--owner', 'session:feature-queue', '--command-id', 'command:claim')
        claimed = queue('claim-next', *claim_args)
        assert queue('claim-next', *claim_args)['result'] == claimed['result']
        task = snapshot('claimed', task_id)
        assert snapshots['claimed']['inventory'] == {'run': [], 'claim': []}
        selection = ('--task-id', task_id, '--task-owner', task['claim']['owner'],
                     '--task-revision', str(task['revision']), '--task-claim-generation', str(task['claim']['generation']))
        assert base64.b64decode(task['revisions'][0]['request_bytes']) == request_raw
        cli('project', 'local', 'set', '--repository', repository,
            '--allow-executable', 'python=' + str(Path(sys.executable).resolve()))
        common = ('--repository', repository, '--launch', 'aif-feature', '--host', 'codex-cli',
                  '--workspace', 'worktree', '--allow-execution', '--decision-policy', 'autonomous',
                  '--preflight-answer', 'plan_retention="capture"', '--preflight-answer', 'plan_tests=true',
                  '--preflight-answer', 'plan_constraints=""', *selection)
        # Queue TaskInput is intake evidence, not the workflow's typed task input.
        cli('project', 'questionnaire', *common, '--prepare', refusal='missing_input')
        assert inventory() == {'run': [], 'claim': []}
        launch = (*common, '--input', 'task=' + str(typed_path))
        prepared = cli('project', 'questionnaire', *launch, '--prepare')
        assert prepared['schema_version'] == 'project-launch-summary/4'
        assert prepared['queue_task']['task_id'] == task_id
        assert prepared['queue_task']['request_digest'] == digest(request_raw)
        assert prepared['input_digests']['task'] == digest(typed_path.read_bytes())
        assert inventory() == {'run': [], 'claim': []}
        start_args = (*launch, '--expected-launch-digest', prepared['review_digest'], '--command-id', 'command:start')
        started = cli('project', 'start', *start_args)
        rid = started['run_id']; runs.append(rid)
        assert cli('project', 'start', *start_args)['run_id'] == rid
        assert len(inventory()['run']) == 1
        assert len(snapshot('admitted', task_id)['associations']) == 1
        queue('complete', *selection, '--command-id', 'command:premature-complete',
              '--reason', 'Negative fixture: live Run must prevent completion', refusal='queue_task_busy')
        state = h.drive_feature(rid)
        source = json.loads(json.dumps(state))
        source_view = cli('run', 'status', rid)
        first_outputs = {port: export(ref, 'source-' + port) for port, ref in state['output_artifacts'].items()}
        if case != 'backend':
            assert (state.get('outcome') == 'partial' if case == 'blocked-resume' else state['status'] == 'cancelled'), state
            stopped = snapshot('stopped', task_id)
            assert stopped['state'] == 'claimed' and len(stopped['associations']) == 1
            assert 'commit' not in [item['step'] for item in h.seen]
            if case == 'blocked-resume':
                assert first_outputs['gate']['status'] == 'blocked'
                assert first_outputs['evidence']['reports']['checks']['checks'][0]['status'] == 'unavailable'
            from test_review_evidence import evidence as w1
            source_candidate = w1.snapshot(h.tree, h.base)
            # Deliberate owner edits between Runs; no editing a live reader's candidate.
            (h.tree / 'owner.txt').write_text('Preserved tracked owner edit across queue continuation\n')
            (h.tree / 'owner-note.txt').write_text('Preserved untracked owner note\n')
            before_continue = {name: (h.tree / name).read_bytes() for name in ('owner.txt', 'owner-note.txt', 'greeting.py', 'test_greeting.py')}
            h.iteration = 1
            cont_base = ('--repository', repository, '--launch', 'aif-feature', '--host', 'codex-cli',
                         '--source-run', rid, '--allow-execution')
            cli('project', 'continue', *cont_base, '--prepare', refusal='queue_source_identity_conflict')
            cont = (*cont_base, *selection)
            prep = cli('project', 'continue', *cont, '--prepare')
            assert prep['queue_task'] == prepared['queue_task']
            assert len(inventory()['run']) == 1
            assert all((h.tree / name).read_bytes() == raw for name, raw in before_continue.items())
            cont_args = (*cont, '--expected-launch-digest', prep['review_digest'], '--command-id', 'command:continue')
            resumed = cli('project', 'continue', *cont_args)
            rid = resumed['run_id']; runs.append(rid)
            assert rid != runs[0]
            assert cli('project', 'continue', *cont_args)['run_id'] == rid
            assert len(inventory()['run']) == 2
            assert all((h.tree / name).read_bytes() == raw for name, raw in before_continue.items())
            prefix = len(h.seen)
            state = h.drive_feature(rid)
            resumed_steps = [item['step'] for item in h.seen[prefix:]]
            assert not {'warmup', 'plan', 'implement', 'repair'} & set(resumed_steps), resumed_steps
            assert {'checks', 'security', 'review', 'commit'} <= set(resumed_steps), resumed_steps
            assert all((h.tree / name).read_bytes() == raw for name, raw in before_continue.items())
            source_after = cli('run', 'status', runs[0])
            assert source_after['run_version'] == source_view['run_version']
            assert source_after['run'] == source, 'Continuation changed historical source Run'
            resumed_rounds = [item for item in h.rounds if item['run'] == rid]
            assert resumed_rounds and all(item['digest'] != source_candidate['digest'] for item in resumed_rounds), 'Old candidate accepted after owner edit'
        assert state['outcome'] == 'succeeded'
        assert len(h.claims) == 1
        outputs = {port: export(ref, 'final-' + port) for port, ref in state['output_artifacts'].items()}
        assert outputs['gate']['status'] in ('passed', 'warnings')
        evidence = outputs['evidence']
        assert set(evidence['reports']) == {'checks', 'security', 'review'}
        for lens, report in evidence['reports'].items():
            assert report['candidate'] == evidence['candidate'], (lens, report)
            assert all(item['status'] == 'executed' and item['result'] == 'passed' for item in report['checks']), report
        final_task = snapshot('succeeded-not-completed', task_id)
        assert final_task['state'] == 'claimed', 'Run success must not auto-complete the queue task'
        assert [item['run_id'] for item in final_task['associations']] == runs
        assert len(inventory()['claim']) == 1
        for run in runs:
            recorded = cli('run', 'status', run)['run']
            assert recorded['queue_task']['selection'] == prepared['queue_task']
            assert base64.b64decode(recorded['queue_request_bytes']) == request_raw
        # Read the actual full monitor API on a separate owned loopback listener.
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
        with (root / 'monitor.log').open('w') as log:
            monitor = subprocess.Popen([str(binary), '--project', str(authority), 'monitor', '--addr', f'127.0.0.1:{port}'], stdout=log, stderr=log)
        base_url = f'http://127.0.0.1:{port}'
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        def http(path, **query):
            with opener.open(base_url + path + '?' + urllib.parse.urlencode(query), timeout=5) as response:
                return json.load(response)
        deadline = time.monotonic() + 10
        while True:
            try:
                http('/api/health'); break
            except OSError:
                assert monitor.poll() is None and time.monotonic() < deadline
                time.sleep(.05)
        deadline = time.monotonic() + 10
        while True:
            monitor_runs = http('/api/runs')
            if {item['run_id'] for item in monitor_runs['runs']} == set(runs):
                break
            assert time.monotonic() < deadline, monitor_runs
            time.sleep(.1)
        monitor_source = hashlib.sha256(str(authority.resolve()).encode()).hexdigest()
        monitor_run = http('/api/run', source=monitor_source, id=rid)
        assert monitor_run['run']['id'] == rid and monitor_run['run']['outcome'] == 'succeeded'
        monitor_artifact = http('/api/artifact', source=monitor_source, **state['output_artifacts']['evidence'], full='1')
        assert json.loads(monitor_artifact['content']) == evidence
        assert not monitor_artifact['truncated']
        complete_args = (*selection, '--reason', 'Fixture owner inspected current review evidence and local commit; no external publication',
                         '--command-id', 'command:complete')
        queue('complete', *complete_args)
        assert queue('complete', *complete_args)['duplicate'] is True
        completed = snapshot('completed', task_id)
        assert completed['state'] == 'done'
        assert completed['associations'] == final_task['associations']
        assert base64.b64decode(completed['revisions'][0]['request_bytes']) == request_raw
        record.update({'case': case, 'result': 'PASS', 'task_id': task_id, 'runs': runs,
                'initial_outcome': source.get('outcome') or source['status'], 'outcome': state['outcome'],
                'same_workspace_claim': len(h.claims) == 1, 'original_request_digest': digest(request_raw),
                'typed_input_digest': digest(typed_path.read_bytes()), 'snapshots': snapshots,
                'source_outputs': first_outputs, 'final_outputs': outputs, 'rounds': h.rounds, 'steps': h.seen,
                'monitor': {'runs': monitor_runs, 'run': monitor_run, 'evidence': monitor_artifact},
                'commands': commands})
    finally:
        if monitor:
            monitor.terminate(); monitor.wait(timeout=10)
        # Includes an admitted Run even if a subsequent assertion failed.
        all_runs = [item['run_id'] for item in verify.run(binary, '--project', authority, 'run', 'list')['runs']]
        clean(binary, authority, all_runs)
        assert not any(item['status'] == 'active' for item in verify.run(binary, '--project', authority, 'claim', 'list')['claims'])
        record['claims_released'] = True
        verify.forget_authority(authority)


def main():
    if not __debug__:
        raise RuntimeError('Verification requires enabled assertions')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--case', choices=('backend', 'blocked-resume', 'cancel-resume'))
    args = parser.parse_args()
    if sys.platform != 'linux':
        parser.error('This isolated process cleanup is qualified on Linux only')
    binary, report_path = args.binary.resolve(strict=True), args.report.resolve()
    report = {'schema_version': 'feature-queue-qualification/1', 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
              'mode': 'synthetic assisted actors, real released CLI/programs/Git/full-monitor HTTP; no live host/model or browser attestation',
              'cases': [], 'cleanup': {}}
    try:
        with tempfile.TemporaryDirectory(prefix='aif-feature-queue-') as directory:
            root = Path(directory); home = root / 'home'; home.mkdir()
            os.environ.update(HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'), XDG_CACHE_HOME=str(home / '.cache'),
                              XDG_DATA_HOME=str(home / '.local/share'), GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1')
            try:
                version = subprocess.run([str(binary), '--json', 'version'], capture_output=True, text=True, check=True, timeout=30)
                report['prifly'] = json.loads(version.stdout)
                for case in ([args.case] if args.case else ['backend', 'blocked-resume', 'cancel-resume']):
                    stand = root / case; stand.mkdir()
                    record = {'case': case}
                    report['cases'].append(record)
                    qualify(binary, case, stand, record)
                    print(json.dumps({'case': case, 'result': 'PASS'}), flush=True)
            finally:
                report['cleanup']['stopped_owned_monitors'] = stop_monitors(binary, home)
        report['cleanup']['temporary_root_removed'] = not root.exists()
        report['result'] = 'PASS'
    except BaseException as error:
        report['result'] = 'FAIL'
        report['error'] = repr(error)
        raise
    finally:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
