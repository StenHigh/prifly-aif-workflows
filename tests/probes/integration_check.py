"""Full W4 Runs: real isolated merge/check/CAS; synthetic or fresh CLI final reader."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify
from integration_fixture import EXAMPLE, fixture, install, i, report, FakeGitLab, publication, publication_spec
from evidence_check import read
from run_check import clean

CASES = ('assess', 'local-merge', 'semantic-regression', 'conflict', 'unrelated-target', 'owner-required', 'owner-approved',
         'missing-tool', 'source-stale', 'dirty-start', 'dirty-source', 'moving-candidate', 'moving-target',
         'final-defect', 'missing-spot', 'reader-unavailable', 'reader-no-report', 'partial-resume', 'cancel-resume',
         'draft-repeat', 'draft-lost-ack', 'draft-format', 'draft-unknown', 'draft-no-receipt', 'draft-reentry')


def submit(binary, authority, rid, task, port, value, verdict='pass', expect_ok=True):
    template = verify.run(binary, '--project', authority, 'session', 'submit', '--template', '--run', rid, '--attempt', task['attempt_id'])
    if port is None:
        template['result']['outputs'] = {}
    else:
        output = Path(task['workspace']) / task['context']['outputs'][port]['path']
        output.write_bytes(i.w1.encoded(value) + b'\n')
        template['result']['outputs'][port]['digest'] = i.w1.digest(output.read_bytes())
    template['result']['verdict'] = verdict
    template['result']['summary'] = 'Offline W4 provider/synthetic reader; actual isolated Git and commands'
    template['answered_questions'] = []
    if task.get('model_profile'):
        template['model_profile'] = {'outcome': 'unavailable', 'reason': 'Synthetic host; no actual model choice or fresh session'}
    path = Path(task['workspace']) / 'submission.json'
    path.write_text(json.dumps(template))
    return verify.run(binary, '--project', authority, 'session', 'submit', '--file', path, expect_ok=expect_ok)


def live_reader(binary, authority, rid, task, artifacts):
    workspace = Path(task['workspace'])
    (workspace / 'task.json').write_text(json.dumps(task, indent=2))
    template = verify.run(binary, '--project', authority, 'session', 'submit', '--template', '--run', rid, '--attempt', task['attempt_id'])
    (workspace / 'submission-template.json').write_text(json.dumps(template, indent=2))
    assessment = read(task, 'assessment')
    integration_tree = Path(assessment['session']['path']) / 'tree'
    source = Path(task['repository_workspace'])
    prompt = f'''Execute exactly this delivered Pri-Fly final-reader Attempt. Read {workspace / 'task.json'}, all delivered skill/context references, inputs and submission-template.json. Follow the sealed final-reader bridge. The exact owned merged tree is {integration_tree}; the source repository {source} is read-only. Inspect the actual merged code for every declared spot-check description and the source/integrated command reports. No expected result is supplied. Do not repair, change policy, commit, publish, release or call Pri-Fly control commands.
Write the exact typed W1 report into the allocated report output slot and compute its digest. Copy the delivered request artifact digest, round and integration candidate unchanged. Actual session separate and actual model choice are different; no alternate-model mapping is supplied, so report unavailable model/null honestly. Use the native template identity and report fields unchanged; answered_questions is [] when none were met. Native model_profile object uses outcome and reason, while typed report model_profile is a string. Complete submission.json in this task workspace. Do not submit it yourself; the controller submits your file unchanged.
Your sandbox grants only this task and the exact fixture source/integration directories. If shell fails before launch due to bwrap, request automatic review for the same bounded read-only command. Do not disable sandbox or request blanket access. If access cannot be granted, return an honest unavailable check. No credentials or unrelated projects are needed.'''
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / 'prompt.txt').write_text(prompt)
    before = i.w1.snapshot(source, read(task, 'handoff')['acceptance'][0]['report']['candidate']['base_commit'])
    version = verify.run(binary, '--project', authority, 'run', 'status', rid)['run_version']
    started = time.monotonic()
    with (artifacts / 'events.jsonl').open('w') as out, (artifacts / 'stderr.txt').open('w') as err:
        result = subprocess.run(['codex', 'exec', '--ephemeral', '--json', '--approve-for-me',
                                 '--add-dir', str(source), '--add-dir', str(integration_tree),
                                 '-C', str(workspace), '--skip-git-repo-check', '-o', str(workspace / 'final.txt'), '-'],
                                input=prompt, text=True, stdout=out, stderr=err, timeout=600)
    assert result.returncode == 0, (artifacts / 'stderr.txt').read_text()
    assert i.w1.snapshot(source, before['base_commit']) == before
    assert verify.run(binary, '--project', authority, 'run', 'status', rid)['run_version'] == version
    submission = workspace / 'submission.json'
    raw = submission.read_bytes()
    report_data = (workspace / task['context']['outputs']['report']['path']).read_bytes()
    (artifacts / 'report.json').write_bytes(report_data)
    (artifacts / 'submission.json').write_bytes(raw)
    verify.run(binary, '--project', authority, 'session', 'submit', '--file', submission)
    assert submission.read_bytes() == raw
    events = [json.loads(line) for line in (artifacts / 'events.jsonl').read_text().splitlines() if line.strip()]
    sessions = [e['thread_id'] for e in events if e.get('type') == 'thread.started']
    assert len(sessions) == 1
    observed = {'cli': subprocess.run(['codex', '--version'], capture_output=True, text=True, check=True).stdout.strip(),
                'session': sessions[0], 'elapsed_seconds': round(time.monotonic() - started, 3),
                'submission_digest': i.w1.digest(raw), 'report_digest': i.w1.digest(report_data),
                'event_digest': i.w1.digest((artifacts / 'events.jsonl').read_bytes()),
                'report': json.loads(report_data), 'usage': [e for e in events if e.get('type') == 'turn.completed'],
                'source_unchanged': True, 'authority_unchanged_by_reader': True, 'submission_unedited': True,
                'other_model_attested': False}
    (artifacts / 'observation.json').write_text(json.dumps(observed, indent=2) + '\n')
    return observed


def run_case(binary, case, host='codex-cli', live=None, skills=None):
    started = time.monotonic()
    runs, sessions, observations, claims = [], [], [], set()
    with tempfile.TemporaryDirectory(prefix='w4-run-') as directory:
        root = Path(directory)
        repository, authority = verify.prepare_repository(binary, root)
        try:
            install(repository)
            if skills:
                for host_root in verify.HOSTS.values():
                    shutil.copyfile(skills / 'aif-review.md', repository / host_root / 'aif-review/SKILL.md')
                    shutil.copyfile(skills / 'severity.md', repository / host_root / 'aif-review/references/SEVERITY.md')
            setup = case if case in ('semantic-regression', 'conflict', 'unrelated-target') else 'risk' if case.startswith('owner-') else 'ready'
            source, handoff, before = fixture(root, repository, setup)
            if live:
                handoff['require_separate_session'] = True
            if case == 'local-merge':
                handoff['mode'] = 'local_merge'
            if case == 'owner-approved':
                handoff['risk_approval'] = {'candidate_commit': handoff['candidate_commit'], 'target_commit': handoff['target']['commit'],
                                          'policy_digest': i.w1.digest(i.w1.encoded(handoff['policy'])), 'categories': ['migrations'],
                                          'reference': 'fixture-owner-decision', 'reason': 'Owner reviewed the named migration'}
            if case == 'missing-tool':
                handoff['integrated_checks'][0]['argv'] = ['/no/such/owned/fixture/tool']
            if case == 'source-stale':
                handoff['acceptance'][0]['report']['request_digest'] = 'sha256:' + '1' * 64
            if case == 'dirty-start':
                (source / 'owner.txt').write_text('Preserved dirty owner work\n')
                before = i.w1.snapshot(source, before['base_commit'])
            provider = None
            if case.startswith('draft-'):
                handoff['mode'] = 'gitlab_draft'
                handoff['publication'] = {'project': 'fixture-project', 'source_branch': 'feature', 'target_branch': 'main',
                                           'title': 'Draft: TRK-1 · Feature', 'body': 'Owned fixture integration', 'identity': 'fixture-one'}
                provider = FakeGitLab(handoff['target']['commit'], lose_ack=case == 'draft-lost-ack', duplicate=case == 'draft-format')
            file = root / 'handoff.json'
            file.write_bytes(i.w1.encoded(handoff) + b'\n')
            verify.run(binary, '--project', authority, 'project', 'local', 'set', '--repository', source,
                       '--allow-executable', 'python=' + str(Path(sys.executable).resolve()))
            args = ('--project', authority, 'project', 'start', '--repository', source, '--launch', 'verified-integration',
                    '--host', host, '--workspace', 'checkout', '--input', 'handoff=' + str(file), '--allow-execution')
            prepared = verify.run(binary, *args[:3], 'questionnaire', *args[4:], '--prepare')
            if case == 'dirty-start':
                refusal = verify.run(binary, *args, '--expected-launch-digest', prepared['review_digest'], expect_ok=False)
                assert 'checkout_dirty' in refusal
                assert i.w1.snapshot(source, before['base_commit']) == before
                assert not verify.run(binary, '--project', authority, 'run', 'list')['runs']
                return {'case': case, 'host': host, 'outcome': 'refused', 'status': 'checkout_dirty',
                        'source_preserved': True, 'runs': 0, 'claim_count': 0, 'provider': None, 'mr_creations': 0,
                        'assessment': None, 'live': [], 'elapsed_seconds': round(time.monotonic() - started, 3)}
            rid = verify.run(binary, *args, '--expected-launch-digest', prepared['review_digest'])['run']['run']['id']
            runs.append(rid)
            if case == 'dirty-source':
                (source / 'owner.txt').write_text('Preserved dirty owner work\n')
                before = i.w1.snapshot(source, before['base_commit'])

            def drive(rid, iteration=0):
                nonlocal before
                for _ in range(10):
                    verify.run(binary, '--project', authority, 'run', 'drive', rid)
                    tasks = verify.run(binary, '--project', authority, 'session', 'task', '--run', rid, '--all')['tasks']
                    if not tasks:
                        return verify.run(binary, '--project', authority, 'run', 'status', rid)['run']
                    for task in tasks:
                        claims.add(task['claim_id'])
                        assessment = read(task, 'assessment')
                        sessions.append(assessment)
                        name = task['skill_refs'][0]['id'].rsplit('/', 1)[-1]
                        if name == 'final-reader-bridge':
                            if case == 'cancel-resume' and iteration == 0:
                                verify.run(binary, '--project', authority, 'run', 'cancel', rid, '--reason', 'Fixture final reader cancelled')
                                verify.run(binary, '--project', authority, 'run', 'drive', rid)
                                assert i.release(assessment)['cleanup'] == 'released'
                                return verify.run(binary, '--project', authority, 'run', 'status', rid)['run']
                            if case == 'reader-no-report':
                                submit(binary, authority, rid, task, None, None, verdict='fail')
                            elif live:
                                observations.append(live_reader(binary, authority, rid, task, live))
                            else:
                                config, basis = read(task, 'request'), read(task, 'candidate')
                                value = report(config, basis, task['context']['inputs']['request']['ref']['digest'], failed=case == 'final-defect')
                                if case == 'missing-spot':
                                    value['checks'] = []
                                if case == 'reader-unavailable' or case == 'partial-resume' and iteration == 0:
                                    for check in value['checks']:
                                        check.update(status='unavailable', result='not_run', reason='Actual fixture tool unavailable', evidence=[])
                                if case == 'dirty-source':
                                    failure = submit(binary, authority, rid, task, 'report', value, expect_ok=False)
                                    assert 'effect_not_permitted' in failure
                                    verify.run(binary, '--project', authority, 'run', 'cancel', rid, '--reason', 'Owner edit during reader refused by Core; preserve work')
                                    verify.run(binary, '--project', authority, 'run', 'drive', rid)
                                    assert i.release(assessment)['cleanup'] == 'released'
                                    return verify.run(binary, '--project', authority, 'run', 'status', rid)['run']
                                submit(binary, authority, rid, task, 'report', value)
                            if case == 'moving-candidate':
                                (source / 'owner.txt').write_text('Preserved intervening owner edit\n')
                                before = i.w1.snapshot(source, before['base_commit'])
                            if case == 'moving-target':
                                i.git(Path(handoff['target']['repository']), 'fetch', '--no-tags', str(source), handoff['candidate_commit'])
                                i.git(Path(handoff['target']['repository']), 'update-ref', handoff['target']['ref'], handoff['candidate_commit'])
                        elif name == 'publication-bridge':
                            spec = publication_spec(handoff, assessment)
                            value = publication.publish(provider, spec)
                            if case == 'draft-repeat':
                                value = publication.publish(provider, spec)
                            if case in ('draft-unknown', 'draft-reentry'):
                                value.update(status='reconcile_required', url=None, reason='Provider acknowledgement/state unavailable')
                            if case == 'draft-no-receipt':
                                submit(binary, authority, rid, task, None, None, verdict='fail')
                            else:
                                submit(binary, authority, rid, task, 'receipt', value)
                        else:
                            raise AssertionError(name)
                raise AssertionError('W4 did not finish')

            state = drive(rid)
            if case == 'dirty-source':
                assert state['status'] == 'cancelled' and i.w1.snapshot(source, before['base_commit']) == before
                return {'case': case, 'host': host, 'outcome': 'cancelled', 'status': 'effect_not_permitted',
                        'source_preserved': True, 'runs': len(runs), 'claim_count': len(claims), 'provider': None,
                        'mr_creations': 0, 'assessment': None, 'live': [], 'named_refusal': 'effect_not_permitted',
                        'elapsed_seconds': round(time.monotonic() - started, 3)}
            if case in ('cancel-resume', 'partial-resume', 'draft-reentry'):
                assert state['status'] == 'cancelled' if case == 'cancel-resume' else state.get('outcome') == 'partial'
                continuation = ('--project', authority, 'project', 'continue', '--repository', source, '--launch', 'verified-integration',
                                '--source-run', rid, '--host', host, '--allow-execution')
                plan = verify.run(binary, *continuation, '--prepare')
                rid = verify.run(binary, *continuation, '--expected-launch-digest', plan['review_digest'])['run']['run']['id']
                runs.append(rid)
                state = drive(rid, 1)
            ref = state['output_artifacts']['assessment']
            reference = root / 'assessment-ref.json'
            reference.write_text(json.dumps(ref))
            exported = root / 'assessment.json'
            verify.run(binary, '--project', authority, 'artifact', 'export', '--ref', reference, '--output', exported)
            assessment = json.loads(exported.read_text())
            if live:
                (live / 'final-assessment.json').write_bytes(exported.read_bytes())
            expected = 'succeeded' if case in ('assess', 'local-merge', 'owner-approved', 'cancel-resume', 'partial-resume', 'draft-repeat', 'draft-lost-ack') else 'partial'
            assert state.get('outcome') == expected, {'status': state['status'], 'outcome': state.get('outcome'), 'assessment': assessment}
            assert i.w1.snapshot(source, before['base_commit']) == before
            assert (source / 'owner.txt').read_text() == ('Preserved dirty owner work\n' if case == 'dirty-source' else 'Preserved intervening owner edit\n' if case == 'moving-candidate' else 'Owner work remains intact\n')
            if case == 'local-merge':
                assert assessment['operation']['status'] == 'applied'
                assert i.target_head(handoff) == assessment['integration_head']
            elif case != 'moving-target':
                assert i.target_head(handoff) == handoff['target']['commit']
            if provider:
                assert provider.create_calls == 1
            if case == 'draft-reentry':
                assert len(runs) == 2 and assessment['status'] == 'reconcile_required'
                assert any('Previous owned integration session remains' in x for x in assessment['findings'])
                assert len(sessions) == 2, 'Retained unknown must not deliver a second reader/publisher'
            assert len(claims) <= 1
            return {'case': case, 'host': host, 'outcome': state['outcome'], 'status': assessment['status'],
                    'program_digest': i.w1.digest((source / '.prifly/workflows/verified-integration/files/integration.py').read_bytes()),
                    'source_preserved': True, 'runs': len(runs), 'claim_count': len(claims),
                    'provider': 'offline fixture only' if provider else None, 'mr_creations': provider.create_calls if provider else 0,
                    'assessment': assessment, 'live': observations, 'elapsed_seconds': round(time.monotonic() - started, 3)}
        finally:
            clean(binary, authority, runs)
            for assessment in sessions:
                info = assessment['session']
                if info and Path(info['path']).exists():
                    # Fixture provider state was inspected above. Only remove
                    # this exact fixture's owned clone, never another session.
                    shutil.rmtree(i.owned(assessment))
            assert not any(c['status'] == 'active' for c in verify.run(binary, '--project', authority, 'claim', 'list')['claims'])
            verify.forget_authority(authority)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--case', choices=CASES)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--live-artifacts', type=Path)
    parser.add_argument('--live-skills', type=Path)
    args = parser.parse_args()
    cases = [args.case] if args.case else ['assess'] if args.live_artifacts else CASES
    results = []
    for case in cases:
        value = run_case(args.binary, case, live=args.live_artifacts, skills=args.live_skills)
        results.append(value)
        print(json.dumps({'case': case, 'outcome': value['outcome'], 'status': value['status']}), flush=True)
    if not args.case and not args.live_artifacts:
        for host in ('codex-app', 'claude-code'):
            results.append(run_case(args.binary, 'assess', host))
    if args.report:
        args.report.write_text(json.dumps({'prifly': verify.run(args.binary, 'version')['version'],
                              'binary_sha256': hashlib.sha256(args.binary.read_bytes()).hexdigest(), 'cases': results}, indent=2) + '\n')


if __name__ == '__main__':
    main()
