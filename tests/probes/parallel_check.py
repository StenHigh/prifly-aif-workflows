#!/usr/bin/env python3
"""W5 released-runtime probes. Synthetic reader reports are never live evidence."""
import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify
from parallel_fixture import install
from evidence_check import read
from run_check import clean, git_out
from test_review_evidence import config, report, evidence

CASES = ('pass', 'failed', 'blocked', 'owner', 'failed-blocked', 'failed-owner', 'missing',
         'duplicate', 'stale-round', 'stale-request', 'malformed', 'missing-output',
         'intervening-edit', 'during-reader-edit', 'cancel-after-first', 'defect-repair', 'partial-resume', 'cancel-resume', 'crash', 'one-crash', 'unhandled-crash', 'outer-handler-crash')
KEEP = False


def invoke(binary, authority, *args):
    result = subprocess.run([str(binary), '--json', '--project', str(authority), *map(str, args)],
                            capture_output=True, text=True, timeout=120)
    document = json.loads(result.stdout or result.stderr)
    rejection = (document.get('receipt') or {}).get('rejection')
    return {'exit': result.returncode, 'document': document, 'rejection': rejection}


def submission(call, rid, task, value):
    template = call('session', 'submit', '--template', '--run', rid, '--attempt', task['attempt_id'])
    raw = json.dumps(value).encode()
    path = Path(task['workspace']) / task['context']['outputs']['report']['path']
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    template['result']['outputs']['report']['digest'] = evidence.digest(raw)
    template['result'].update(verdict='pass', summary='Synthetic W5 reader; no actual session/model asserted.')
    template['answered_questions'] = []
    template['model_profile'] = {'outcome': 'unavailable', 'reason': 'Synthetic qualification host.'}
    path = Path(task['workspace']) / 'submission.json'
    path.write_text(json.dumps(template))
    return path


def export(call, root, ref, name):
    ref_path, output = root / (name + '-ref.json'), root / (name + '.json')
    ref_path.write_text(json.dumps(ref))
    call('artifact', 'export', '--ref', ref_path, '--output', output)
    assert evidence.digest(output.read_bytes()) == ref['digest']
    return json.loads(output.read_text())


def aggregate(call, root, state):
    """Read exact sealed refs after native join, outside any worker/repair.

    Native manifest carries references, not report bytes. This test controller
    uses the public read API; it is not an automatic feature aggregation step.
    """
    manifest = export(call, root, state['output_artifacts']['results'], 'manifest')
    rows = manifest['branches']
    assert [r['id'] for r in rows] == ['first', 'second']
    gates, reports = {}, {}
    for row in rows:
        assert row['status'] == 'completed'
        gates[row['id']] = export(call, root, row['output_refs']['gate'], row['id'] + '-gate')
        reports[row['id']] = export(call, root, row['output_refs']['report'], row['id'] + '-report')
    # Keep each reader/check/evidence intact, including duplicated observations.
    findings = [{'reader': name, 'check': c['id'], 'report_digest': rows[n]['output_refs']['report']['digest'],
                 'result': c['result'], 'reason': c['reason'], 'evidence': c['evidence']}
                for n, (name, item) in enumerate(reports.items()) for c in item['checks']]
    status = ('blocked' if any(g['status'] == 'blocked' for g in gates.values()) else
              'owner' if any(g['blocking_owner_only'] for g in gates.values()) else
              'failed' if any(g['blocking'] for g in gates.values()) else 'accepted')
    return {'decision': status, 'join_result': manifest['join_result'], 'gates': gates,
            'findings': findings, 'duplicate_observations_counted_as_extra_checks': False}


class Fixture:
    def __init__(self, binary, root, case, host='codex-cli', parallelism=2, skills=None):
        self.binary, self.root, self.case, self.host = binary, root, case, host
        self.repo, self.authority = verify.prepare_repository(binary, root)
        self.runs = []
        self.expected_unsettled = False
        self.package = install(self.repo, parallelism=parallelism, handle_errors=case != 'unhandled-crash',
                               timeout=30000 if case.endswith('crash') else None, asymmetric=case == 'one-crash',
                               wrap_errors=case != 'outer-handler-crash')
        if skills:
            for host_root in verify.HOSTS.values():
                for name, source in (('aif-review/SKILL.md', 'aif-review.md'), ('aif-review/references/SEVERITY.md', 'severity.md')):
                    import shutil
                    shutil.copyfile(skills / source, self.repo / host_root / name)
        (self.repo / 'calc.py').write_text('def total(values):\n    return sum(values)' + (' + 1' if case == 'defect-repair' else '') + '\n')
        (self.repo / 'owner.txt').write_text('Preserve candidate and unrelated owner work.\n')
        verify.git('-C', self.repo, 'add', '.')
        verify.git('-C', self.repo, 'commit', '-qm', 'W5 bounded read-only implementation review')
        self.base = git_out(self.repo, 'rev-parse', 'HEAD')
        self.configuration = config(self.base, method='code', optional_policy='stop' if case in ('owner', 'failed-owner') else 'ignore',
                                    require_separate_session=bool(skills))
        self.configuration['checks'][0]['description'] = 'Inspect calc.py: total must return the sum of numeric values, including zero for an empty list. Report code evidence at the function and relevant lines.'
        request = root / 'request.json'
        request.write_text(json.dumps(self.configuration))
        self.call('project', 'local', 'set', '--repository', self.repo,
                  '--allow-executable', 'python=' + str(Path(sys.executable).resolve()))
        args = ('project', 'start', '--repository', self.repo, '--launch', 'parallel-review', '--host', host,
                '--workspace', 'worktree', '--input', 'request=' + str(request), '--allow-execution')
        prepared = self.call(args[0], 'questionnaire', *args[2:], '--prepare')
        started = self.call(*args, '--expected-launch-digest', prepared['review_digest'])
        self.rid = started['run']['run']['id']; self.runs.append(self.rid)

    def call(self, *args, **kw):
        return verify.run(self.binary, '--project', self.authority, *args, **kw)

    def tasks(self, rid=None):
        return self.call('session', 'task', '--run', rid or self.rid, '--all')['tasks']

    def state(self, rid=None):
        return self.call('run', 'status', rid or self.rid)

    def drive(self, rid=None):
        return self.call('run', 'drive', rid or self.rid)

    def submit(self, task, value, rid=None):
        path = submission(self.call, rid or self.rid, task, value)
        self.call('session', 'submit', '--file', path)
        return path

    def continuation(self, source):
        return ('project', 'continue', '--repository', self.repo, '--launch', 'parallel-review', '--host', self.host,
                '--source-run', source, '--allow-execution')

    def resume(self, source):
        args = self.continuation(source)
        prepared = self.call(*args, '--prepare')
        result = self.call(*args, '--expected-launch-digest', prepared['review_digest'])
        rid = result['run']['run']['id']; self.runs.append(rid)
        return rid

    def close(self):
        try:
            if not self.expected_unsettled:
                clean(self.binary, self.authority, self.runs)
                assert not any(c['status'] == 'active' for c in self.call('claim', 'list')['claims'])
            # For a named cancellation negative the authority cannot settle its
            # claim. No actor/process remains; default TemporaryDirectory tears
            # down this entire owned sandbox, NOT a successful native release.
            # --keep preserves it for inspection instead. Never clear flags or
            # reset the source to manufacture native cleanup/recovery success.
        finally:
            verify.forget_authority(self.authority)
            if KEEP: print(json.dumps({'kept_owned_fixture': str(self.root), 'native_unsettled': self.expected_unsettled}), flush=True)


def check(binary, case='pass', host='codex-cli'):
    context = nullcontext(tempfile.mkdtemp(prefix='w5-native-')) if KEEP else tempfile.TemporaryDirectory(prefix='w5-native-')
    with context as directory:
        root = Path(directory)
        fixture = Fixture(binary, root, case, host)
        f = fixture
        try:
            f.drive(); tasks = f.tasks()
            assert len(tasks) == 2, ('Must deliver two independent Attempts', len(tasks))
            assert len({t['attempt_id'] for t in tasks}) == len({t['workspace'] for t in tasks}) == 2
            assert len({t['claim_id'] for t in tasks}) == 1
            before = read(tasks[0], 'candidate')
            assert before == read(tasks[1], 'candidate')
            assert read(tasks[0], 'request') == read(tasks[1], 'request')
            tree = Path(tasks[0]['repository_workspace'])
            result = {'case': case, 'host': host, 'common_candidate': True, 'distinct_attempt_workspaces': True}
            # Late submissions are prepared while the original delivery is valid.
            late = submission(f.call, f.rid, tasks[1], report(read(tasks[1], 'request'), before))
            if case == 'one-crash':
                steps = f.state()['run']['steps']
                live_task = next(t for t in tasks if steps[t['step_instance_id']]['definition_ref']['id'] == 'w5:step/review2')
                expired_task = next(t for t in tasks if t != live_task)
                late = submission(f.call, f.rid, expired_task, report(read(expired_task, 'request'), before))
                sibling = submission(f.call, f.rid, live_task, report(read(live_task, 'request'), before))
            if case.endswith('crash'):
                time.sleep(31)
                f.drive()
                state = f.state()
                if case == 'one-crash':
                    assert state['run']['status'] == 'running' and state['run'].get('outcome') is None
                    assert [t['attempt_id'] for t in f.tasks()] == [live_task['attempt_id']]
                    f.call('session', 'submit', '--file', sibling)
                    f.drive()
                    state = f.state()
                    result.update(waited_for_live_sibling_after_crash=True, sibling_report_accepted=True)
                codes = [d['code'] for d in state['run']['diagnostics']]
                assert 'attempt_deadline_expired' in codes, codes
                assert all(a.get('settled') for a in state['run']['attempts'].values())
                version, snapshot = state['run_version'], evidence.snapshot(tree, f.base)
                late_result = invoke(binary, f.authority, 'session', 'submit', '--file', late)
                assert late_result['exit'] or late_result['rejection'], late_result
                if case in ('crash', 'one-crash'):
                    assert state['run']['status'] == 'completed' and state['run']['outcome'] == 'rejected', state['run']['status']
                    # Same sealed workflow, no timeout removal or state edits.
                    child = f.resume(f.rid); f.drive(child)
                    replay = f.tasks(child)
                    assert len(replay) == 2
                    for task in replay: f.submit(task, report(read(task, 'request'), read(task, 'candidate')), child)
                    f.drive(child)
                    final = f.state(child)['run']
                    assert final['outcome'] == 'succeeded', final.get('diagnostics')
                    assert f.state()['run_version'] == version and evidence.snapshot(tree, f.base) == snapshot
                    result.update(outcome='rejected', replay_outcome='succeeded', diagnostics=codes,
                                  error_handlers_declared=True, late_result=late_result,
                                  all_readers_replayed=True, candidate_preserved=True)
                    return result
                if case == 'outer-handler-crash':
                    assert state['run']['status'] == 'completed' and state['run']['outcome'] == 'rejected'
                else:
                    assert state['run']['status'] == 'failed' and state['run'].get('outcome') is None
                refused = invoke(binary, f.authority, *f.continuation(f.rid), '--prepare')
                expected = 'resume_frontier_ambiguous' if case == 'outer-handler-crash' else 'recover_frontier_unsupported'
                assert refused['exit'] and refused['document']['code'] == expected, refused
                assert f.state()['run_version'] == version and evidence.snapshot(tree, f.base) == snapshot
                # Also inspect the existing in-place reopen alternative.
                reopen = invoke(binary, f.authority, 'run', 'reopen', f.rid, '--expected-version', version,
                                '--reason', 'Owned read-only qualification: inspect supported recovery frontier')
                result.update(outcome=state['run'].get('outcome') or state['run']['status'], qualification='named negative; NOT successful crash recovery',
                              diagnostics=codes, continue_refusal=refused, late_result=late_result, reopen=reopen,
                              error_handlers_declared=case == 'outer-handler-crash', candidate_preserved=True)
                return result
            first = report(read(tasks[0], 'request'), before, result='failed' if case in ('failed', 'failed-blocked', 'failed-owner', 'defect-repair') else 'passed')
            if case == 'missing': first['checks'] = []
            if case == 'duplicate': first['checks'] *= 2
            if case == 'stale-round': first['round'] += 1
            if case == 'stale-request': first['request_digest'] = 'sha256:' + 'a' * 64
            if case == 'partial-resume': first = report(read(tasks[0], 'request'), before, 'unavailable', 'not_run')
            if case in ('malformed', 'missing-output'):
                path = submission(f.call, f.rid, tasks[0], {} if case == 'malformed' else first)
                if case == 'missing-output':
                    value = json.loads(path.read_text()); value['result']['outputs'] = {}; path.write_text(json.dumps(value))
                version = f.state()['run_version']
                refused = invoke(binary, f.authority, 'session', 'submit', '--file', path)
                assert refused['exit'] or refused['rejection'], refused
                assert f.state()['run_version'] == version
                assert len(f.tasks()) == 2
                result['invalid_report_refusal'] = refused
                # The synthetic actor makes a new valid report after a refused
                # protocol submission. No actual reader's bytes are rewritten.
            if case == 'cancel-resume':
                f.call('run', 'cancel', f.rid, '--reason', 'Owned read-only actors stopped before reporting')
                f.drive()
                assert f.state()['run']['status'] == 'cancelled'
                refused = invoke(binary, f.authority, 'session', 'submit', '--file', late)
                assert refused['exit'] or refused['rejection'], refused
                result['late_result'] = refused
            else:
                f.submit(tasks[0], first); f.drive()
                waiting = f.state()['run']
                assert waiting['status'] not in ('completed', 'failed', 'cancelled'), waiting['status']
                remaining = f.tasks()
                assert [t['attempt_id'] for t in remaining] == [tasks[1]['attempt_id']]
                second = report(read(tasks[1], 'request'), before)
                if case in ('blocked', 'failed-blocked'): second = report(read(tasks[1], 'request'), before, 'unavailable', 'not_run')
                if case in ('during-reader-edit', 'cancel-after-first'):
                    if case == 'during-reader-edit':
                        (tree / 'owner.txt').write_text('Owner edit while the last reader was active; preserve it.\n')
                        path = submission(f.call, f.rid, tasks[1], second)
                        refused = invoke(binary, f.authority, 'session', 'submit', '--file', path)
                        assert refused['document']['code'] == 'effect_not_permitted', refused
                        result['intervening_edit_refusal'] = refused
                    snapshot = evidence.snapshot(tree, f.base)
                    f.call('run', 'cancel', f.rid, '--reason', 'One synthetic reader settled; remaining read-only actor returned without an accepted report')
                    driven = invoke(binary, f.authority, 'run', 'drive', f.rid)
                    state = f.state()
                    assert driven['exit'] and driven['document']['code'] == 'invalid_input', driven
                    assert state['run']['status'] == 'stopping' and state['run']['cancel_requested']
                    assert all(a.get('settled') for a in state['run']['attempts'].values())
                    claims = f.call('claim', 'list')['claims']
                    releases = [invoke(binary, f.authority, 'claim', 'release', '--id', c['id'], '--generation', c['generation']) for c in claims if c['status'] == 'active']
                    assert releases and all(r['document']['code'] == 'claim_run_active' for r in releases)
                    version = f.state()['run_version']
                    continued = invoke(binary, f.authority, *f.continuation(f.rid), '--prepare')
                    assert continued['exit'] and continued['document']['code'] == 'recover_source_ineligible'
                    assert f.state()['run_version'] == version and evidence.snapshot(tree, f.base) == snapshot
                    repeated = invoke(binary, f.authority, 'run', 'drive', f.rid)
                    assert repeated['document']['code'] == 'invalid_input' and evidence.snapshot(tree, f.base) == snapshot
                    result.update(cancel_drive=driven, cancelled_state={
                        'status': state['run']['status'], 'cancel_requested': True, 'outcome': state['run'].get('outcome'),
                        'all_attempts_settled': True, 'source_run_id': f.rid, 'run_version': state['run_version'],
                        'raw_state_digest': evidence.digest(evidence.encoded(state)),
                        'attempt_statuses': [a['status'] for a in state['run']['attempts'].values()]},
                        claim_release=releases, continue_result=continued, repeated_drive=repeated,
                        candidate_preserved=True, qualification='named negative; production promotion blocked',
                        native_claim_release='refused; whole owned test sandbox removed by default, not a native release success')
                    f.expected_unsettled = True
                    return result
                else:
                    f.submit(tasks[1], second)
                if case == 'intervening-edit': (tree / 'owner.txt').write_text('Owner edit after both reports; preserve it.\n')
                if case != 'during-reader-edit':
                    f.drive()
                    state = f.state()['run']
                    assessment = aggregate(f.call, root, state)
                    expected = ('blocked' if case in ('blocked', 'failed-blocked', 'missing', 'duplicate', 'stale-round', 'stale-request', 'intervening-edit', 'partial-resume') else
                                'owner' if case in ('owner', 'failed-owner') else 'failed' if case in ('failed', 'defect-repair') else 'accepted')
                    assert assessment['decision'] == expected, assessment
                    assert state['outcome'] == ('succeeded' if expected == 'accepted' else 'partial')
                    result.update(outcome=state['outcome'], waited_for_last_reader=True, assessment=assessment)
            if case in ('partial-resume', 'cancel-resume', 'during-reader-edit', 'defect-repair'):
                version = f.state()['run_version']
                (tree / 'owner.txt').write_text('Preserved owner edit before reviewed full-round replay.\n')
                if case == 'defect-repair':
                    assert not f.tasks(), 'Never repair while a reader is outstanding'
                    (tree / 'calc.py').write_text('def total(values):\n    return sum(values)\n')
                    actual = subprocess.run([sys.executable, '-B', '-c', 'from calc import total; assert total([]) == 0; assert total([1,2]) == 3'], cwd=tree, capture_output=True)
                    assert actual.returncode == 0
                    result['repair_boundary'] = 'Separate owner action only after terminal join, followed by two fresh readers; not an automatic writer'
                child = f.resume(f.rid); f.drive(child)
                replay = f.tasks(child)
                assert len(replay) == 2
                assert not {t['attempt_id'] for t in tasks} & {t['attempt_id'] for t in replay}
                current = read(replay[0], 'candidate')
                assert current != before and current == read(replay[1], 'candidate')
                assert {t['claim_id'] for t in tasks + replay} == {tasks[0]['claim_id']}
                for task in replay: f.submit(task, report(read(task, 'request'), current), child)
                f.drive(child)
                final = f.state(child)['run']
                assert final['outcome'] == 'succeeded'
                assert f.state()['run_version'] == version
                assert (tree / 'owner.txt').read_text() == 'Preserved owner edit before reviewed full-round replay.\n'
                result.update(replay_outcome=final['outcome'], all_readers_replayed=True, owner_work_preserved=True,
                              root_frontier='quality call; recaptures candidate before both readers')
            return result
        finally:
            f.close()


def main():
    global KEEP
    if not __debug__: raise RuntimeError('Qualification requires enabled Python assertions')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', required=True, type=Path)
    p.add_argument('--case', choices=CASES)
    p.add_argument('--report', type=Path)
    p.add_argument('--keep', action='store_true', help='Single case only: retain owned fixture for native read-only inspection; monitor entry removed')
    args = p.parse_args(); results = []
    if args.keep and not args.case: p.error('--keep requires one --case')
    KEEP = args.keep
    cases = [(case, 'codex-cli') for case in ([args.case] if args.case else CASES)]
    if not args.case: cases += [('pass', host) for host in ('codex-app', 'claude-code')]
    summary = {'prifly': verify.run(args.binary, 'version')['version'],
               'binary_sha256': hashlib.sha256(args.binary.read_bytes()).hexdigest(),
               'boundary': 'Synthetic reader reports; actual released runtime, Git, W1 evaluators and public artifact exports. Named negatives are not successful recovery or native claim release. No live host overlap claim.',
               'cases': results, 'matrix_complete': False}
    for case, host in cases:
        result = check(args.binary, case, host); results.append(result)
        if args.report: args.report.write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps({k: v for k, v in result.items() if k not in ('assessment', 'reopen', 'continue_refusal', 'late_result', 'cancelled_state', 'claim_release', 'continue_result', 'repeated_drive')}), flush=True)
    if args.report:
        summary['matrix_complete'] = True
        args.report.write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__': main()
