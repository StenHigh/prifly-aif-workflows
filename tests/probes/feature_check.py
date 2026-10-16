#!/usr/bin/env python3
"""W3 complete released-runtime Runs: synthetic writers/readers, real Git/programs."""
import argparse
import copy
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
from test_review_evidence import config, report
from test_product_review import configuration as product_configuration
from evidence_check import read
from run_check import clean, git_out
from fix_check import Host, implementation
from product_environment import OwnedEnvironment
from product_check import live_reader
sys.path.insert(0, str(verify.ROOT / 'aif-feature/files'))
import parallel_host

CASES = ('backend', 'frontend', 'repair-checks', 'repair-security', 'repair-review', 'repair-ui', 'repair-ux',
         'required-unavailable', 'owner-stop', 'exhaustion', 'max-budget', 'too-large', 'requirement-conflict',
         'repair-too-large', 'retained-plan', 'foreign-plan', 'foreign-fix-plan', 'configured-plan',
         'blocked-resume', 'cancel-resume', 'chained-resume', 'plan-cancel', 'implement-cancel',
         'stale-after-review', 'stale-before-commit', 'upgrade', 'upgrade-refusal', 'excluded-security',
         'verdict-independent', 'commit-diagnostic', 'frontend-unavailable', 'frontend-cancel','commit-resume')


def task_input(frontend=False):
    value = {'title': 'Small greeting feature', 'description': 'Add a greeting(name) function returning Hello, <name>! with a test.',
             'scope': ['greeting.py', 'test_greeting.py'], 'assumptions': ['Name is a nonempty string; no new dependency.'],
             'optional_policy': 'ignore', 'require_separate_session': False,
             'product': product_configuration() if frontend else None}
    for lens, method in (('checks', 'command'), ('security', 'code'), ('review', 'code')):
        value[lens] = config(method=method)['checks']
        value[lens][0].update(id=lens + '_acceptance', description='python3 -B -m unittest test_greeting' if lens == 'checks' else
                             'Inspect greeting implementation against scope; no secrets or unsafe execution' if lens == 'security' else
                             'Inspect greeting(name) returns exact expected text, test and edge cases within scope')
    if frontend:
        value.update(title='Notes confirmation feature', description='Add a local notes form with responsive layout and save confirmation.',
                     scope=['index.html'], assumptions=['Ephemeral in-page state only; no backend writes.'])
        value['checks'][0]['description'] = 'Check index.html contains the declared notes form; python3 -B -c "from pathlib import Path; assert \'addEventListener\' in Path(\'index.html\').read_text()"'
        value['security'][0]['description']='Inspect index.html notes form for unsafe script execution, outbound effects or exposed secrets; only ephemeral in-page state is authorized.'
        value['review'][0]['description']='Inspect scoped notes confirmation: hide empty state, show Saved: <trimmed note>, clear input and restore focus; preserve existing error/loading behavior, responsive design and form IDs.'
    return value


def result(outcome='implemented', reason='Synthetic feature host', work=None):
    return {'outcome': outcome, 'reason': reason, 'work': work or ['Preserved task work and original base.']}


class FeatureHost(Host):
    def __init__(self, binary, authority, case, root, frontend, library=None, live=False, artifacts=None):
        super().__init__(binary, authority, case, 'frontend' if frontend else 'backend')
        self.root, self.frontend, self.library, self.live, self.artifacts = root, frontend, library, live, artifacts
        self.envs, self.env, self.rounds, self.observations, self.run_ids = [], None, [], [], []
        self.plan_captures=[]
        self.iteration, self.cancelled, self.started_at = 0, False, time.monotonic()
        self.review_mode, self.parallel_fault, self.parallel_live = 'sequential', None, False
        self.parallel_batches, self.parallel_observations = [], []

    def state(self, rid):
        return self.call('run', 'status', rid)['run']

    def drive_feature(self, rid):
        for _ in range(130):
            self.call('run', 'drive', rid)
            tasks = self.call('session', 'task', '--run', rid, '--all')['tasks']
            if not tasks:
                state = self.state(rid)
                assert state['status'] in ('completed', 'failed', 'cancelled'),{k:state.get(k) for k in ('status','outcome','diagnostics')}
                return state
            if self.review_mode == 'parallel-backend' and len(tasks) == 2:
                assert {parallel_host.role(t) for t in tasks} == {'security', 'review'}
                # Public task listing is not branch order. Targeted first/last
                # cancellation/edit cases must settle security before review.
                tasks.sort(key=lambda t: ('security', 'review').index(parallel_host.role(t)))
                assert len({t['attempt_id'] for t in tasks}) == len({t['workspace'] for t in tasks}) == 2
                assert len({t['claim_id'] for t in tasks}) == 1
                assert read(tasks[0], 'candidate') == read(tasks[1], 'candidate')
                self.parallel_batches.append({'attempts': [t['attempt_id'] for t in tasks],
                                              'candidate': read(tasks[0], 'candidate'), 'round': read(tasks[0], 'request')['round']})
                if self.parallel_fault == 'one-timeout' and not self.cancelled:
                    self.cancelled = True
                    time.sleep(31)
                    self.call('run', 'drive', rid)
                    state = self.state(rid)
                    assert state['status'] == 'running' and state.get('outcome') is None, state['status']
                    surviving = self.call('session', 'task', '--run', rid, '--all')['tasks']
                    assert len(surviving) == 1 and parallel_host.role(surviving[0]) == 'review'
                    task = surviving[0]
                    self.tree = Path(task['repository_workspace']); self.claims.add(task['claim_id'])
                    self.seen.append({'run': rid, 'step': 'review'})
                    verdict, values = self.answer_feature(task, 'review')
                    assert self.submit(rid, task, verdict, values) is None
                    self.call('run', 'drive', rid)
                    return self.state(rid)
                if self.parallel_live:
                    self.tree = Path(tasks[0]['repository_workspace']); self.claims.add(tasks[0]['claim_id'])
                    for task in tasks:
                        name = parallel_host.role(task)
                        self.seen.append({'run': rid, 'step': name})
                        request = read(task, 'request')
                        self.rounds.append({'run': rid, 'lens': name, 'round': request['round'],
                                            'digest': read(task, 'candidate')['digest'], 'base': self.base})
                    observation = parallel_host.service(self.binary, self.authority, tasks, host='codex-cli',
                                                         artifacts=self.artifacts / ('round-' + str(len(self.parallel_batches))))
                    self.parallel_observations.extend(observation['observations'])
                    continue
            for task in tasks:
                name = task['skill_refs'][0]['id'].rsplit('/', 1)[-1].removeprefix('feature-').removesuffix('-bridge')
                self.seen.append({'run': rid, 'step': name})
                if task.get('repository_workspace'): self.tree = Path(task['repository_workspace'])
                if task.get('claim_id'): self.claims.add(task['claim_id'])
                if name != 'warmup' and 'implementation' in task['context']['inputs']:
                    assert read(task, 'implementation')['base_commit'] == self.base
                if self.case in ('cancel-resume', 'plan-cancel', 'implement-cancel','frontend-cancel') and not self.cancelled and name == {
                    'cancel-resume': 'review' if self.review_mode == 'parallel-backend' else 'checks',
                    'plan-cancel': 'plan', 'implement-cancel': 'implement','frontend-cancel':'ui'}[self.case]:
                    # A cancelled writer may leave its own plan bytes. Native continue must reconcile them.
                    if self.parallel_fault == 'timeout':
                        self.cancelled = True
                        time.sleep(31)
                        self.call('run', 'drive', rid)
                        state = self.state(rid)
                        assert all(a.get('settled') for a in state['attempts'].values())
                        assert any(d['code'] == 'attempt_deadline_expired' for d in state['diagnostics'])
                        return state
                    if self.parallel_fault == 'during-reader-edit':
                        (self.tree / 'owner.txt').write_text('Owner edit while last parallel reader was active\n')
                        verdict, values = self.answer_feature(task, name)
                        refused = self.submit(rid, task, verdict, values)
                        assert refused and refused['code'] == 'effect_not_permitted', refused
                    if name == 'plan':
                        path = self.tree / '.ai-factory/PLAN.md'; path.parent.mkdir(exist_ok=True)
                        path.write_text('Interrupted owner plan bytes\n')
                    self.cancelled = True
                    self.call('run', 'cancel', rid, '--reason', 'Owned fixture cancellation')
                    if name in ('plan','implement'):
                        refusal=verify.run(self.binary,'--project',self.authority,'run','drive',rid,expect_ok=False)
                        assert 'recovery_required' in refusal,refusal
                        self.call('run','resolve',rid,'--attempt',task['attempt_id'],'--outcome','applied' if name=='plan' else 'not_applied',
                                  '--reason','Synchronous fixture actor returned: planner wrote inspected partial bytes; implement cancellation occurred before any actor write. Materialized inputs and work preserved; no external effects.')
                    self.call('run', 'drive', rid)
                    if self.env: self.env.close()
                    return self.state(rid)
                if self.live:
                    if name in ('environment', 'release'):
                        verdict, values = self.answer_feature(task, name)
                        refusal=self.submit(rid, task, verdict, values)
                        assert refusal is None,refusal
                    elif name in ('ui', 'ux'):
                        self.observations.append(live_reader(self.binary, self.authority, rid, task, self.library,
                                                            self.artifacts, self.case, self.iteration*100+read(task,'request')['round']))
                    else:
                        self.live_attempt(rid, task, name)
                    continue
                verdict, values = self.answer_feature(task, name)
                refusal=self.submit(rid, task, verdict, values)
                assert refusal is None,(name,refusal)
                if self.case == 'stale-after-review' and name == 'review':
                    # Both reports are accepted, before drive hands out the
                    # transport Attempt. Editing during any live assisted
                    # Attempt correctly fails the native none-effects guard.
                    (self.tree / 'owner.txt').write_text('Owner edited after reader\n')
                if self.review_mode == 'parallel-backend' and name in ('security', 'review'):
                    self.call('run', 'drive', rid)
                    outstanding = self.call('session', 'task', '--run', rid, '--all')['tasks']
                    if name == 'security':
                        assert len(outstanding)==1 and parallel_host.role(outstanding[0])=='review'
                    if outstanding:
                        state = self.state(rid)
                        active_steps = [state['steps'][a['step_instance_id']]['definition_ref']['id']
                                        for a in state['attempts'].values() if not a.get('settled')]
                        assert 'aif-feature:step/repair' not in active_steps and 'aif-feature:step/commit' not in active_steps
        raise AssertionError('W3 Run did not settle within fixture bound')

    def answer_feature(self, task, name):
        tree = self.tree
        if name == 'parallel-admission':
            parallel_host.verify_adapter(task)
            value = (parallel_host.admission(self.binary, self.authority, 'codex-cli') if self.parallel_live else
                     {'protocol': parallel_host.PROTOCOL, 'status': 'ready', 'host': 'codex-cli',
                      'reason': 'Synthetic capability for native graph assertions; not actual host qualification.'})
            if self.parallel_fault == 'unsupported-host':
                value.update(status='unavailable', host='claude-code', reason='No qualified independent host dispatcher')
            return 'pass' if value['status'] == 'ready' else 'blocked', {'admission': value}
        if name == 'collect-reviews':
            value = parallel_host.collect(self.binary, self.authority, task)
            if self.parallel_fault == 'bad-digest': value['reports'][0]['raw_base64'] = 'e30='
            if self.parallel_fault == 'stale-bundle': value['manifest_digest'] = 'sha256:' + '0' * 64
            if self.parallel_fault == 'missing-report': value['reports'] = value['reports'][:1]
            if self.parallel_fault == 'export-unavailable':
                value = parallel_host.collect(Path('/bin/false'), self.authority, task)
            return 'pass' if value['status'] == 'ready' else 'blocked', {'bundle': value}
        if name == 'warmup':
            self.base = git_out(tree, 'rev-parse', 'HEAD')
            return 'pass', {'handoff': {'summary': 'Small isolated feature fixture.', 'entry_points': ['index.html' if self.frontend else 'greeting.py'],
                                       'conventions': ['No dependencies; keep owner files.'], 'sources': ['owner.txt']},
                            'implementation': implementation(tree, self.base)}
        if name == 'plan':
            if self.case in ('too-large', 'requirement-conflict', 'foreign-fix-plan', 'configured-plan'):
                path=tree/'.ai-factory/PLAN.md';path.parent.mkdir(exist_ok=True);path.write_text('# BLOCKED diagnostic snapshot\n\n## Original Request\n'+read(task,'task')['description']+'\n\n## Settings\n- Testing: yes\n- Logging: verbose\n- Docs: no\n\nBlocking reason: '+self.case+'\n\n## Tasks\nNo executable tasks; owner resolution required.\n')
                return 'blocked', {'result': result('too_large' if self.case == 'too-large' else 'owner_required', self.case)}
            value = read(task, 'task')
            path = tree / '.ai-factory/PLAN.md'; path.parent.mkdir(exist_ok=True)
            assert not path.exists(), 'Native producer must not overwrite existing bytes'
            path.write_text('# Implementation Plan: ' + value['title'] + '\n\nBranch: ' + git_out(tree, 'branch', '--show-current') +
                            '\nCreated: fixture\n\n## Original Request\n' + value['description'] +
                            '\n\n## Settings\n- Testing: yes\n- Logging: verbose\n- Docs: no\n\n## Tasks\n'
                            '- [ ] Task 1: Implement scoped feature with configurable logging.\n'
                            '- [ ] Task 2: Verify declared acceptance with test.\n')
            if task['decision_context']['plan_retention'] == 'retain':
                git_out(tree, 'add', '--', '.ai-factory/PLAN.md')
            self.plan_captures.append({'stage':'plan','sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            return 'pass', {'result': result('ready')}
        if name in ('implement', 'repair'):
            if name == 'repair' and self.case == 'repair-too-large':
                return 'pass', {'implementation': implementation(tree, self.base), 'result': result('too_large', 'Requires another reviewed plan')}
            if name == 'implement':
                path = tree / '.ai-factory/PLAN.md'; assert path.exists()
                manifest=read(task,'plan')
                assert manifest['files'][0]['ref']['digest']=='sha256:'+hashlib.sha256(path.read_bytes()).hexdigest(),manifest
                path.write_text(path.read_text().replace('- [ ]', '- [x]'))
                self.plan_captures.append({'stage':'implement','sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            if self.frontend:
                html = (verify.ROOT / 'tests/fixtures/product/index.html').read_text()
                if name == 'implement' and self.case in ('repair-ui', 'repair-ux'):
                    html = html.replace('/* DEFECT_OVERFLOW */', 'section { min-width: 800px; }') if self.case == 'repair-ui' else html.replace('/* DEFECT_FLOW */', 'return;')
                (tree / 'index.html').write_text(html)
            else:
                (tree / 'greeting.py').write_text('def greeting(name):\n    return f"Hello, {name}!"\n')
                (tree / 'test_greeting.py').write_text('import unittest\nfrom greeting import greeting\nclass GreetingTest(unittest.TestCase):\n    def test_name(self): self.assertEqual(greeting("Ada"), "Hello, Ada!")\n')
            if name == 'repair':
                path=tree/('index.html' if self.frontend else 'greeting.py')
                path.write_text(path.read_text()+('\n<!-- scoped fixture repair -->\n' if self.frontend else '\n# scoped fixture repair\n'))
            return 'pass', {'implementation': implementation(tree, self.base), 'result': result()}
        if name in ('checks', 'security', 'review', 'ui', 'ux'):
            request, candidate = read(task, 'request'), read(task, 'candidate')
            count = request['round']; self.rounds.append({'run': task['run_id'], 'lens': name, 'round': count, 'digest': candidate['digest'], 'base': candidate['base_commit']})
            value = report(request, candidate)
            if self.review_mode == 'parallel-backend' and name in ('security', 'review'):
                value['session'] = 'separate' if self.parallel_fault != 'shared-session' else 'shared'
                if self.parallel_fault == 'stale-report': value['round'] += 1
            value['request_digest'] = task['context']['inputs']['request']['ref']['digest']
            for i, check in enumerate(request['checks']):
                entry = copy.deepcopy(value['checks'][0]); value['checks'][i:i+1] = [entry]
                entry['id'] = check['id']
                skip = 'excluded' if not check['enabled'] else 'not_applicable' if not check['applicable'] else None
                unavailable = self.case == 'required-unavailable' and name == 'checks' or self.case in ('blocked-resume', 'upgrade', 'upgrade-refusal') and self.iteration == 0 and name == 'checks' or self.case == 'chained-resume' and self.iteration < 2 and name == 'checks'
                if unavailable: skip = 'unavailable'
                if self.parallel_fault == 'failed-unavailable' and name == 'review': skip = 'unavailable'
                failing = (self.case == 'repair-' + name and count == 1 or self.case == 'repair-too-large' and name == 'checks'
                           or self.case in ('exhaustion', 'max-budget') and name == 'checks'
                           or self.case == 'verdict-independent' and count == 1 and name == 'checks')
                if self.parallel_fault == 'failed-unavailable' and name == 'security': failing = True
                if skip:
                    entry.update(status=skip, result='not_run', reason='Declared skip / required environment unavailable', evidence=[])
                elif name in ('ui', 'ux'):
                    cfg, env = read(task, 'configuration'), read(task, 'environment')
                    if env['status']!='ready':
                        entry.update(status='unavailable',result='not_run',reason=env['reason'],evidence=[])
                        continue
                    if self.library:
                        out = Path(task['workspace']) / 'browser'; task_file = Path(task['workspace']) / 'browser-task.json'; task_file.write_text(json.dumps(task))
                        proc = subprocess.run(['node', str(Path(__file__).with_name('product_browser.cjs')), str(self.library), str(task_file), str(out)], text=True, capture_output=True, timeout=90, env=os.environ.copy())
                        assert proc.returncode == 0, proc.stderr
                        observation = json.loads(proc.stdout); items = observation['observations']; tool = observation['tool']
                        failing = any(item['failures'] for item in items)
                        if self.artifacts:
                            destination=self.artifacts/(self.case+'-round'+str(count)+'-'+name)
                            shutil.copytree(out,destination,dirs_exist_ok=True)
                            for item in items:
                                screenshot=Path(item['screenshot'])
                                item['screenshot_sha256']=hashlib.sha256(screenshot.read_bytes()).hexdigest()
                                item['screenshot_artifact']=destination.name+'/'+screenshot.name
                        self.observations.append(observation)
                    else:
                        items = [{'scenario': s['id'], 'viewport': s['viewport'], 'url': env['url'] + s['path'], 'observations': 'Synthetic scenario declaration, no browser execution claimed'} for s in cfg['scenarios'] if s['lens'] == name]
                        tool = 'synthetic-browser-report'
                    entry.update(result='failed' if failing else 'passed', reason='Observed product defect' if failing else '', evidence=[{'method':'browser','tool':tool,'locator': item['url'],'observation':json.dumps({k:item[k] for k in ('scenario','viewport','url','observations')}),'exit_code':None} for item in items])
                else:
                    if check['method'] == 'command':
                        args = ['python3','-B','-c',"from pathlib import Path; assert 'addEventListener' in Path('index.html').read_text()"] if self.frontend else ['python3','-B','-m','unittest','test_greeting']
                        proc = subprocess.run(args,cwd=tree,capture_output=True,text=True,timeout=60)
                        assert proc.returncode == 0, proc.stderr
                        entry['evidence'] = [{'method':'command','tool':' '.join(args),'locator':str(tree),'observation':'exit='+str(proc.returncode)+'; stdout='+repr(proc.stdout)+'; stderr='+repr(proc.stderr),'exit_code':0}]
                    entry.update(result='failed' if failing else 'passed', reason='Injected scoped defect' if failing else '')
                    if self.case == 'owner-stop' and name == 'checks': entry.update(result='warnings',reason='Owner review required by declared policy')
            return ('needs_revision' if self.case == 'verdict-independent' and name == 'review' else 'pass'), {'report': value}
        if name == 'environment':
            cfg, candidate = read(task, 'configuration'), read(task, 'candidate')
            if self.case=='frontend-unavailable':
                return 'pass',{'environment':{'status':'unavailable','owner':cfg['environment']['owner'],'profile':cfg['environment']['profile'],
                    'configuration_digest':task['context']['inputs']['configuration']['ref']['digest'],'candidate_digest':candidate['digest'],
                    'session':None,'url':None,'reason':'Required project browser/server unavailable; no provision attempted'}}
            self.env = OwnedEnvironment(self.root/'environment-state', tree, cfg['environment']['owner'], profile=cfg['environment']['profile'])
            self.envs.append(self.env); self.env.ensure()
            return 'pass', {'environment': {'status':'ready','owner':self.env.owner,'profile':cfg['environment']['profile'],
                'configuration_digest': task['context']['inputs']['configuration']['ref']['digest'], 'candidate_digest':candidate['digest'],
                'session':self.env.session,'url':self.env.url,'reason':''}}
        if name == 'release':
            env = read(task, 'environment')
            if self.env:self.env.close()
            return 'pass', {'release':{'status':'released' if env['session'] else 'not_needed','owner':env['owner'],'session':env['session'],'reason':''}}
        if name == 'commit':
            if self.case in ('stale-before-commit','commit-diagnostic') or self.case=='commit-resume' and self.iteration==0:
                if self.case == 'stale-before-commit': (tree/'owner.txt').write_text('Intervening owner edit before commit\n')
                return 'pass', {'implementation':implementation(tree,self.base),'result':result('owner_required','Candidate/commit requires owner')}
            paths = ['index.html'] if self.frontend else ['greeting.py','test_greeting.py']
            if git_out(tree, 'ls-files', '--', '.ai-factory/PLAN.md'): paths.append('.ai-factory/PLAN.md')
            verify.git('-C', tree, 'add', '--', *paths)
            if git_out(tree,'diff','--cached','--name-only'): verify.git('-C',tree,'commit','-qm','feat: scoped fixture')
            committed = implementation(tree,self.base)
            committed['changed_files'] = git_out(tree,'-c','core.quotepath=off','diff','--name-only',self.base+'..HEAD').splitlines()
            return 'pass', {'implementation':committed,'result':result()}
        raise AssertionError(name)

    def live_attempt(self, rid, task, name):
        import shlex
        workspace=Path(task['workspace']);task_file=workspace/'task.json';task_file.write_text(json.dumps(task,indent=2))
        template=self.call('session','submit','--template','--run',rid,'--attempt',task['attempt_id'])
        (workspace/'submission-template.json').write_text(json.dumps(template,indent=2))
        prefix=self.artifacts/(f'{len(self.observations):02d}-'+name);prefix.mkdir(parents=True,exist_ok=True)
        prompt=f'''Execute exactly one delivered Pri-Fly assisted-session Attempt. Read {task_file}, every pinned instruction/supporting reference materialized under this task workspace context/skills, the bound inputs, and submission-template.json. Follow the sealed W3 bridge and upstream AI Factory skill. The caller has chosen this bounded workflow; do not start other workflows or select an expected verdict.
Use ONLY the named repository_workspace for this task. Readers and warmup are read-only; writers may edit only the feature's declared scope, its owned native PLAN progress, and explicitly permitted factual project context. Preserve other files and staged work. No push, merge, dependency installation, credentials, unrelated projects, environment changes or Pri-Fly control calls. The controller supplies no expected verdict and will submit your file unchanged.
The caller explicitly authorizes this owned fixture directory {self.tree} for the role just declared and the task workspace {workspace} for output files. CLI --add-dir grants only that exact fixture directory alongside this task workspace, retaining workspace-write sandbox and automatic review. Read-only Attempts still must not write the repository; the controller verifies that contract. No parent directory or other project is authorized.
This is an isolated stdlib Python feature fixture (or a local notes HTML fixture if the task says so); no external network/dependencies are required. Apply actual project discovery and acceptance. Do not invent a host model mapping: this is a fresh separate CLI session but no independent-review model translation is supplied. A typed W1 report model_profile is a string with model:null for unavailable. Native submission model_profile is answered ONLY when task.model_profile is declared: an object with outcome and literal reason for unavailable/declined, or named for honoured. When the task has no model profile, keep template model_profile:null; any non-null object is rejected model_profile_not_declared. answered_questions is a top-level list, [] when no actual questions arose. Copy identities from the template unchanged. A usable report can have failed/unavailable check results; derive them from observed facts, not controller expectations.
Write all ordinary typed outputs to allocated output slots and compute actual SHA256 digests. A native plan output uses engine capture: create/update .ai-factory/PLAN.md in the repository as declared, and leave the native captured plan slot and identity fields in the template for Pri-Fly; do not invent a workspace-tree manifest. Produce a complete submission.json in {workspace}. Do not submit it yourself.
Git local commits are authorized only where the bridge allows them, with fixture identity via per-command git -c user.name=prifly-feature-test -c user.email=fixture@example.invalid -c commit.gpgsign=false; do not change global git configuration. The scope has a local commit stage, no publication.
If a bounded shell command cannot start because of bwrap/environment sandbox, request automatic approval for exactly that task command using require_escalated and a concrete reason. Keep workspace-write isolation; no full-access flags, credentials or broader path access. A rejected command stays rejected, and genuine unavailability must be reported. Finish with the output paths.'''
        (prefix/'prompt.txt').write_text(prompt);shutil.copyfile(task_file,prefix/'task.json')
        shutil.copyfile(workspace/'submission-template.json',prefix/'template.json')
        shutil.copytree(workspace/'inputs',prefix/'inputs',dirs_exist_ok=True)
        before_version=self.call('run','status',rid)['run_version']
        before=None
        if name not in ('plan','implement','repair','commit'):
            from test_product_review import p
            before=p.w1.snapshot(self.tree,git_out(self.tree,'rev-parse','HEAD') if self.base is None else self.base)
        with (prefix/'events.jsonl').open('w') as out,(prefix/'stderr.txt').open('w') as err:
            proc=subprocess.run(['codex','exec','--ephemeral','--json','--approve-for-me','--add-dir',str(self.tree),'-C',str(workspace),
                '--skip-git-repo-check','-o',str(workspace/'host-final.txt'),'-'],input=prompt,text=True,stdout=out,stderr=err,timeout=600)
        assert proc.returncode==0,(proc.returncode,(prefix/'stderr.txt').read_text()[-2500:])
        assert self.call('run','status',rid)['run_version']==before_version,'Host mutated authority'
        submission=workspace/'submission.json';data=json.loads(submission.read_text())
        # Preserve unedited files before validation so protocol/scope failures remain reviewable.
        shutil.copyfile(submission,prefix/'submission.json')
        for port,slot in task['context']['outputs'].items():
            output_path=workspace/slot['path']
            if output_path.is_file():shutil.copyfile(output_path,prefix/(port+'.json'))
        if name=='warmup':self.base=read_output(task,'implementation')['base_commit']
        if before is not None:
            assert p.w1.snapshot(self.tree,self.base or before['base_commit'])==before,'Reader mutated claimed candidate'
        session=None
        for line in (prefix/'events.jsonl').read_text().splitlines():
            event=json.loads(line)
            if event.get('type')=='thread.started':session=event['thread_id']
        assert session
        outputs={}
        for port,slot in task['context']['outputs'].items():
            path=workspace/slot['path']
            if path.is_file():
                raw=path.read_bytes();assert data['result']['outputs'][port]['digest']=='sha256:'+hashlib.sha256(raw).hexdigest()
                outputs[port]=json.loads(raw);shutil.copyfile(path,prefix/(port+'.json'))
        shutil.copyfile(submission,prefix/'submission.json')
        receipt=self.call('session','submit','--file',submission);(prefix/'receipt.json').write_text(json.dumps(receipt,indent=2))
        self.observations.append({'step':name,'session':session,'verdict':data['result']['verdict'],'outputs':outputs,
                                  'submission_sha256':hashlib.sha256(submission.read_bytes()).hexdigest(),
                                  'events_sha256':hashlib.sha256((prefix/'events.jsonl').read_bytes()).hexdigest()})
        print(json.dumps({'live_step':name,'verdict':data['result']['verdict'],'session':session}),flush=True)
        # Isolated test injection AFTER actual author completion, outside reader context.
        if name=='implement' and self.case=='live-repair':
            path=self.tree/'greeting.py';original=path.read_text();assert 'Hello' in original
            path.write_text(original.replace('Hello','Goodbye',1))
            test=subprocess.run(['python3','-B','-m','unittest','test_greeting'],cwd=self.tree,capture_output=True,text=True,timeout=60)
            if test.returncode==0:
                # A docstring edit is not a product defect. Inject an actual scoped exported behavior instead.
                path.write_text(original+'\n\ndef greeting(name):\n    return f"Goodbye, {name}!"\n')
                test=subprocess.run(['python3','-B','-m','unittest','test_greeting'],cwd=self.tree,capture_output=True,text=True,timeout=60)
            assert test.returncode!=0,'Fixture fault did not break actual acceptance'
            (self.artifacts/'fault-injection.json').write_text(json.dumps({'path':'greeting.py','before_sha256':hashlib.sha256(original.encode()).hexdigest(),
                'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'check':'python3 -B -m unittest test_greeting','exit_code':test.returncode,
                'stdout':test.stdout,'stderr':test.stderr},indent=2))
        if name=='checks' and self.case=='live-resume' and self.iteration==0:
            # The initial delivered check is genuinely unavailable; no reader verdict edits.
            assert outputs['report']['checks'][0]['status']=='unavailable',outputs


def read_output(task, name):
    return json.loads((Path(task['workspace'])/task['context']['outputs'][name]['path']).read_text())


def run_case(binary, case, host='codex-cli', library=None, live=False, artifacts=None, skills=None,
             review_mode='sequential', parallel_fault=None, parallel_live=False,
             host_factory=None, adapter_factory=None, task_mutator=None, expected_outcome=None):
    with tempfile.TemporaryDirectory(prefix='w3-run-') as directory:
        root = Path(directory); repository, authority = verify.prepare_repository(binary, root); runs=[]; h=None
        try:
            frontend = review_mode == 'parallel-ui-ux' or case in ('frontend','repair-ui','repair-ux','frontend-unavailable','frontend-cancel')
            if case=='live-frontend':frontend=True
            if live or parallel_live:
                source=skills or Path('/tmp/w3-upstream')
                import product_check
                product_check.AUTO_REVIEW=True
                skill_files={'aif-plan':'plan.md','aif-implement':'implement.md','aif-commit':'aif-commit.md',
                             'aif-warmup':'aif-warmup.md','aif-security-checklist':'aif-security-checklist.md'}
                for host_root in verify.HOSTS.values():
                    for skill,filename in skill_files.items():shutil.copyfile(source/filename,repository/host_root/skill/'SKILL.md')
                    shutil.copyfile(source/'aif-review.md',repository/host_root/'aif-review/SKILL.md')
                    shutil.copyfile(source/'severity.md',repository/host_root/'aif-review/references/SEVERITY.md')
                    for skill,filename,target in [('aif-plan','task-format.md','TASK-FORMAT.md'),('aif-implement','implementation-guide.md','IMPLEMENTATION-GUIDE.md'),('aif-implement','logging-guide.md','LOGGING-GUIDE.md')]:
                        shutil.copyfile(source/filename,repository/host_root/skill/'references'/target)
            (repository/'owner.txt').write_text('Preserve owner work\n')
            if frontend: (repository/'index.html').write_text('<!doctype html><title>Initial page</title>\n')
            if case=='live-frontend':
                html=(verify.ROOT/'tests/fixtures/product/index.html').read_text()
                html=html.replace("document.querySelector('#empty').hidden=true;document.querySelector('#success').hidden=false;",'')
                html=html.replace("document.querySelector('#success').textContent='Saved: '+note.value.trim();note.value='';note.focus();",'')
                (repository/'index.html').write_text(html)
            if case=='live-resume':
                (repository/'.gitignore').write_text('.acceptance-ready\n')
                (repository/'acceptance.py').write_text("from pathlib import Path\nif not Path('.acceptance-ready').exists():\n    print('Required fixture tool prerequisite unavailable: owner must provide .acceptance-ready; this is not a code defect')\n    raise SystemExit(77)\nfrom greeting import greeting\nassert greeting('Ada') == 'Hello, Ada!'\nprint('acceptance passed')\n")
            if case == 'foreign-plan':
                path=repository/'.ai-factory/PLAN.md';path.parent.mkdir(exist_ok=True);path.write_text('Foreign native plan bytes\n')
            if case == 'foreign-fix-plan':
                path=repository/'.ai-factory/FIX_PLAN.md';path.parent.mkdir(exist_ok=True);path.write_text('Foreign fix plan bytes\n')
            if case == 'configured-plan':
                path=repository/'.ai-factory/config.yaml';path.parent.mkdir(exist_ok=True);path.write_text('paths:\n  plan: other/PLAN.md\n')
            package=repository/'.prifly/workflows/aif-feature'
            limit=8 if case == 'max-budget' else 2 if case == 'exhaustion' else 3
            (package/'extend.yaml').write_text(f'profile: {"frontend" if frontend else "backend"}\nsettings:\n  quality: {{limit: {limit}}}\n  feature: {{review_mode: {review_mode}}}\nexclude: []\nextensions: []\n')
            if adapter_factory:
                adapter = adapter_factory(root, repository, package)
                path = package/'extend.yaml'
                path.write_text(path.read_text().replace('{review_mode: '+review_mode+'}',
                    json.dumps({'review_mode': review_mode, 'browser_adapter': adapter})))
            if parallel_fault in ('timeout','one-timeout'):
                path = package/'steps'/('security.yaml' if parallel_fault=='one-timeout' else 'review.yaml')
                path.write_text(path.read_text().replace('active_timeout_ms: null', 'active_timeout_ms: 30000'))
            verify.git('-C',repository,'add','.');verify.git('-C',repository,'commit','-qm','Feature fixture')
            value=task_input(frontend)
            if task_mutator: task_mutator(value)
            if live:
                value['require_separate_session']=True
                if value['product']:
                    for lens in ('ui','ux'):value['product'][lens]['require_separate_session']=True
            if case=='live-frontend':
                value['description']='Add save confirmation to the existing notes form: after loading hide empty state, show Saved: <trimmed note>, clear input and restore focus. Preserve existing error/loading, mobile layout and IDs.'
            if case=='live-resume':
                value['checks'][0]['description']='Run python3 -B acceptance.py. Exit 77 explicitly means required tool prerequisite unavailable (owner must provide ignored .acceptance-ready); report unavailable/not_run, not a code defect. Do not create/alter this owner prerequisite or acceptance.py during implementation or repair.'
            if case=='owner-stop':value['optional_policy']='stop'
            if case=='excluded-security':value['security'][0]['enabled']=False
            task_path=root/'task.json';task_path.write_text(json.dumps(value))
            verify.run(binary,'--project',authority,'project','local','set','--repository',repository,'--allow-executable','python='+str(Path(sys.executable).resolve()))
            args=('--project',authority,'project','start','--repository',repository,'--launch','aif-feature','--host',host,'--workspace','worktree','--input','task='+str(task_path),'--allow-execution', '--decision-policy','autonomous','--preflight-answer','plan_retention='+json.dumps('retain' if case=='retained-plan' else 'capture'),'--preflight-answer','plan_tests=true','--preflight-answer','plan_constraints=""')
            prepared=verify.run(binary,*args[:3],'questionnaire',*args[4:],'--prepare')
            rid=verify.run(binary,*args,'--expected-launch-digest',prepared['review_digest'])['run']['run']['id'];runs.append(rid)
            h=(host_factory or FeatureHost)(binary,authority,case,root,frontend,library,live,artifacts)
            h.review_mode, h.parallel_fault, h.parallel_live = review_mode, parallel_fault, parallel_live
            state=h.drive_feature(rid); source_outcome=state.get('outcome') or state['status']
            initial_state=copy.deepcopy(state)
            if live and artifacts:
                (artifacts/'source-state.json').write_text(json.dumps(state,indent=2))
            if case == 'foreign-plan':
                assert state['status']=='failed' and any(x['code']=='workspace_tree_output_exists' for x in state['diagnostics']),{k:state.get(k) for k in ('status','outcome','diagnostics')}
                assert (h.tree/'.ai-factory/PLAN.md').read_text()=='Foreign native plan bytes\n'
            if case in ('blocked-resume','cancel-resume','chained-resume','plan-cancel','implement-cancel','upgrade','upgrade-refusal','live-resume','frontend-cancel','commit-resume'):
                assert (source_outcome in ('partial','cancelled') or case in ('plan-cancel','implement-cancel') and source_outcome=='failed'
                        or parallel_fault in ('timeout','one-timeout') and source_outcome=='rejected'), {k:state.get(k) for k in ('status','outcome','diagnostics')}
                if case == 'plan-cancel':
                    # Preparation must refuse the partial producer's bytes rather than discard them.
                    before=(h.tree/'.ai-factory/PLAN.md').read_bytes()
                (h.tree/'owner.txt').write_text('Preserved owner edit across continuation\n')
                if case=='live-resume':(h.tree/'.acceptance-ready').write_text('Owner provided isolated fixture prerequisite\n')
                if case=='upgrade':
                    p=package/'contexts/feature-review.yaml';p.write_text(p.read_text().replace('version: 1.0.0','version: 1.0.1',1).replace('Apply pinned aif-review','Repeat current review, preserving coverage. Apply pinned aif-review',1))
                if case=='upgrade-refusal':
                    p=package/'steps/configure.yaml';p.write_text(p.read_text().replace('retry_class: never','retry_class: pure'))
                for iteration in range(1,3 if case=='chained-resume' else 2):
                    h.iteration=iteration
                    cont=('--project',authority,'project','continue','--repository',repository,'--launch','aif-feature','--source-run',runs[-1],'--host',host,'--allow-execution')
                    if case in ('plan-cancel','implement-cancel'):
                        before_version=verify.run(binary,'--project',authority,'run','status',rid)['run_version']
                        refused=verify.run(binary,*cont,'--prepare',expect_ok=False)
                        assert 'recover_source_unsettled' in refused,refused
                        assert verify.run(binary,'--project',authority,'run','status',rid)['run_version']==before_version
                        if case=='plan-cancel':assert (h.tree/'.ai-factory/PLAN.md').read_bytes()==before
                        assert (h.tree/'owner.txt').read_text()=='Preserved owner edit across continuation\n'
                        return {'case':case,'host':host,'source_outcome':'failed after cancellation + inspected resolve',
                                'outcome':'recover_source_unsettled','writer_reconciliation':('applied' if case=='plan-cancel' else 'not_applied')+'; no retry',
                                'work_preserved':True,'same_claim':len(h.claims)==1,'cleaned':True}
                    if case=='upgrade-refusal':
                        version=verify.run(binary,'--project',authority,'run','status',rid)['run_version']
                        refused=verify.run(binary,*cont,'--prepare',expect_ok=False);assert 'recover_prefix_changed' in refused,refused
                        assert verify.run(binary,'--project',authority,'run','status',rid)['run_version']==version
                        replay=(*cont,'--from-stage','configure')
                        prep=verify.run(binary,*replay,'--prepare')
                        assert verify.run(binary,'--project',authority,'run','status',rid)['run_version']==version
                        replay_id=verify.run(binary,*replay,'--expected-launch-digest',prep['review_digest'])['run']['run']['id'];runs.append(replay_id)
                        replay_state=h.drive_feature(replay_id)
                        assert replay_state['outcome']=='succeeded',{k:replay_state.get(k) for k in ('status','outcome','diagnostics')}
                        assert len(h.claims)==1 and (h.tree/'owner.txt').read_text()=='Preserved owner edit across continuation\n'
                        return {'case':case,'host':host,'source_outcome':source_outcome,'default_prepare_refusal':'recover_prefix_changed',
                                'reviewed_replay':'configure (warmup prefix retained)','outcome':'succeeded','same_claim':True,'work_preserved':True,'cleaned':True}
                    prep=verify.run(binary,*cont,'--prepare')
                    rid=verify.run(binary,*cont,'--expected-launch-digest',prep['review_digest'])['run']['run']['id'];runs.append(rid)
                    if case=='plan-cancel':
                        # No automatic deletion of an interrupted native producer.
                        try:state=h.drive_feature(rid)
                        except AssertionError:
                            state=h.state(rid)
                        assert (h.tree/'.ai-factory/PLAN.md').read_bytes()==before
                        assert state['status']=='failed' and any(x['code']=='workspace_tree_output_exists' for x in state['diagnostics']),{k:state.get(k) for k in ('status','outcome','diagnostics')}
                        break
                    state=h.drive_feature(rid)
                assert (h.tree/'owner.txt').read_text()=='Preserved owner edit across continuation\n'
            expected='succeeded' if case in ('backend','frontend','repair-checks','repair-security','repair-review','repair-ui','repair-ux','retained-plan','blocked-resume','cancel-resume','chained-resume','implement-cancel','upgrade','excluded-security','verdict-independent') else 'partial'
            if parallel_fault and parallel_fault not in ('timeout','one-timeout','during-reader-edit'):
                expected = 'rejected' if parallel_fault == 'unsupported-host' else 'partial'
            if review_mode == 'parallel-backend' and frontend: expected = 'rejected'
            if case.startswith('live-') or case in ('frontend-cancel','commit-resume'):expected='succeeded'
            if expected_outcome is not None: expected=expected_outcome
            if case not in ('foreign-plan','plan-cancel'):assert state.get('outcome')==expected,{k:state.get(k) for k in ('status','outcome','diagnostics')}
            if expected=='succeeded':
                assert {'implementation','result','plan','gate','evidence'} <= state['output_artifacts'].keys()
                assert git_out(h.tree,'rev-parse','HEAD') != h.base
            names=[x['step'] for x in h.seen]
            if parallel_fault and parallel_fault not in ('timeout','one-timeout','during-reader-edit') or review_mode == 'parallel-backend' and frontend:
                assert 'repair' not in names and 'commit' not in names
            if parallel_fault == 'unsupported-host' or review_mode == 'parallel-backend' and frontend:
                assert 'plan' not in names and 'implement' not in names and not h.parallel_batches
            if case in ('required-unavailable','owner-stop','too-large','requirement-conflict','stale-after-review','frontend-unavailable'):
                assert 'repair' not in names and 'commit' not in names
            if case in ('exhaustion','max-budget'):
                assert names.count('repair')==limit-1 and names.count('checks')==limit and 'commit' not in names
            if case.startswith('repair-') and case!='repair-too-large' or case=='verdict-independent':
                assert names.count('repair')==1
                for lens in ('checks','security','review') + (('ui','ux') if frontend else ()):
                    assert names.count(lens)==2,(lens,names)
            if case=='live-repair':
                assert names.count('repair')>=1,names
                for lens in ('checks','security','review'):assert names.count(lens)>=2,names
            if case=='commit-resume':
                for lens in ('checks','security','review'):assert names.count(lens)==2,names
                assert names.count('commit')==2
                assert len({x['digest'] for x in h.rounds})==2,'Commit continuation accepted old candidate'
            assert len(h.claims)==1
            assert all(item['base']==h.base for item in h.rounds)
            if case=='retained-plan':assert git_out(h.tree,'ls-files','--','.ai-factory/PLAN.md') and '[x]' in (h.tree/'.ai-factory/PLAN.md').read_text()
            elif case not in ('foreign-plan','plan-cancel'):assert not (h.tree/'.ai-factory/PLAN.md').exists(), 'Owned untracked plan must be captured, not lost or left blocking next Run'
            if case=='foreign-fix-plan':assert (h.tree/'.ai-factory/FIX_PLAN.md').read_text()=='Foreign fix plan bytes\n'
            actual_outputs={}
            if live or review_mode in ('parallel-backend','parallel-ui-ux') and 'evidence' in state['output_artifacts']:
                for port,reference in state['output_artifacts'].items():
                    ref_file=root/(port+'-ref.json');out_file=root/(port+'-export.json');ref_file.write_text(json.dumps(reference))
                    h.call('artifact','export','--ref',ref_file,'--output',out_file)
                    actual_outputs[port]=json.loads(out_file.read_text())
                if artifacts:
                    (artifacts/'final-state.json').write_text(json.dumps(state,indent=2))
                    (artifacts/'final-outputs.json').write_text(json.dumps(actual_outputs,indent=2))
                if expected == 'succeeded':
                    assert actual_outputs['implementation']['base_commit']==h.base
                    assert actual_outputs['implementation']['head_commit']==git_out(h.tree,'rev-parse','HEAD')
                    assert actual_outputs['implementation']['changed_files']==git_out(h.tree,'-c','core.quotepath=off','diff','--name-only',h.base+'..HEAD').splitlines()
                verify.git('-C',h.tree,'status','--porcelain')
            return {'case':case,'host':host,'mode':'fresh actual Codex CLI writers/readers, unedited submissions' if live else 'actual browser with deterministic writer/reader assertions' if library else 'synthetic host, real programs/Git',
                    'source_outcome':source_outcome,'outcome':state.get('outcome') or state['status'],'runs':len(runs),
                    'steps':names,'rounds':h.rounds,'plan_captures':h.plan_captures,'elapsed_seconds':round(time.monotonic()-h.started_at,3),'cleaned':True,
                    'review_mode':review_mode,'parallel_fault':parallel_fault,'parallel_batches':h.parallel_batches,
                    'parallel_observations':h.parallel_observations,
                    **({'parallel_outputs':actual_outputs} if review_mode in ('parallel-backend','parallel-ui-ux') else {}),
                    **({'observations':h.observations,'outputs':actual_outputs} if live else
                       {'browser_observations':h.observations} if library else {}),
                    **(h.extra_result() if hasattr(h,'extra_result') else {})}
        finally:
            if h:
                if hasattr(h,'cleanup_fixture'): h.cleanup_fixture()
                for env in h.envs:env.close()
            runs=list(dict.fromkeys(runs+[r['run_id'] for r in verify.run(binary,'--project',authority,'run','list')['runs']]))
            try:
                clean(binary,authority,runs)
                for owned in runs:
                    state=verify.run(binary,'--project',authority,'run','status',owned)['run']
                    for attempt_id,attempt in state['attempts'].items():
                        if attempt['status']=='uncertain':
                            verify.run(binary,'--project',authority,'run','resolve',owned,'--attempt',attempt_id,
                                       '--outcome','applied','--reason','Synchronous fixture host returned; exact bounded local effects inspected and own environment cleaned/reconciled; code preserved, no broader action.')
                clean(binary,authority,runs)
                assert not any(c['status']=='active' for c in verify.run(binary,'--project',authority,'claim','list')['claims'])
            finally:verify.forget_authority(authority)


def main():
    if not __debug__:raise RuntimeError('Verification requires enabled assertions')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--binary',type=Path,required=True);parser.add_argument('--case',choices=CASES);parser.add_argument('--browser-library',type=Path);parser.add_argument('--report',type=Path)
    parser.add_argument('--live-mode',choices=('direct','repair','resume','frontend'));parser.add_argument('--live-skills',type=Path);parser.add_argument('--artifacts',type=Path)
    args=parser.parse_args();results=[]
    if args.live_mode:
        if args.case or not args.live_skills or not args.artifacts:parser.error('Live qualification requires --live-skills and --artifacts, without --case')
        if args.live_mode=='frontend' and not args.browser_library:parser.error('Frontend live qualification requires --browser-library')
        args.artifacts.mkdir(parents=True,exist_ok=True)
        cases=({'direct':'backend','repair':'live-repair','resume':'live-resume','frontend':'live-frontend'}[args.live_mode],)
    else:
        cases=(args.case,) if args.case else ('frontend','repair-ui','repair-ux') if args.browser_library else CASES
        if args.artifacts:args.artifacts.mkdir(parents=True,exist_ok=True)
    for case in cases:
        item=run_case(args.binary,case,library=args.browser_library,live=bool(args.live_mode),artifacts=args.artifacts,skills=args.live_skills);results.append(item)
        print(json.dumps({k:v for k,v in item.items() if k not in ('observations','outputs','rounds','plan_captures','browser_observations')}),flush=True)
    if not args.case and not args.browser_library and not args.live_mode:
        for host in ('codex-app','claude-code'):
            item=run_case(args.binary,'backend',host);results.append(item);print(json.dumps(item),flush=True)
    if args.report:args.report.write_text(json.dumps({'prifly':verify.run(args.binary,'version')['version'],'binary_sha256':hashlib.sha256(args.binary.read_bytes()).hexdigest(),'cases':results},indent=2)+'\n')


if __name__=='__main__':main()
