"""Opt-in host controller for W5 handoffs, using only public Pri-Fly commands.

Does not select/start/drive/continue a Run or handle its writers. The caller
keeps its normal host loop and invokes service only for the named handoffs.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile
from threading import Timer
import time

import evidence as w1
import parallel_reports as transport

PROTOCOL = 'aif-feature-parallel-host/1'


def verify_adapter(task):
    """Pin the installed controller files to this Run's sealed context contract."""
    matches = [ref for ref in task.get('skill_refs', [])
               if ref['id'] == 'aif-feature:context/parallel-adapter-contract']
    if len(matches) != 1:
        raise w1.Invalid('Missing reviewed parallel adapter contract')
    ref = matches[0]
    name = re.sub(r'[^a-zA-Z0-9.-]', '-', ref['id'] + '@' + ref['version']).strip('-')
    raw = (Path(task['workspace']) / 'context/skills' / name).read_bytes()
    if w1.digest(raw) != ref['digest']:
        raise w1.Invalid('Parallel adapter contract bytes differ from pinned context')
    contract = transport.strict_json(raw)
    files = {'parallel_host.py': Path(__file__), 'parallel_reports.py': Path(transport.__file__),
             'evidence.py': Path(w1.__file__)}
    if contract.get('protocol') != PROTOCOL or set(contract.get('files', {})) != set(files):
        raise w1.Invalid('Unsupported parallel adapter contract')
    for name, path in files.items():
        if w1.digest(path.read_bytes()) != contract['files'][name]:
            raise w1.Invalid('Installed adapter differs from reviewed source: ' + name)


def call(binary, authority, *args):
    result = subprocess.run([str(binary), '--json', '--project', str(authority), *map(str, args)],
                            capture_output=True, text=True, timeout=120)
    if result.returncode:
        try:
            code = json.loads((result.stderr or result.stdout).strip().splitlines()[-1]).get('code', 'unknown_problem')
        except (ValueError, IndexError):
            code = 'invalid_problem'
        raise w1.Invalid('Public CLI operation failed: ' + ' '.join(map(str, args[:2])) + ' (' + str(code) + ')')
    value = transport.strict_json(result.stdout)
    rejection = (value.get('receipt') or {}).get('rejection')
    if rejection:
        raise w1.Invalid('Public CLI receipt refused: ' + str(rejection.get('code', rejection)))
    return value


def read(task, port):
    return transport.strict_json((Path(task['workspace']) / task['context']['inputs'][port]['path']).read_bytes())


def role(task):
    refs = task.get('skill_refs') or []
    if not refs:
        return None
    prefix = 'aif-feature:context/feature-'
    value = refs[0]['id']
    return value[len(prefix):] if value.startswith(prefix) else None


def admission(binary, authority, host, codex='codex'):
    value = {'protocol': PROTOCOL, 'status': 'unavailable', 'host': host,
             'reason': 'Only the explicit codex-cli dispatcher is qualified for backend review.'}
    if host != 'codex-cli':
        return value
    try:
        version = call(binary, authority, 'version')['version']
        if not re.fullmatch(r'\d+\.\d+\.\d+', version) or tuple(map(int, version.split('.'))) < (0, 13, 77):
            raise w1.Invalid('Parallel review requires released Pri-Fly >=0.13.77')
        executable = shutil.which(str(codex))
        if not executable:
            raise w1.Invalid('Codex CLI independent-session dispatcher is unavailable')
        check = subprocess.run([executable, '--version'], capture_output=True, text=True, timeout=20)
        if check.returncode or not check.stdout.strip():
            raise w1.Invalid('Codex CLI availability check failed')
        value.update(status='ready', reason='Explicit independent codex exec dispatcher and public artifact export; '
                     'Pri-Fly ' + version + '; ' + check.stdout.strip())
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        value['reason'] = str(error)[:4000]
    return value


def collect(binary, authority, task):
    """Export only manifest refs; encode original bytes, never serialize reports."""
    reference = task['context']['inputs']['manifest']['ref']
    expected = reference['digest']
    try:
        verify_adapter(task)
        path = Path(task['workspace']) / task['context']['inputs']['manifest']['path']
        if w1.digest(path.read_bytes()) != expected:
            raise w1.Invalid('Delivered manifest differs from its sealed digest')
        manifest = read(task, 'manifest')
        refs = transport.report_refs(manifest)
        entries = []
        with tempfile.TemporaryDirectory(prefix='sealed-reports-', dir=task['workspace']) as temporary:
            for branch, ref in refs.items():
                root = Path(temporary)
                ref_file, exported = root / (branch + '-ref.json'), root / (branch + '-report.json')
                ref_file.write_bytes(w1.encoded(ref))
                call(binary, authority, 'artifact', 'export', '--ref', ref_file, '--output', exported)
                if exported.stat().st_size > transport.MAX_REPORT_BYTES:
                    raise w1.Invalid('Report exceeds 4 MiB transport bound')
                raw = exported.read_bytes()
                if w1.digest(raw) != ref['digest']:
                    raise w1.Invalid('Exported report differs from its sealed digest')
                entries.append({'branch': branch, 'ref': ref, 'raw_base64': base64.b64encode(raw).decode('ascii')})
        bundle = {'schema_version': '1', 'manifest_digest': expected, 'status': 'ready', 'reason': '', 'reports': entries}
        transport.unpack(manifest, expected, bundle)
        return bundle
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        return transport.unavailable(expected, error)


def submit_values(binary, authority, task, values):
    template = call(binary, authority, 'session', 'submit', '--template', '--run', task['run_id'], '--attempt', task['attempt_id'])
    for port, value in values.items():
        path = Path(task['workspace']) / task['context']['outputs'][port]['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = w1.encoded(value) + b'\n'
        path.write_bytes(raw)
        template['result']['outputs'][port]['digest'] = w1.digest(raw)
    ready = all(value.get('status') == 'ready' for value in values.values())
    template['result'].update(verdict='pass' if ready else 'blocked', summary='Exact host adapter output; no quality verdict chosen.')
    template['answered_questions'] = []
    path = Path(task['workspace']) / 'host-adapter-submission.json'
    path.write_bytes(w1.encoded(template) + b'\n')
    call(binary, authority, 'session', 'submit', '--file', path)


def reader(task, codex, destination, timeout):
    """One fresh, bounded CLI actor; it gets no authority handle or writer role."""
    workspace = Path(task['workspace'])
    prompt = '''Execute exactly one read-only Pri-Fly reader Attempt. Read parallel-task.json,
parallel-template.json, its sealed instructions/supporting skills and bound inputs.
Use only the named repository_workspace and declared task scope. Actually perform
each enabled applicable criterion. No author conversation or expected verdict is supplied.
Do not repair, write repository files, install dependencies, manage environments,
start other workflows or invoke Pri-Fly control. Write only into this task workspace.
Follow the pinned typed report and native submission template exactly. Preserve
method, candidate, request ref.digest and round; every declared check appears once.
Unavailable checks remain unavailable/not_run. No fabricated evidence or model mapping.
This is a fresh separate CLI session. No independent-model translation is supplied:
report model_profile unavailable and model null unless actually established.
Native submission model_profile is the template object (outcome unavailable with reason),
whereas the typed report uses the string unavailable. answered_questions=[] if none.
Write the report in its output slot, calculate the exact SHA-256 and write a native
submission to parallel-submission.json. Do not submit it: controller submits unchanged.
Commands retain sandbox and automatic review. If bwrap blocks a scoped command,
request require_escalated for that exact command; a rejection means unavailable.
'''
    (destination / 'prompt.txt').write_text(prompt)
    command = [str(codex), 'exec', '--ephemeral', '--json', '--approve-for-me', '--add-dir', task['repository_workspace'],
               '-C', str(workspace), '--skip-git-repo-check', '-o', str(workspace / 'parallel-final.txt'), '-']
    session, started, ended, usage = None, None, None, None
    with (destination / 'events.jsonl').open('w') as events, (destination / 'stderr.txt').open('w') as errors:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors,
                                   text=True, start_new_session=True)
        def stop():
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        timer = Timer(timeout, stop)
        timer.daemon = True
        timer.start()
        try:
            process.stdin.write(prompt)
            process.stdin.close()
            for line in process.stdout:
                events.write(line)
                events.flush()
                event = json.loads(line)
                if event.get('type') == 'thread.started': session = event['thread_id']
                if event.get('type') == 'turn.started': started = time.monotonic()
                if event.get('type') == 'turn.completed': ended, usage = time.monotonic(), event.get('usage')
            code = process.wait()
        finally:
            timer.cancel()
            stop()
            process.wait()
    if code or not session or started is None or ended is None or usage is None:
        raise w1.Invalid('Independent reader did not finish; settle the actual actor before native cancellation/recovery')
    submission = workspace / 'parallel-submission.json'
    native = transport.strict_json(submission.read_bytes())
    report = workspace / task['context']['outputs']['report']['path']
    if native['result']['outputs']['report']['digest'] != w1.digest(report.read_bytes()):
        raise w1.Invalid('Reader submission digest differs from original report bytes')
    for source, name in ((submission, 'submission.json'), (report, 'report.json')):
        shutil.copyfile(source, destination / name)
    return {'role': role(task), 'attempt_id': task['attempt_id'], 'session_id': session,
            'started_monotonic': started, 'ended_monotonic': ended, 'usage': usage,
            'submission': str(submission), 'submission_digest': w1.digest(submission.read_bytes()),
            'report_digest': w1.digest(report.read_bytes()), 'events_digest': w1.digest((destination / 'events.jsonl').read_bytes())}


def dispatch(binary, authority, tasks, *, codex='codex', artifacts, timeout=600):
    """Wait for every actor before any submission; no repair or unknown-effect retry."""
    tasks = sorted(tasks, key=lambda t: transport.READERS.index(role(t)) if role(t) in transport.READERS else 99)
    if [role(t) for t in tasks] != list(transport.READERS):
        raise w1.Invalid('Dispatcher requires exactly the security/review pair')
    for task in tasks:
        verify_adapter(task)
    if (len({t['run_id'] for t in tasks}) != 1 or len({t['attempt_id'] for t in tasks}) != 2
            or len({t['workspace'] for t in tasks}) != 2 or len({t['claim_id'] for t in tasks}) != 1
            or len({t['repository_workspace'] for t in tasks}) != 1):
        raise w1.Invalid('Reader deliveries do not share one candidate/claim with separate Attempts/workspaces')
    basis = read(tasks[0], 'candidate')
    if basis != read(tasks[1], 'candidate') or read(tasks[0], 'request')['round'] != read(tasks[1], 'request')['round']:
        raise w1.Invalid('Readers belong to different candidates/rounds')
    before = w1.snapshot(tasks[0]['repository_workspace'], basis['base_commit'])
    if before != basis:
        raise w1.Invalid('Candidate moved before concurrent dispatch')
    root = Path(artifacts)
    destinations = []
    # Authority control stays in this one controller. Parallel actors never
    # race session take/template/submit or receive an authority handle.
    for task in tasks:
        workspace = Path(task['workspace'])
        claim = os.open(workspace / 'parallel-dispatch.claim', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(claim, 'w') as locked:
            locked.write(task['attempt_id'] + '\n')
        destination = root / role(task) / task['attempt_id'].replace(':', '-')
        destination.mkdir(parents=True, exist_ok=False)
        destinations.append(destination)
        call(binary, authority, 'session', 'take', '--run', task['run_id'], '--attempt', task['attempt_id'])
        template = call(binary, authority, 'session', 'submit', '--template', '--run', task['run_id'], '--attempt', task['attempt_id'])
        (workspace / 'parallel-task.json').write_bytes(w1.encoded(task))
        (workspace / 'parallel-template.json').write_bytes(w1.encoded(template))
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(reader, task, codex, destination, timeout) for task,destination in zip(tasks,destinations)]
        observations = [future.result() for future in futures]
    if len({o['session_id'] for o in observations}) != 2:
        raise w1.Invalid('Host reused a reader session')
    if w1.snapshot(tasks[0]['repository_workspace'], basis['base_commit']) != before:
        raise w1.Invalid('Read-only actor changed candidate; preserve work and use native recovery')
    for observation in observations:
        call(binary, authority, 'session', 'submit', '--file', observation['submission'])
    return observations


def service(binary, authority, tasks, *, host, codex='codex', artifacts=None):
    """One handoff batch. False means the normal host must handle these tasks."""
    roles = [role(t) for t in tasks]
    if roles == ['parallel-admission']:
        try:
            verify_adapter(tasks[0])
            value = admission(binary, authority, host, codex)
        except (ValueError, OSError, KeyError, TypeError) as error:
            value = {'protocol': PROTOCOL, 'status': 'unavailable', 'host': host, 'reason': str(error)[:4000]}
        submit_values(binary, authority, tasks[0], {'admission': value})
        return {'handled': True, 'role': roles[0]}
    if roles == ['collect-reviews']:
        submit_values(binary, authority, tasks[0], {'bundle': collect(binary, authority, tasks[0])})
        return {'handled': True, 'role': roles[0]}
    if len(roles) == 2 and set(roles) == set(transport.READERS):
        if host != 'codex-cli' or artifacts is None:
            raise w1.Invalid('Qualified dispatcher and an owned artifact directory are required')
        return {'handled': True, 'role': 'parallel-readers',
                'observations': dispatch(binary, authority, tasks, codex=codex, artifacts=artifacts)}
    return {'handled': False, 'reason': 'Use the existing host for this ordinary feature handoff'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--run', required=True)
    parser.add_argument('--host', choices=('codex-cli', 'codex-app', 'claude-code'), required=True)
    parser.add_argument('--codex', default='codex')
    parser.add_argument('--artifacts', type=Path, required=True, help='Owned directory for exact reader events/submissions')
    args = parser.parse_args()
    tasks = call(args.binary, args.project, 'session', 'task', '--run', args.run, '--all')['tasks']
    print(json.dumps(service(args.binary, args.project, tasks, host=args.host, codex=args.codex, artifacts=args.artifacts)))


if __name__ == '__main__':
    main()
