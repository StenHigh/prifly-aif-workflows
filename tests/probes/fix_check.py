#!/usr/bin/env python3
"""Drive aif-fix through completion with a deterministic synthetic host.

Real Git trees, regression commands, native captures and released CLI; no LLM
or installed aif skills run. Model/session independence is reported unavailable.
Every stand, Run, claim and monitor entry created here is cleaned on exit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify
from run_check import clean, git_out

BAD = 'def total(value):\n    return (value or 0) - 1\n'
GOOD = 'def total(value):\n    return 0 if value is None else value\n'
INCOMPLETE = 'def total(value):\n    return value\n'
CASES = ('direct', 'install', 'security-off', 'extension', 'escalation', 'decision-wait', 'custom', 'blocked-plan', 'blocked-execution', 'repair-review', 'repair-check', 'repair-limit',
         'repair-security', 'blocked-chain', 'cancel-check', 'cancel-review',
         'blocked-fix', 'owner-review', 'foreign-plan', 'plan-stop',
         'effect-refusal', 'missing-output')


def command(tree, review=False):
    expression = 'from calc import total; assert total(None) == 0' if review else 'from calc import total; assert total(2) == 2'
    done = subprocess.run([sys.executable, '-B', '-c', expression], cwd=tree,
                          capture_output=True, text=True, timeout=20)
    return done.returncode, f'{expression}\nexit={done.returncode}\n{done.stdout}{done.stderr}'


def implementation(tree, base):
    paths = set(git_out(tree, '-c', 'core.quotepath=off', 'diff', '--name-only', base).splitlines())
    paths.update(git_out(tree, '-c', 'core.quotepath=off', 'ls-files', '--others', '--exclude-standard').splitlines())
    return {'base_commit': base, 'head_commit': git_out(tree, 'rev-parse', 'HEAD'), 'changed_files': sorted(paths)}


def value(task, port):
    return json.loads((Path(task['workspace']) / task['context']['inputs'][port]['path']).read_text())


def gate(kind, failed=False, owner=False, blocked=False, findings=None):
    return {'gate': kind, 'status': 'blocked' if blocked else 'failed' if failed else 'passed',
            'blocking': failed, 'blocking_owner_only': owner, 'findings': findings or [],
            'suggested_next': '/aif-fix' if failed and not owner else 'continue'}


def result(outcome, before, after='not yet checked', execute=False):
    return {'outcome': outcome, 'reason': f'fixture: {outcome}', 'work': ['Current tracked and untracked work preserved.'],
            'regression': {'check': 'python -B -c "from calc import total; assert total(2) == 2"',
                           'before': before, 'after': after}, 'execute_plan': execute}


class Host:
    def __init__(self, binary, authority, case, profile):
        self.binary, self.authority, self.case, self.profile = binary, authority, case, profile
        self.seen, self.runs, self.captures, self.generations = [], [], [], []
        self.base, self.tree, self.blocked = None, None, 0
        self.refusals = []
        self.claims = set()
        self.changed_checked = False

    def call(self, *args):
        return verify.run(self.binary, '--project', self.authority, *args)

    def submit(self, run_id, task, verdict, values, omit=False):
        template = self.call('session', 'submit', '--template', '--run', run_id, '--attempt', task['attempt_id'])
        for port, data in values.items():
            raw = json.dumps(data).encode()
            path = Path(task['workspace']) / task['context']['outputs'][port]['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            template['result']['outputs'][port]['digest'] = 'sha256:' + hashlib.sha256(raw).hexdigest()
        if omit:
            template['result']['outputs'].pop('implementation', None)
        template['result']['verdict'] = verdict
        template['result']['summary'] = f'Synthetic host {self.case}: {self.seen[-1]["step"]}'
        template['answered_questions'] = []
        if task.get('model_profile'):
            template['model_profile'] = {'outcome': 'unavailable', 'reason': 'Synthetic host; no model/session independence claimed.'}
        report = Path(task['workspace']) / 'submission.json'
        report.write_text(json.dumps(template))
        done = subprocess.run([str(self.binary), '--json', '--project', str(self.authority), 'session', 'submit', '--file', str(report)],
                              capture_output=True, text=True, timeout=120)
        if done.returncode:
            problem = json.loads((done.stderr or done.stdout).strip().splitlines()[-1])
            self.refusals.append(problem)
            return problem
        document = json.loads(done.stdout)
        assert not (document.get('receipt') or {}).get('rejection'), document
        return None

    def answer(self, task, step):
        tree = Path(task['repository_workspace']); self.tree = tree
        self.generations.append(task['claim_generation'])
        self.claims.add(task['claim_id'])
        if step == 'extension':
            assert not task['context']['inputs']
            return 'pass', {}
        if step == 'warmup':
            self.base = git_out(tree, 'rev-parse', 'HEAD')
            return 'pass', {'handoff': {'summary': 'Tiny arithmetic regression fixture.', 'entry_points': ['calc.py'],
                                      'conventions': ['Python standard library'], 'sources': ['calc.py']},
                            'implementation': implementation(tree, self.base)}
        current = value(task, 'implementation')
        assert current['base_commit'] == self.base
        if step == 'fix-task':
            before_rc, before = command(tree)
            if self.case == 'foreign-plan':
                return 'needs_revision', {'implementation': implementation(tree, self.base), 'result': result('owner_required', before)}
            if self.case == 'blocked-fix' and self.blocked == 0:
                self.blocked += 1
                return 'blocked', {'implementation': implementation(tree, self.base), 'result': result('environment_unavailable', before)}
            if self.case in ('escalation', 'decision-wait', 'custom', 'plan-stop', 'blocked-plan', 'blocked-execution'):
                assert before_rc != 0
                (tree / 'tracked.txt').write_text('partial work\n')
                (tree / 'untracked.txt').write_text('preserve this work\n')
                return 'needs_revision', {'implementation': implementation(tree, self.base), 'result': result('needs_planning', before)}
            assert before_rc != 0
            (tree / 'calc.py').write_text(INCOMPLETE if self.case == 'repair-review' else BAD if self.case in ('repair-check', 'repair-limit') else GOOD)
            if self.case == 'repair-security': (tree / 'security-canary.txt').write_text('unsafe\n')
            after_rc, after = command(tree)
            assert after_rc == 0 or self.case in ('repair-check', 'repair-limit')
            (tree / '.ai-factory/patches').mkdir(parents=True, exist_ok=True)
            (tree / '.ai-factory/patches/fixture.md').write_text('# Learning patch\nRoot cause: arithmetic offset.\n')
            return 'pass', {'implementation': implementation(tree, self.base), 'result': result('fixed', before, after)}
        prior = value(task, 'result') if step != 'aif-security' else None
        if step == 'fix-plan':
            memo = json.loads((Path(task['workspace']) / 'workspace-trees.json').read_text())
            path = tree / memo['ports'][0]['capture']['path']
            assert not path.exists()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('# Fix Plan: arithmetic bug\n\nPreserve tracked/untracked work and initial base.\n\n1. Reproduce regression.\n2. Fix total.\n3. Rerun the same check.\n')
            if self.profile == 'custom': git_out(tree, 'add', '--', str(path.relative_to(tree)))
            self.captures.append({'stage': 'create', 'digest': hashlib.sha256(path.read_bytes()).hexdigest()})
            if self.case == 'blocked-plan' and self.blocked == 0:
                self.blocked += 1
                path.write_text(path.read_text() + '\nINCOMPLETE: dependency unavailable; not executable.\n')
                return 'blocked', {'implementation': implementation(tree, self.base), 'result': {**prior, 'outcome': 'environment_unavailable'}}
            if self.case == 'decision-wait':
                assert 'fix_plan_execution' not in task['decision_context']
                saved = path.read_bytes()
                self.call('run', 'decision', task['run_id'], 'request', '--attempt', task['attempt_id'],
                          '--envelope-digest', task['envelope_digest'], '--decision', 'fix_plan_execution',
                          '--expected-run-version', str(task['run_version']), '--yield-execution')
                pending = self.call('run', 'decisions', task['run_id'])
                assert pending['pending']['attempt_id'] == task['attempt_id']
                assert not self.call('session', 'task', '--run', task['run_id'], '--all')['tasks']
                # This is the fixture owner's explicit answer, not inferred consent.
                self.call('run', 'decision', task['run_id'], 'answer', '--decision', 'fix_plan_execution',
                          '--request-digest', pending['pending_request_digest'],
                          '--expected-run-version', str(pending['run_version']), '--value', 'true')
                self.call('run', 'drive', task['run_id'])
                delivered = self.call('session', 'task', '--run', task['run_id'], '--all')['tasks'][0]
                assert delivered['attempt_id'] == task['attempt_id']
                assert delivered['envelope_digest'] != task['envelope_digest']
                assert path.read_bytes() == saved
                task.clear(); task.update(delivered)
            planned = {**prior, 'outcome': 'planned', 'execute_plan': task['decision_context']['fix_plan_execution']}
            return 'pass', {'implementation': implementation(tree, self.base), 'result': planned}
        if step == 'fix-from-plan':
            memo = json.loads((Path(task['workspace']) / 'workspace-trees.json').read_text())
            path = tree / memo['ports'][0]['capture']['path']
            assert '# Fix Plan: arithmetic bug' in path.read_text()
            assert (tree / 'tracked.txt').read_text() == 'partial work\n'
            assert (tree / 'untracked.txt').read_text() == 'preserve this work\n'
            self.captures.append({'stage': 'materialize', 'digest': hashlib.sha256(path.read_bytes()).hexdigest()})
            assert self.captures[-1]['digest'] == self.captures[-2]['digest']
            if self.case == 'blocked-execution' and self.blocked == 0:
                self.blocked += 1
                return 'blocked', {'implementation': implementation(tree, self.base), 'result': {**prior, 'outcome': 'environment_unavailable'}}
            (tree / 'calc.py').write_text(GOOD)
            rc, after = command(tree); assert rc == 0
            path.write_text(path.read_text() + '\nExecuted and checked.\n')
            return 'pass', {'implementation': implementation(tree, self.base), 'result': {**prior, 'outcome': 'fixed', 'regression': {**prior['regression'], 'after': after}}}
        if step == 'check-change':
            rc, observed = command(tree)
            if self.case == 'effect-refusal': (tree / 'calc.py').write_text(BAD)
            if self.case == 'blocked-chain' and self.blocked == 0:
                self.blocked += 1
                return 'blocked', {'gate': gate('verify', blocked=True, findings=['Fixture dependency unavailable; regression command left unrun.'])}
            if self.case == 'blocked-chain' and self.blocked == 1 and not self.changed_checked:
                assert rc != 0, 'resumed checker must see the changed tree, not the prior fixed result'
                self.changed_checked = True
            return 'pass', {'gate': gate('verify', failed=bool(rc), findings=[observed] if rc else [])}
        if step == 'aif-security':
            canary = tree / 'security-canary.txt'
            failed = canary.exists() and canary.read_text() != 'safe\n'
            return 'pass', {'gate': gate('security', failed=failed, findings=['security-canary.txt is unsafe'] if failed else [])}
        if step == 'review-task':
            if self.case == 'blocked-chain' and self.blocked == 1:
                self.blocked += 1
                return 'blocked', {'gate': gate('review', blocked=True, findings=['Fixture reviewer dependency unavailable.'])}
            if self.case == 'owner-review' and self.blocked == 0:
                self.blocked += 1
                return 'pass', {'gate': gate('review', failed=True, owner=True, findings=['Fixture owner decision needed.'])}
            rc, observed = command(tree, review=True)
            reviewed = gate('review', failed=bool(rc), findings=[observed] if rc else ['Reviewer independence unavailable in synthetic host.'])
            if not rc: reviewed['status'] = 'warnings'
            return 'pass', {'gate': reviewed}
        if step == 'repair':
            source = value(task, 'gate')
            assert source['blocking'] and not source['blocking_owner_only']
            rc, before = command(tree, review=source['gate'] == 'review')
            (tree / 'calc.py').write_text(GOOD)
            if (tree / 'security-canary.txt').exists(): (tree / 'security-canary.txt').write_text('safe\n')
            rc, after = command(tree, review=source['gate'] == 'review'); assert rc == 0
            return 'pass', {'implementation': implementation(tree, self.base), 'result': {**prior, 'outcome': 'fixed', 'regression': {'check': 'python -B -c "from calc import total; assert total(None) == 0"' if source['gate'] == 'review' else prior['regression']['check'], 'before': before, 'after': after}}}
        if step == 'commit':
            assert command(tree)[0] == command(tree, review=True)[0] == 0
            for relative in ('calc.py', 'tracked.txt', 'untracked.txt', 'security-canary.txt', '.ai-factory/patches/fixture.md'):
                if (tree / relative).exists(): git_out(tree, 'add', '--', relative)
            if self.profile == 'custom':
                assert 'fix_plan' in task['context']['inputs']
                git_out(tree, 'add', '--', '.ai-factory/fix-plans/FIX_PLAN.md')
            if git_out(tree, 'diff', '--cached', '--name-only'):
                git_out(tree, '-c', 'user.name=probe', '-c', 'user.email=probe@example.invalid', 'commit', '-q', '-m', 'Fix arithmetic regression')
            return 'pass', {'implementation': implementation(tree, self.base), 'result': prior}
        raise AssertionError(step)

    def drive(self, run_id, cancel=None):
        for _ in range(80):
            self.call('run', 'drive', run_id)
            tasks = self.call('session', 'task', '--run', run_id, '--all')['tasks']
            if not tasks: return self.call('run', 'status', run_id)['run']
            for task in tasks:
                bridge = task['skill_refs'][0]['id'].rsplit('/', 1)[-1]
                step = bridge.removesuffix('-bridge')
                self.seen.append({'run': run_id, 'step': step, 'head': git_out(task['repository_workspace'], 'rev-parse', 'HEAD')})
                if cancel == step:
                    self.tree = Path(task['repository_workspace'])
                    self.call('run', 'cancel', run_id, '--reason', 'fixture host cancelled')
                    self.call('run', 'drive', run_id)
                    return self.call('run', 'status', run_id)['run']
                verdict, values = self.answer(task, step)
                refused = self.submit(run_id, task, verdict, values, omit=self.case == 'missing-output' and step == 'fix-task')
                if refused:
                    if self.case in ('effect-refusal', 'missing-output'):
                        if self.case == 'effect-refusal': Path(task['repository_workspace'], 'calc.py').write_text(GOOD)
                        accepted = self.submit(run_id, task, verdict, values)
                        assert not accepted, accepted
                        return self.call('run', 'status', run_id)['run']
                    raise AssertionError(refused)
        raise AssertionError('Run did not settle within bounded probe turns')

    def snapshot(self):
        return (git_out(self.tree, 'rev-parse', 'HEAD'), git_out(self.tree, 'diff', '--binary', self.base),
                {p: (self.tree / p).read_bytes() for p in git_out(self.tree, 'ls-files', '--others', '--exclude-standard').splitlines()})

    def resume(self, repository, source, host):
        arguments = ('project', 'continue', '--repository', repository, '--launch', 'aif-fix', '--source-run', source, '--host', host)
        before = self.snapshot(); source_state = self.call('run', 'status', source)
        prepared = self.call(*arguments, '--prepare')
        assert self.snapshot() == before
        assert self.call('run', 'status', source)['run_version'] == source_state['run_version']
        started = self.call(*arguments, '--expected-launch-digest', prepared['review_digest'])
        resumed = started['run']['run']['id']; self.runs.append(resumed)
        assert self.snapshot() == before
        state = self.call('run', 'status', resumed)['run']
        assert state['fork']['source_run_id'] == source
        assert 'warmup' in {record.get('stage_id') for record in state['recovery']['reused']}
        return resumed


def run_case(binary, case, host='codex-cli'):
    with tempfile.TemporaryDirectory(prefix='aif-fix-probe-') as temporary:
        root = Path(temporary); repository, authority = verify.prepare_repository(binary, root)
        probe = Host(binary, authority, case, 'custom' if case == 'custom' else 'default')
        try:
            (repository / 'calc.py').write_text(BAD); (repository / 'tracked.txt').write_text('original\n')
            package = repository / '.prifly/workflows/aif-fix'
            if case == 'install':
                source = root / 'workflow-source'
                source.mkdir()
                shutil.copytree(package, source / 'aif-fix')
                catalog = (verify.ROOT / 'catalog/aif-fix.yaml').read_text().replace('https://github.com/StenHigh/prifly-aif-workflows.git', source.as_uri()).replace('ref: v1.51.0', 'ref: main')
                (source / 'catalog.yaml').write_text(catalog)
                verify.git('-C', source, 'init', '-q', '-b', 'main')
                verify.git('-C', source, 'add', '-A')
                verify.git('-C', source, 'commit', '-q', '-m', 'Publish fixture package')
                probe.call('project', 'workflows', 'remove', 'aif-fix', '--repository', repository)
                discovered = probe.call('project', 'workflows', 'search', '--catalog', source.as_uri())
                assert 'aif-fix' in json.dumps(discovered)
                probe.call('project', 'workflows', 'add', 'aif-fix', '--catalog', source.as_uri(), '--repository', repository)
                launches = probe.call('project', 'workflows', '--repository', repository)['launches']
                fix = next(launch for launch in launches if launch['id'] == 'aif-fix')
                assert 'bug' in fix['description'] and 'fix-plan' in fix['description']
            if case == 'repair-limit':
                (package / 'extend.yaml').write_text('profile: default\nsettings: {quality: {repair_round_limit: 1}}\nexclude: []\nextensions: []\n')
            if case == 'security-off':
                (package / 'extend.yaml').write_text('profile: default\nexclude: [security]\nextensions: []\n')
            if case == 'extension':
                (package / 'contexts/extension-bridge.yaml').write_text('id: probe:context/extension-bridge\nversion: 1.0.0\nmedia_type: text/plain\ntext: Generic read-only extension fixture.\n')
                (package / 'steps/extension.yaml').write_text('''authoring: prifly-step/2
id: probe:step/extension
version: 1.0.0
title: Generic project extension
kind: worker
executor: {adapter_ref: "{{assisted_adapter}}", operation: session}
instructions_ref: "{{context_extension-bridge}}"
effects: {class: none, retry_class: pure}
repository_workspace: read_only
session_limits: {active_timeout_ms: null}
result_schema_ref: "{{step_result_schema_v2}}"
''')
                (package / 'extend.yaml').write_text('''profile: default
extensions:
  - id: generic
    workflow: fix
    step: extension
    between: {from: commit, to: done}
    on: {pass: done, needs_revision: abandoned, blocked: abandoned, fail: abandoned, no_work: abandoned}
''')
            if case in ('direct', 'foreign-plan'):
                (repository / '.ai-factory').mkdir(exist_ok=True)
                (repository / '.ai-factory/PLAN.md').write_text('Other task ordinary plan\n')
                (repository / '.ai-factory/FIX_PLAN.md').write_text('Other task fix plan\n')
            verify.git('-C', repository, 'add', '-A'); verify.git('-C', repository, 'commit', '-q', '-m', 'Bug fixture')
            task = root / 'task.json'; task.write_text(json.dumps({'title': 'Fix arithmetic offset', 'description': 'total(2) should be 2, not 1; None means zero.'}))
            q = probe.call('project', 'questionnaire', '--repository', repository, '--launch', 'aif-fix', '--package-profile', probe.profile)
            runtime_answers = () if case == 'decision-wait' else ('--runtime-answer', 'fix_plan_execution=' + ('false' if case == 'plan-stop' else 'true'))
            started = probe.call('project', 'start', '--repository', repository, '--launch', 'aif-fix', '--host', host,
                                 '--workspace', 'worktree', '--package-profile', probe.profile, '--input', f'task={task}',
                                 '--preflight-answer', 'short_checks=""', '--preflight-answer', 'gate_warnings="ignore"',
                                 *runtime_answers,
                                 '--expected-decision-catalog-digest', q['catalog_digest'])
            run_id = started['run']['run']['id']; probe.runs.append(run_id)
            cancel = 'check-change' if case == 'cancel-check' else 'review-task' if case == 'cancel-review' else None
            state = probe.drive(run_id, cancel)
            if case in ('blocked-chain', 'cancel-check', 'cancel-review', 'blocked-fix', 'blocked-plan', 'blocked-execution', 'owner-review'):
                assert state['status'] == 'cancelled' if cancel else state['outcome'] == 'partial', state
                if case == 'blocked-chain': (probe.tree / 'calc.py').write_text(BAD)
                resumed = probe.resume(repository, run_id, host); state = probe.drive(resumed)
                if case == 'blocked-chain':
                    assert state['outcome'] == 'partial'
                    state = probe.drive(probe.resume(repository, resumed, host))
                assert len(set(probe.generations)) >= 2
            if case == 'repair-limit':
                assert state['outcome'] == 'partial'
                assert [entry['step'] for entry in probe.seen] == ['warmup', 'fix-task', 'check-change', 'repair']
                assert 'gate' in state['output_artifacts'] and command(probe.tree)[0] == 0
            elif case in ('foreign-plan', 'plan-stop'):
                assert state['outcome'] == 'partial'
                assert 'gate' not in state['output_artifacts']
            elif case in ('effect-refusal', 'missing-output'):
                assert probe.refusals
                expected = 'effect_not_permitted' if case == 'effect-refusal' else 'output'
                assert expected in json.dumps(probe.refusals), probe.refusals
            else:
                assert (state['status'], state['outcome']) == ('completed', 'succeeded'), state
                assert 'implementation' in state['output_artifacts']
                assert probe.seen[-1]['step'] == ('extension' if case == 'extension' else 'commit')
                final_bytes = json.dumps(implementation(probe.tree, probe.base)).encode()
                assert state['output_artifacts']['implementation']['digest'] == 'sha256:' + hashlib.sha256(final_bytes).hexdigest()
                if case not in ('escalation', 'decision-wait', 'custom', 'blocked-plan', 'blocked-execution'):
                    assert 'fix_plan' not in state['output_artifacts'], state['output_artifacts']
            assert len(probe.claims) == 1, 'resume must transfer the original claim, not make a different workspace'
            if case == 'security-off': assert 'aif-security' not in [entry['step'] for entry in probe.seen]
            if (case.startswith('repair') and case != 'repair-limit') or case == 'blocked-chain':
                steps = [entry['step'] for entry in probe.seen]
                position = steps.index('repair')
                assert steps[position + 1:position + 4] == ['check-change', 'aif-security', 'review-task'], steps
            if case in ('direct', 'foreign-plan'):
                assert (probe.tree / '.ai-factory/PLAN.md').read_text() == 'Other task ordinary plan\n'
                assert (probe.tree / '.ai-factory/FIX_PLAN.md').read_text() == 'Other task fix plan\n'
                assert 'fix-plan' not in [entry['step'] for entry in probe.seen]
            if case in ('escalation', 'decision-wait', 'custom', 'plan-stop', 'blocked-plan', 'blocked-execution'):
                assert 'fix_plan' in state['output_artifacts']
                assert (probe.tree / 'tracked.txt').read_text() == 'partial work\n'
                assert (probe.tree / 'untracked.txt').read_text() == 'preserve this work\n'
                path = probe.tree / ('.ai-factory/fix-plans/FIX_PLAN.md' if case == 'custom' else '.ai-factory/FIX_PLAN.md')
                assert path.exists() == (case == 'custom')
                if case not in ('plan-stop', 'blocked-plan', 'blocked-execution'): assert [p['stage'] for p in probe.captures] == ['create', 'materialize']
            return {'case': case, 'host': host, 'outcome': state.get('outcome'), 'status': state['status'],
                    'steps': [entry['step'] for entry in probe.seen], 'runs': len(probe.runs),
                    'claim_generations': sorted(set(probe.generations)), 'captures': probe.captures,
                    'refusals': [{'code': p['code'], 'message': p['message']} for p in probe.refusals]}
        finally:
            clean(binary, authority, probe.runs)
            # A failed probe may leave a workspace-write delivery uncertain.
            # Its only worker was this synchronous fixture; all local operations
            # have returned and no external effect was possible.
            for owned_run in probe.runs:
                stopped = probe.call('run', 'status', owned_run)['run']
                for attempt_id, attempt in stopped['attempts'].items():
                    if attempt['status'] == 'uncertain':
                        probe.call('run', 'resolve', owned_run, '--attempt', attempt_id,
                                   '--outcome', 'applied', '--reason',
                                   'Synchronous synthetic host stopped; all fixture-local operations returned, no external effects.')
            clean(binary, authority, probe.runs)
            assert not any(claim['status'] == 'active' for claim in probe.call('claim', 'list')['claims']), 'probe left an active claim'
            assert verify.forget_authority(authority) == 1


def main():
    if not __debug__: raise RuntimeError('Verification requires Python assertions')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True, type=Path)
    parser.add_argument('--case', choices=CASES)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(); binary = args.binary.resolve(strict=True)
    reports = []
    for case in (args.case,) if args.case else CASES:
        reports.append(run_case(binary, case))
        print(json.dumps(reports[-1], ensure_ascii=False), flush=True)
    if not args.case:
        for host in ('codex-app', 'claude-code'):
            reports.append(run_case(binary, 'direct', host))
            print(json.dumps(reports[-1], ensure_ascii=False), flush=True)
    document = {'outcome': 'passed', 'prifly': verify.run(binary, 'version')['version'],
                'binary_sha256': 'sha256:' + hashlib.sha256(binary.read_bytes()).hexdigest(),
                'boundary': 'Synthetic host, real runtime/Git/captures; no LLM or independent reviewer session claimed.', 'cases': reports}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True); args.report.write_text(json.dumps(document, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'outcome': 'passed', 'cases': len(reports), 'prifly': document['prifly']}))


if __name__ == '__main__': main()
