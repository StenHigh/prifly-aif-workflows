#!/usr/bin/env python3
"""Opt-in W5 host observation: paired sequential/parallel fresh Codex CLI readers.

Uses real host usage. No expected verdict is supplied to actors. This qualifies
only these read-only backend deliveries, never the feature repair workflow.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from threading import Timer
import time

from parallel_check import Fixture, read, aggregate, evidence, verify


def actor(f, task, destination):
    workspace = Path(task['workspace'])
    destination.mkdir(parents=True)
    task_file = workspace / 'task.json'
    task_file.write_text(json.dumps(task, indent=2))
    template = f.call('session', 'submit', '--template', '--run', f.rid, '--attempt', task['attempt_id'])
    (workspace / 'submission-template.json').write_text(json.dumps(template, indent=2))
    prompt = f'''Execute exactly one delivered Pri-Fly read-only review Attempt.
Read {task_file}, the delivered sealed skills/contexts, bound input artifacts and submission-template.json. Inspect only the named repository_workspace and perform the declared checks. This is an isolated Python stdlib fixture. Derive your own assessment from actual observations; no expected result is supplied.
Do not repair, change source/configuration, install dependencies, create repository audit files, manage resources or invoke Pri-Fly control. Write outputs only into the allocated task workspace. Each evidence entry must preserve its check's declared method: code evidence has method code and exit_code null, including any supplementary command described as narrative context. Command checks, if declared, require command evidence and actual exit code. No fabricated execution or independence.
Use the submission template's identity fields unchanged. Copy the candidate unchanged. The report request_digest is the delivered request ref.digest. Follow the sealed report schema exactly and cover every check once. Put the report in the allocated output slot, compute its actual SHA-256, and write submission.json in the task workspace. answered_questions is [] if none were met.
The controller started this fresh CLI session without the author's conversation; no independent-review mapping to a different model is provided. Report separate session and model availability independently. Native model_profile has outcome unavailable/declined and reason, or honoured with named if actually established. Typed report model_profile is a string, and unavailable/declined uses model null. Do not invent another model.
Commands remain sandboxed with automatic approval review. If bwrap prevents the exact bounded read-only command from starting, request require_escalated for that command and explain the fixture read. Do not disable sandbox or broaden scope. A rejected command stays rejected; report unavailable if necessary.
Do not submit your result: the controller submits the exact unedited file. Finish with its paths.'''
    (destination / 'prompt.txt').write_text(prompt)
    command = ['codex', 'exec', '--ephemeral', '--json', '--approve-for-me', '--add-dir', task['repository_workspace'],
               '-C', str(workspace), '--skip-git-repo-check', '-o', str(workspace / 'host-final.txt'), '-']
    start = time.monotonic()
    events, started, ended, session, usage = [], None, None, None, None
    with (destination / 'events.jsonl').open('w') as out, (destination / 'stderr.txt').open('w') as err:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err, text=True)
        timeout = Timer(600, process.kill)
        timeout.daemon = True
        timeout.start()
        try:
            process.stdin.write(prompt); process.stdin.close()
            for line in process.stdout:
                out.write(line); out.flush()
                observed = time.monotonic()
                try: event = json.loads(line)
                except ValueError: continue
                kind = event.get('type')
                if kind == 'thread.started': session = event['thread_id']
                if kind == 'turn.started': started = observed
                if kind == 'turn.completed': ended, usage = observed, event.get('usage')
                if kind in ('item.started', 'item.completed'):
                    item = event.get('item', {})
                    events.append({'event': kind, 'type': item.get('type'), 'observed_monotonic': observed,
                                   'exit_code': item.get('exit_code')})
                if observed - start > 600:
                    raise TimeoutError('Owned reader exceeded qualification time allowance')
            code = process.wait(timeout=15)
        finally:
            timeout.cancel()
            if process.poll() is None: process.kill(); process.wait()
    assert code == 0 and session and started and ended and usage, (code, destination)
    submission = workspace / 'submission.json'
    report_file = workspace / task['context']['outputs']['report']['path']
    result = json.loads(submission.read_text())
    assert result['result']['outputs']['report']['digest'] == evidence.digest(report_file.read_bytes())
    for name, source in (('task.json', task_file), ('submission.json', submission), ('report.json', report_file)):
        shutil.copyfile(source, destination / name)
    return {'attempt_id': task['attempt_id'], 'session_id': session, 'started_monotonic': started,
            'ended_monotonic': ended, 'elapsed_seconds': ended - started, 'usage': usage,
            'events_digest': evidence.digest((destination / 'events.jsonl').read_bytes()),
            'submission_digest': evidence.digest(submission.read_bytes()), 'report_digest': evidence.digest(report_file.read_bytes()),
            'tool_events': events, 'submission': str(submission), 'report': json.loads(report_file.read_text())}


def observe(binary, skills, artifacts, mode):
    with tempfile.TemporaryDirectory(prefix='w5-live-') as directory:
        root = Path(directory)
        f = Fixture(binary, root, 'pass', parallelism=2 if mode == 'parallel' else 1, skills=skills)
        observations = []
        try:
            f.drive()
            while tasks := f.tasks():
                assert len(tasks) == (2 if mode == 'parallel' else 1)
                basis = read(tasks[0], 'candidate')
                assert all(read(t, 'candidate') == basis for t in tasks)
                before, version = evidence.snapshot(tasks[0]['repository_workspace'], f.base), f.state()['run_version']
                with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
                    futures = [pool.submit(actor, f, task, artifacts / mode / str(len(observations) + i)) for i, task in enumerate(tasks)]
                    delivered = [future.result() for future in futures]
                assert f.state()['run_version'] == version, 'Reader changed the authority'
                assert evidence.snapshot(tasks[0]['repository_workspace'], f.base) == before, 'Reader changed source'
                for observation in delivered:
                    f.call('session', 'submit', '--file', observation.pop('submission'))
                    observations.append(observation)
                f.drive()
            state = f.state()['run']
            assessment = aggregate(f.call, root, state)
            assert len(observations) == 2 and len({o['session_id'] for o in observations}) == 2
            overlap = max(0, min(o['ended_monotonic'] for o in observations) - max(o['started_monotonic'] for o in observations))
            assert (overlap > 0) == (mode == 'parallel'), (mode, overlap)
            return {'mode': mode, 'host': 'codex-cli', 'code_digest': evidence.digest((f.repo / 'calc.py').read_bytes()),
                    'check_scope': f.configuration['checks'], 'optional_policy': f.configuration['optional_policy'],
                    'reader_observations': observations, 'overlap_seconds': overlap,
                    'reader_wall_span_seconds': max(o['ended_monotonic'] for o in observations) - min(o['started_monotonic'] for o in observations),
                    'usage_total': {k: sum(o['usage'].get(k, 0) for o in observations) for k in ('input_tokens', 'cached_input_tokens', 'output_tokens')},
                    'source_and_authority_unchanged_by_readers': True, 'outcome': state['outcome'], 'assessment': assessment}
        finally: f.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', required=True, type=Path)
    p.add_argument('--skills', required=True, type=Path, help='Pinned AI Factory 2.19 review/severity files')
    p.add_argument('--artifacts', required=True, type=Path, help='Private exact event/report destination')
    p.add_argument('--report', required=True, type=Path)
    args = p.parse_args(); args.artifacts.mkdir(parents=True, exist_ok=True)
    result = {'prifly': verify.run(args.binary, 'version')['version'],
              'binary_sha256': hashlib.sha256(args.binary.read_bytes()).hexdigest(),
              'host_version': subprocess.run(['codex', '--version'], capture_output=True, text=True, check=True).stdout.strip(),
              'skills_digest': {n: evidence.digest((args.skills / n).read_bytes()) for n in ('aif-review.md', 'severity.md')},
              'boundary': 'One paired observation, identical code/check scope, fresh sessions. Host reports and observed timings, not different-model attestation or a cost/quality benefit estimate. No browser, repair, automatic production aggregator or feature mode.'}
    result['runs'] = []
    for mode in ('sequential', 'parallel'):
        value = observe(args.binary, args.skills, args.artifacts, mode); result['runs'].append(value)
        args.report.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({'mode': mode, 'outcome': value['outcome'], 'overlap_seconds': value['overlap_seconds'], 'usage_total': value['usage_total']}), flush=True)
    assert result['runs'][0]['code_digest'] == result['runs'][1]['code_digest']
    assert result['runs'][0]['check_scope'] == result['runs'][1]['check_scope']


if __name__ == '__main__': main()
