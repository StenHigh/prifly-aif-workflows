#!/usr/bin/env python3
"""Whole shipping parallel-ui-ux feature: real browser/native gates, opt-in LLMs.

Synthetic reports are explicitly labelled; --live-skills runs the shipped
dispatcher with original independent CLI submissions and actual image tools.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
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
from feature_check import FeatureHost, run_case
from evidence_check import read
from fix_check import implementation
from run_check import clean
from parallel_check import invoke, submission as late_submission
from test_review_evidence import report
import verify
sys.path.insert(0, str(verify.ROOT / 'aif-feature/files'))
import parallel_host as controller
import frontend_host as frontend
import browser_contract as browser

CASES = {
    'frontend': ('frontend', None, None, 'succeeded'),
    'repair-ui': ('repair-ui', None, None, 'succeeded'),
    'repair-ux': ('repair-ux', None, None, 'succeeded'),
    'repair-checks': ('repair-checks', None, None, 'succeeded'),
    'required-unavailable': ('required-unavailable', None, None, 'partial'),
    'owner-stop': ('owner-stop', None, None, 'partial'),
    'last-round': ('exhaustion', None, None, 'partial'),
    'max-budget': ('max-budget', None, None, 'partial'),
    'cancel-before': ('frontend-cancel', 'cancel-before', None, 'succeeded'),
    'cancel-after-first': ('frontend-cancel', 'cancel-after-first', None, 'succeeded'),
    'cancel-during-browser': ('frontend-cancel', 'cancel-browser', 'hold-browser', 'succeeded'),
    'one-timeout': ('frontend-cancel', 'one-timeout', None, 'succeeded'),
    'commit-replay': ('commit-resume', None, None, 'succeeded'),
    'evaluate-failure': ('frontend', 'evaluate-failure', None, 'partial'),
    'intervening-edit': ('stale-after-review', 'intervening-edit', None, 'partial'),
    'stale-after-repair': ('repair-ui', 'stale-after-repair', None, 'partial'),
    **{name: ('frontend', name, None, 'partial') for name in ('wrong-origin', 'shared-session', 'bad-digest', 'missing-report', 'stale-bundle')},
    **{name: ('frontend', None, name, 'partial') for name in ('missing-environment', 'runtime-browser-unavailable', 'wrong-cleanup-owner', 'cleanup-interrupted')},
    **{name: ('frontend', name, name if name in ('unsupported-browser', 'shared-context', 'shared-identity') else None, 'rejected')
       for name in ('unsupported-host', 'unsupported-browser', 'shared-context', 'shared-identity', 'shared-resource', 'capacity-one', 'source-drift', 'no-adapter')},
}


class UIUXHost(FeatureHost):
    def __init__(self, *args, fault=None, live_readers=False, launch_host='codex-cli', **kwargs):
        super().__init__(*args, **kwargs)
        self.fault, self.live_readers, self.launch_host = fault, live_readers, launch_host
        self.evidence_root = self.artifacts or self.root / 'uiux-evidence'
        self.evidence_root.mkdir(parents=True, exist_ok=True)
        self.pairs, self.reader_observations, self.teardown = [], [], []
        self.saved_reports = None
        self.adapter_path = self.root / 'browser-adapter.json'
        self.adapter = json.loads(self.adapter_path.read_text()) if self.adapter_path.exists() else None

    def cancel_and_cleanup(self, rid, journal_path):
        self.call('run', 'cancel', rid, '--reason', 'Owned frontend qualification cancellation')
        self.call('run', 'drive', rid)
        assert self.state(rid)['status'] == 'cancelled'
        assert all(a.get('settled') for a in self.state(rid)['attempts'].values())
        value = frontend.cleanup(self.binary, self.authority, journal_path)
        assert value['status'] == 'released', value
        self.cancelled = True

    def observe_pair(self, tasks, journal_path, journal):
        frontend.exclusive(journal_path.with_suffix('.actors'), ','.join(t['attempt_id'] for t in tasks))
        journal['actor_phase'] = 'active'; frontend.save(journal_path, journal)
        observations, timing = {}, {}
        def observe(task):
            started = time.monotonic()
            value = frontend.observe(task, Path(task['workspace']) / 'browser')
            return controller.role(task), value, started, time.monotonic()
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(observe, t) for t in tasks]
                if self.fault == 'cancel-browser' and not self.cancelled:
                    folder = Path(tasks[1]['workspace']) / 'browser'; deadline = time.monotonic() + 15
                    while not (folder / 'browser-active').exists():
                        assert time.monotonic() < deadline and not futures[1].done(), 'Browser did not reach owned active context'
                        time.sleep(.05)
                    self.call('run', 'cancel', tasks[0]['run_id'], '--reason', 'Cancel while owned browser context is active')
                    self.call('run', 'drive', tasks[0]['run_id'])
                    assert self.state(tasks[0]['run_id'])['status'] == 'cancelled'
                    assert not futures[1].done(), 'Actor was not alive at native cancellation'
                    (folder / 'browser-stop').write_text('Stop only this fixture actor\n')
                    for future in futures:
                        try: future.result()
                        except ValueError as error: assert 'Owned browser stopped' in str(error)
                    Path(self.adapter['settings']['control_release']).write_text('Owner provided fixture continuation prerequisite\n')
                    self.cancelled = True
                    return None
                for future in futures:
                    lens, value, start, end = future.result(); observations[lens] = value; timing[lens] = (start, end)
            overlap = min(t[1] for t in timing.values()) - max(t[0] for t in timing.values())
            assert overlap > 0
            self.pairs[-1]['browser_work_overlap_seconds'] = overlap
            return observations
        finally:
            journal['actor_phase'] = 'settled'; frontend.save(journal_path, journal)

    def pair(self, rid, tasks):
        tasks.sort(key=lambda t: browser.READERS.index(controller.role(t)))
        assert [controller.role(t) for t in tasks] == list(browser.READERS)
        assert len({t['attempt_id'] for t in tasks}) == len({t['workspace'] for t in tasks}) == 2
        assert len({t['claim_id'] for t in tasks}) == 1
        assert read(tasks[0], 'candidate') == read(tasks[1], 'candidate')
        bindings = {controller.role(t): frontend.validate_reader(t) for t in tasks}; browser.distinct(bindings)
        path, journal = frontend.journal_for(tasks[0], self.evidence_root)
        row = {'run': rid, 'round': read(tasks[0], 'request')['round'], 'candidate': read(tasks[0], 'candidate'),
            'attempts': [t['attempt_id'] for t in tasks], 'browser_sessions': bindings, 'environment': read(tasks[0], 'environment')}
        self.pairs.append(row)
        self.tree = Path(tasks[0]['repository_workspace']); self.claims.add(tasks[0]['claim_id'])
        for task in tasks:
            lens = controller.role(task); request = read(task, 'request')
            self.seen.append({'run': rid, 'step': lens})
            self.rounds.append({'run': rid, 'lens': lens, 'round': request['round'], 'digest': row['candidate']['digest'], 'base': self.base})
        if self.fault == 'cancel-before' and not self.cancelled:
            self.cancel_and_cleanup(rid, path)
            return
        if self.live_readers:
            value = controller.service(self.binary, self.authority, tasks, host='codex-cli', artifacts=self.evidence_root)
            self.reader_observations.extend(value['observations'])
            return
        observations = self.observe_pair(tasks, path, journal)
        if observations is None:
            value = frontend.cleanup(self.binary, self.authority, path); assert value['status'] == 'released'
            row['cancelled_while_browser_active'] = True
            return
        row['browser_observations'] = observations
        values = {}
        for task in tasks:
            lens = controller.role(task); request = read(task, 'request'); observed = observations[lens]
            value = report(request, row['candidate']); value.update(session='separate', request_digest=task['context']['inputs']['request']['ref']['digest'])
            checks = []
            for check in request['checks']:
                entry = {'id': check['id'], 'status': 'executed', 'result': 'passed', 'reason': '', 'evidence': []}
                if observed['status'] != 'ready':
                    entry.update(status='unavailable', result='not_run', reason=observed['reason'])
                else:
                    ids = {s['id'] for s in read(task, 'configuration')['scenarios'] if s['lens'] == lens and s['check_id'] == check['id']}
                    items = [item for item in observed['observations'] if item['scenario'] in ids]
                    failures = [f for item in items for f in item['failures']]
                    entry.update(result='failed' if failures else 'passed', reason='; '.join(failures), evidence=[
                        {'method': 'browser', 'tool': observed['tool'], 'locator': item['url'],
                         'observation': json.dumps({k: item[k] for k in ('scenario', 'viewport', 'url', 'observations')}), 'exit_code': None} for item in items])
                checks.append(entry)
            value['checks'] = checks
            if lens == 'ui' and self.fault == 'shared-session': value['session'] = 'shared'
            if lens == 'ui' and self.fault == 'wrong-origin':
                item = checks[0]['evidence'][0]; observation = json.loads(item['observation']); observation['url'] = 'http://127.0.0.1:1/index.html'; item['observation'] = json.dumps(observation)
            if lens == 'ui' and self.fault == 'stale-after-repair' and self.saved_reports: value = self.saved_reports[lens]
            values[lens] = value
        if self.saved_reports is None: self.saved_reports = copy.deepcopy(values)
        if self.fault == 'one-timeout' and not self.cancelled:
            time.sleep(31); self.call('run', 'drive', rid)
            assert [controller.role(t) for t in self.call('session','task','--run',rid,'--all')['tasks']] == ['ux']
            assert self.submit(rid, tasks[1], 'pass', {'report': values['ux']}) is None
            self.cancelled = True
            row['timeout_waited_for_sibling'] = True
            return
        for task in tasks:
            lens = controller.role(task)
            assert self.submit(rid, task, 'pass', {'report': values[lens]}) is None
            if lens == 'ui':
                self.call('run', 'drive', rid)
                outstanding = self.call('session', 'task', '--run', rid, '--all')['tasks']
                assert [controller.role(t) for t in outstanding] == ['ux'], 'Early repair/release before all-join'
                if self.fault == 'cancel-after-first' and not self.cancelled:
                    late = late_submission(self.call, rid, tasks[1], values['ux'])
                    self.cancel_and_cleanup(rid, path)
                    refused = invoke(self.binary, self.authority, 'session', 'submit', '--file', late)
                    assert refused['exit'] or refused['rejection'], 'Late report accepted after cancellation'
                    return
        if self.fault == 'intervening-edit': (self.tree / 'owner.txt').write_text('Owner edit after both UI/UX reports\n')

    def drive_feature(self, rid):
        self.run_ids.append(rid)
        for _ in range(150):
            self.call('run', 'drive', rid)
            tasks = self.call('session', 'task', '--run', rid, '--all')['tasks']
            if not tasks: return self.state(rid)
            roles = [controller.role(t) for t in tasks]
            if len(tasks) == 2:
                self.pair(rid, tasks)
                if self.state(rid)['status'] == 'cancelled': return self.state(rid)
                continue
            assert len(tasks) == 1
            task = tasks[0]; name = roles[0]
            if name is None: name = task['skill_refs'][0]['id'].rsplit('/',1)[-1].removesuffix('-bridge')
            self.seen.append({'run': rid, 'step': name})
            if task.get('repository_workspace'): self.tree = Path(task['repository_workspace'])
            if task.get('claim_id'): self.claims.add(task['claim_id'])
            if name == 'parallel-admission' and not self.live_readers:
                controller.verify_adapter(task)
                value = {'protocol': controller.PROTOCOL, 'status': 'ready', 'host': 'codex-cli',
                    'reason': 'Synthetic independent-session capability; real browser/source/resource admission checked separately'}
                try:
                    if self.launch_host != 'codex-cli': raise ValueError('Unsupported independent session host')
                    frontend.admit(self.binary, self.authority, task, self.evidence_root)
                except (ValueError, OSError, subprocess.SubprocessError) as error:
                    value.update(status='unavailable', reason=str(error))
                controller.submit_values(self.binary, self.authority, task, {'admission': value})
            elif name in ('parallel-admission', 'frontend-environment', 'frontend-release', 'collect-uiux'):
                if name == 'collect-uiux' and self.fault in ('bad-digest','missing-report','stale-bundle'):
                    bundle = controller.collect(self.binary, self.authority, task, browser.READERS)
                    if self.fault == 'bad-digest': bundle['reports'][0]['raw_base64'] = 'e30='
                    if self.fault == 'missing-report': bundle['reports'] = bundle['reports'][:1]
                    if self.fault == 'stale-bundle': bundle['manifest_digest'] = 'sha256:' + '0'*64
                    controller.submit_values(self.binary, self.authority, task, {'bundle': bundle})
                else: controller.service(self.binary, self.authority, tasks, host=self.launch_host, artifacts=self.evidence_root)
            else:
                verdict, values = self.answer_feature(task, name)
                if name == 'repair':
                    path = self.tree / 'index.html'; path.write_text(path.read_text() + '\n<!-- repair round ' + str(len(self.pairs)) + ' -->\n')
                    values['implementation'] = implementation(self.tree, self.base)
                assert self.submit(rid, task, verdict, values) is None
        raise AssertionError('Frontend feature did not settle')

    def extra_result(self):
        journals = [json.loads(p.read_text()) for p in (self.evidence_root / 'frontend').glob('*/*.json')]
        return {'mode': 'Synthetic author/checks/code readers, actual independent CLI UI/UX with unedited submissions' if self.live_readers else
            'Synthetic model/session reports, actual concurrent Chromium/native feature/program/cleanup/commit',
            'uiux_pairs': self.pairs, 'uiux_reader_observations': self.reader_observations, 'environment_journals': journals,
            'fixture_teardown': self.teardown, 'actual_independent_llm_sessions': len(self.reader_observations)}

    def cleanup_fixture(self):
        # Test-owned teardown only. It never changes a failed Run to success or
        # provides consumer recovery for unknown production external effects.
        if not self.adapter: return
        root = Path(self.adapter['settings']['state_root'])
        if not root.is_dir(): return
        for path in root.glob('environment-*.json'):
            state = json.loads(path.read_text())
            lease = root / ('owner-' + hashlib.sha256(state['owner'].encode()).hexdigest()[:24] + '.lease')
            if not lease.exists(): continue
            assert path.parent == self.root / 'environment-state'
            env = {'owner': state['owner'], 'session': state['session'], 'url': state['url']}
            config = {'environment': {'owner': state['owner']}}
            value = frontend.release_value(self.adapter, config, env)
            if value['status'] == 'reconcile_required': value = frontend.release_value(self.adapter, config, env)
            assert value['status'] == 'released', value
            self.teardown.append({'session': state['session'], 'status': value['status'], 'scope': 'owned fixture finalizer; original native outcome retained'})
        assert not list(root.glob('*.lease'))


def check(binary, name, library, skills=None, artifacts=None):
    case, fault, adapter_fault, expected = CASES[name]
    launch_host = 'claude-code' if name == 'unsupported-host' else 'codex-cli'
    def adapter_factory(root, repository, package):
        if name == 'no-adapter': return None
        bundle = root / 'browser-adapter'; shutil.copytree(verify.ROOT/'tests/fixtures/feature-browser', bundle)
        settings = {'library': str(library.resolve()), 'node': shutil.which('node'), 'state_root': str(root/'environment-state'),
                    'fault': adapter_fault, 'control_release': str(root/'browser-continue-ready')}
        value = {'protocol': browser.PROTOCOL, 'root': str(bundle), 'entrypoint': 'adapter.py',
            'files': {p.name: controller.w1.digest(p.read_bytes()) for p in bundle.iterdir() if p.is_file()}, 'settings': settings}
        if name == 'source-drift': value['files']['adapter.py'] = 'sha256:' + '0'*64
        (root/'browser-adapter.json').write_text(json.dumps(value))
        if name == 'capacity-one':
            path=package/'extend.yaml'; path.write_text(path.read_text()+'resources:\n  fixture-stand:\n    limit: 1\n    stages: [quality]\n')
        if fault == 'one-timeout':
            path=package/'steps/parallel-ui.yaml';path.write_text(path.read_text().replace('active_timeout_ms: null','active_timeout_ms: 30000'))
        if fault == 'evaluate-failure':
            # Fail only the pure program executor; source/adapter pins stay exact.
            path=package/'workflow.yaml'
            text=path.read_text();marker='    aif-feature:step/evaluate-uiux:';start=text.index(marker);end=text.find('\n    aif-',start+len(marker))
            if end<0:end=len(text)
            text=text[:start]+text[start:end].replace('timeout_ms: 120000','timeout_ms: 1')+text[end:];path.write_text(text)
        return value
    def factory(*args, **kwargs): return UIUXHost(*args, fault=fault, live_readers=bool(skills), launch_host=launch_host, **kwargs)
    def mutate(task):
        if name == 'shared-resource': task['product']['environment']['shared_resource'] = 'fixture-stand'
        if name == 'owner-stop':
            for lens in browser.READERS: task['product'][lens]['optional_policy'] = 'stop'
    row = run_case(binary, case, host=launch_host, library=library, review_mode='parallel-ui-ux', parallel_live=bool(skills),
        skills=skills, artifacts=artifacts, host_factory=factory, adapter_factory=adapter_factory, task_mutator=mutate, expected_outcome=expected)
    row['scenario'] = name
    if expected == 'rejected': assert not {'plan','implement','repair','commit'} & set(row['steps']) and not row['uiux_pairs']
    if expected == 'partial' and case not in ('exhaustion','max-budget','repair-ui'):
        assert 'repair' not in row['steps'] and 'commit' not in row['steps']
    if name in ('repair-ui','repair-ux','repair-checks','stale-after-repair','commit-replay'):
        assert len(row['uiux_pairs']) == 2
        a,b = row['uiux_pairs']
        assert a['candidate'] != b['candidate'] and a['environment']['session'] != b['environment']['session']
        assert not set(a['attempts']) & set(b['attempts'])
    if name == 'stale-after-repair': assert row['parallel_outputs']['gate']['status'] == 'blocked'
    if name == 'one-timeout': assert row['source_outcome'] == 'partial' and row['outcome'] == 'succeeded'
    if skills:
        observations = row['uiux_reader_observations']; assert len(observations) >= 2
        assert len({o['session_id'] for o in observations}) == len(observations)
        for i in range(0,len(observations),2):
            overlap=min(o['ended_monotonic'] for o in observations[i:i+2])-max(o['started_monotonic'] for o in observations[i:i+2])
            assert overlap > 0
            row['uiux_pairs'][i//2]['actual_reader_turn_overlap_seconds'] = overlap
    return row


def main():
    if not __debug__: raise RuntimeError('Qualification requires assertions')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',type=Path,required=True);parser.add_argument('--browser-library',type=Path,required=True)
    group=parser.add_mutually_exclusive_group();group.add_argument('--case',choices=CASES);group.add_argument('--cases',choices=CASES,nargs='+')
    parser.add_argument('--jobs',type=int,choices=(1,2,3),default=1);parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--live-skills',type=Path);parser.add_argument('--artifacts',type=Path)
    args=parser.parse_args()
    if args.live_skills and (args.case not in ('frontend','repair-ui','repair-ux') or not args.artifacts or args.jobs!=1):
        parser.error('Actual UI/UX sessions require one normal/repair case, owned artifacts and --jobs 1')
    if args.artifacts: args.artifacts.mkdir(parents=True,exist_ok=True)
    selected=[args.case] if args.case else args.cases or list(CASES)
    result={'prifly':verify.run(args.binary,'version')['version'],'binary_sha256':hashlib.sha256(args.binary.read_bytes()).hexdigest(),
        'cases':[],'matrix_complete':False,'scope':'Whole shipping feature, separate sealed browser grants; '+('actual fresh CLI UI/UX' if args.live_skills else 'deterministic reports, no LLM independence claimed')}
    def record(row):
        result['cases'].append(row);args.report.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'scenario':row['scenario'],'source_outcome':row['source_outcome'],'outcome':row['outcome'],
            'pairs':len(row['uiux_pairs']),'actual_llm_sessions':row['actual_independent_llm_sessions'],'cleaned':row['cleaned']}),flush=True)
    def isolated(name):
        with tempfile.TemporaryDirectory(prefix='w5-feature-uiux-job-') as directory:
            root=Path(directory);env=os.environ.copy()
            # Preserve the parent's installed browser cache before HOME isolation.
            if not env.get('PLAYWRIGHT_BROWSERS_PATH'):
                cache=Path.home()/'Library/Caches' if sys.platform=='darwin' else Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData/Local')) if sys.platform=='win32' else Path(os.environ.get('XDG_CACHE_HOME',Path.home()/'.cache'))
                env['PLAYWRIGHT_BROWSERS_PATH']=str(cache/'ms-playwright')
            env.update(HOME=str(root),XDG_CONFIG_HOME=str(root/'config'))
            report_file=root/'result.json'
            proc=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--binary',str(args.binary.resolve()),
                '--browser-library',str(args.browser_library.resolve()),'--case',name,'--report',str(report_file)],env=env,capture_output=True,text=True,timeout=1800)
            assert proc.returncode==0,(name,proc.stdout,proc.stderr)
            value=json.loads(report_file.read_text());assert value['matrix_complete'];return value['cases'][0]
    if args.jobs==1:
        for name in selected: record(check(args.binary.resolve(),name,args.browser_library,args.live_skills,args.artifacts))
    else:
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures=[pool.submit(isolated,name) for name in selected]
            try:
                for future in as_completed(futures): record(future.result())
            except BaseException:
                for future in futures: future.cancel()
                raise
    result['matrix_complete']=True;args.report.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__': main()
