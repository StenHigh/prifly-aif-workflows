#!/usr/bin/env python3
"""W5 native parallel UI/UX + actual Chromium; deterministic reports, no LLM.

All authority changes and submissions are serial. Only browser work overlaps.
Environment ownership is independent of native Git/resource claims; technical
stop has no automatic cleanup tail. The controller settles its own actors first.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import errno
import functools
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify
from parallel_product_fixture import install
from parallel_product_environment import ProductHandler
from product_environment import OwnedEnvironment, LifecycleError
from evidence_check import read
from parallel_check import invoke
from run_check import clean, git_out
from test_product_review import configuration, p
from test_review_evidence import report

CASES = ('pass', 'defect-repair', 'cancel-before', 'cancel-after-first', 'cancel-during-browser',
         'one-timeout', 'intervening-edit', 'stale-report-after-repair', 'wrong-origin',
         'shared-stand', 'ports', 'port-conflict', 'shared-context-refused', 'shared-identity-refused',
         'wrong-cleanup-owner', 'cleanup-interrupted', 'missing-browser')


def submit(call, rid, task, values, *, raw=False):
    template = call('session', 'submit', '--template', '--run', rid, '--attempt', task['attempt_id'])
    for port, value in values.items():
        data = value if raw else json.dumps(value).encode()
        output = Path(task['workspace']) / task['context']['outputs'][port]['path']
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        template['result']['outputs'][port]['digest'] = p.w1.digest(data)
    template['result'].update(verdict='pass', summary='W5 qualification controller; deterministic reports, no LLM judgement.')
    template['answered_questions'] = []
    if 'model_profile' in template:
        template['model_profile'] = {'outcome': 'unavailable', 'reason': 'Deterministic browser fixture, no model invoked.'}
    file = Path(task['workspace']) / 'qualification-submission.json'
    file.write_text(json.dumps(template))
    call('session', 'submit', '--file', file)
    return file


def export(call, root, ref, name):
    ref_file, output = root / (name + '-ref.json'), root / (name + '.json')
    ref_file.write_text(json.dumps(ref))
    call('artifact', 'export', '--ref', ref_file, '--output', output)
    data = output.read_bytes()
    assert p.w1.digest(data) == ref['digest']
    return data


def port_closed(url):
    from urllib.parse import urlsplit
    with socket.socket() as client:
        client.settimeout(1)
        return client.connect_ex(('127.0.0.1', urlsplit(url).port)) != 0


class Fixture:
    def __init__(self, binary, root, case, library, host):
        self.binary, self.root, self.case, self.library, self.host = binary, root, case, library, host
        self.repo, self.authority = verify.prepare_repository(binary, root)
        self.runs, self.envs, self.actors, self.rounds, self.provenance = [], [], [], [], []
        self.package = install(self.repo, timeout=30000 if case == 'one-timeout' else None)
        if case == 'shared-stand':
            (self.package / 'extend.yaml').write_text('resources:\n  fixture-stand:\n    limit: 1\n    stages: [quality]\nextensions: []\n')
        html = (verify.ROOT / 'tests/fixtures/product/index.html').read_text()
        # The fixture form writes data through an identity-scoped local API.
        html = html.replace("document.querySelector('#success').textContent='Saved: '+note.value.trim();",
            "fetch('/notes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:note.value.trim()})});\n document.querySelector('#success').textContent='Saved: '+note.value.trim();")
        self.good_html = html
        if case in ('defect-repair', 'stale-report-after-repair'):
            html = html.replace('/* DEFECT_OVERFLOW */', 'section { min-width:800px; }').replace('/* DEFECT_FLOW */', 'return;')
        (self.repo / 'index.html').write_text(html)
        (self.repo / 'owner.txt').write_text('Preserve unrelated owner work.\n')
        verify.git('-C', self.repo, 'add', '.')
        verify.git('-C', self.repo, 'commit', '-qm', 'Parallel product qualification')
        self.base = git_out(self.repo, 'rev-parse', 'HEAD')
        self.config = configuration(self.base)
        self.config['ui']['checks'][0]['description'] = 'At desktop/mobile: no horizontal overflow, heading Notes, label Note text and isolated empty state. DOM metrics only; no visual judgement.'
        for scene in self.config['scenarios']:
            if scene['lens'] == 'ui': scene['expectations'] = ['No horizontal overflow; known heading/label and isolated empty state']
        self.config['environment']['test_identity'] = 'Fixture-issued unique cookie per Attempt; no real account or shared data.'
        if case == 'shared-stand': self.config['environment']['shared_resource'] = 'fixture-stand'
        self.input = root / 'configuration.json'; self.input.write_text(json.dumps(self.config))
        self.call('project', 'local', 'set', '--repository', self.repo, '--allow-executable', 'python=' + str(Path(sys.executable).resolve()))
        self.args = ('project', 'start', '--repository', self.repo, '--launch', 'parallel-product', '--host', host,
                     '--workspace', 'worktree', '--input', 'configuration=' + str(self.input), '--allow-execution')
        prepared = self.call('project', 'questionnaire', *self.args[2:], '--prepare')
        self.launch_digest = prepared['review_digest']
        self.rid = self.call(*self.args, '--expected-launch-digest', self.launch_digest)['run']['run']['id']
        self.runs.append(self.rid)
        self.current = None; self.tree = None; self.old_reports = None; self.cancelled = False
        self.notes, self.identities, self.lock = {}, set(), threading.Lock()
        self.refusals = []

    def call(self, *args, **kwargs): return verify.run(self.binary, '--project', self.authority, *args, **kwargs)
    def state(self, rid): return self.call('run', 'status', rid)['run']
    def tasks(self, rid): return self.call('session', 'task', '--run', rid, '--all')['tasks']

    def cleanup_environment(self, env):
        url = env.url
        env.close()
        assert not env.lease.exists() and env.server is None and port_closed(url)

    def cancel(self, rid):
        self.call('run', 'cancel', rid, '--reason', 'Owned W5 browser qualification stop')
        self.call('run', 'drive', rid)
        state = self.state(rid)
        assert state['status'] == 'cancelled', state['status']
        assert all(a.get('settled') for a in state['attempts'].values())
        assert self.current.server is not None and self.current.lease.exists(), 'Native cancellation must not pretend external cleanup'
        self.cancelled = True

    def environment(self, rid, task, iteration):
        self.tree = Path(task['repository_workspace'])
        cfg, basis = read(task, 'configuration'), read(task, 'candidate')
        self.current = OwnedEnvironment(self.root / 'environment-state', self.tree, cfg['environment']['owner'],
            profile=cfg['environment']['profile'], shared=cfg['environment']['shared_resource'],
            handler=functools.partial(ProductHandler, identities=self.identities, notes=self.notes, lock=self.lock))
        self.envs.append(self.current); url = self.current.ensure()
        data_before = json.dumps(self.notes, sort_keys=True)
        for request in (url + '/whoami', Request(url + '/notes', data=b'{"text":"foreign"}', method='POST')):
            try:
                with urlopen(request, timeout=5): pass
            except HTTPError as error: assert error.code == 403
            else: raise AssertionError('unissued fixture identity received data access')
        assert json.dumps(self.notes, sort_keys=True) == data_before
        if self.case == 'port-conflict':
            # Own a foreign-to-the-environment listener; never evict it.
            with socket.socket() as foreign:
                foreign.bind(('127.0.0.1', 0)); foreign.listen()
                port = foreign.getsockname()[1]
                contender = OwnedEnvironment(self.root / 'environment-state', self.tree, 'port-contender', port=port)
                try: contender.ensure()
                except OSError as error: assert error.errno == errno.EADDRINUSE, error
                else: raise AssertionError('occupied port silently replaced or remapped')
                assert not contender.lease.exists() and contender.server is None
                assert not port_closed('http://127.0.0.1:' + str(port))
                assert self.current.server is not None
        if self.case == 'shared-stand' and iteration == 0:
            # Native admission and external lease both refuse a second owner.
            refused = self.call(*self.args, '--expected-launch-digest', self.launch_digest, expect_ok=False)
            assert 'resource_busy' in refused, refused
            other_runs = [r['run_id'] for r in self.call('run', 'list')['runs'] if r['run_id'] not in self.runs]
            assert len(other_runs) == 1
            self.runs.extend(other_runs)
            assert not self.tasks(other_runs[0])
            other = OwnedEnvironment(self.root / 'environment-state', self.tree, 'other-owner', shared='fixture-stand')
            try: other.ensure()
            except LifecycleError as error: assert 'owner_required' in str(error)
            else: raise AssertionError('second external stand owner admitted')
            assert self.current.server is not None and self.current.lease.exists()
        if self.case == 'ports':
            other = OwnedEnvironment(self.root / 'environment-state', self.tree, 'other-owned-port')
            self.envs.append(other); other.ensure()
            assert other.url != url
            self.cleanup_environment(other)
            assert self.current.server is not None and not port_closed(url)
        value = {'status': 'ready', 'owner': cfg['environment']['owner'], 'profile': cfg['environment']['profile'],
            'configuration_digest': task['context']['inputs']['configuration']['ref']['digest'],
            'candidate_digest': basis['digest'], 'session': self.current.session, 'url': url, 'reason': ''}
        submit(self.call, rid, task, {'environment': value})

    def browsers(self, rid, tasks, iteration):
        tasks.sort(key=lambda t: t['skill_refs'][0]['id'])
        assert len(tasks) == len({t['attempt_id'] for t in tasks}) == len({t['workspace'] for t in tasks}) == 2
        assert len({t['claim_id'] for t in tasks}) == 1
        assert read(tasks[0], 'candidate') == read(tasks[1], 'candidate')
        assert read(tasks[0], 'environment') == read(tasks[1], 'environment')
        record = {'iteration': iteration, 'candidate': read(tasks[0], 'candidate'), 'attempts': [t['attempt_id'] for t in tasks],
            'environment': read(tasks[0], 'environment'), 'reports': {}}
        self.rounds.append(record)
        before = p.w1.snapshot(self.tree, self.base)
        if iteration == 0 and self.case == 'cancel-before':
            self.cancel(rid); self.cleanup_environment(self.current); return False
        out = self.root / ('browser-' + str(iteration)); out.mkdir()
        readers = []
        for lens, task in zip(p.LENSES, tasks):
            token = uuid.uuid4().hex; self.identities.add(token)
            task_file = out / (lens + '-task.json'); task_file.write_text(json.dumps(task))
            readers.append({'lens': lens, 'identity': token, 'task': str(task_file)})
        spec = {'context_mode': 'isolated', 'readers': readers}
        if self.case == 'shared-identity-refused': readers[1]['identity'] = readers[0]['identity']
        if self.case == 'shared-context-refused': spec['context_mode'] = 'shared'
        if self.case == 'cancel-during-browser' and iteration == 0: spec['hold_lens'] = 'ux'
        pair_file = out / 'pair.json'; pair_file.write_text(json.dumps(spec))
        observations = None
        if self.case != 'missing-browser':
            command = ['node', str(Path(__file__).with_name('parallel_product_browser.cjs')), str(self.library), str(pair_file), str(out)]
            if spec.get('hold_lens'):
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
                self.actors.append((process, out))
                deadline = time.monotonic() + 25
                while not (out / 'browser-active').exists():
                    assert process.poll() is None, process.communicate()
                    assert time.monotonic() < deadline, 'owned browser readiness timeout'
                    time.sleep(.05)
                self.cancel(rid)
                assert process.poll() is None and self.current.server is not None
                (out / 'stop').write_text('Stop only this owned browser actor.\n')
                _, stderr = process.communicate(timeout=20)
                assert process.returncode != 0 and 'owned browser actor stopped' in stderr, stderr
                assert self.current.server is not None, 'cleanup occurred before actor settlement'
                self.cleanup_environment(self.current)
                record['cancelled_while_browser_active'] = True
                return False
            proc = subprocess.run(command, capture_output=True, text=True, timeout=90)
            if self.case in ('shared-context-refused', 'shared-identity-refused'):
                assert proc.returncode != 0 and ('contexts required' in proc.stderr or 'identities required' in proc.stderr), proc.stderr
                assert not self.notes and not (out / 'observations.json').exists()
                self.cancel(rid); self.cleanup_environment(self.current)
                record['unsafe_adapter_refused_before_browser_operations'] = True
                return False
            assert proc.returncode == 0, proc.stderr
            observations = json.loads(proc.stdout)
            assert observations['overlap_ms'] > 0 and len({r['context_id'] for r in observations['readers']}) == 2
            record['browser'] = observations
        values = {}
        for lens, task in zip(p.LENSES, tasks):
            rq, basis = read(task, 'request'), read(task, 'candidate')
            value = report(rq, basis); value['request_digest'] = task['context']['inputs']['request']['ref']['digest']
            check = value['checks'][0]; check['id'] = lens + '_acceptance'
            if observations is None:
                check.update(status='unavailable', result='not_run', reason='Declared browser adapter unavailable; no code substitution', evidence=[])
            else:
                row = next(r for r in observations['readers'] if r['lens'] == lens)
                failures = [f for scene in row['observations'] for f in scene['failures']]
                check.update(result='failed' if failures else 'passed', reason='; '.join(failures), evidence=[
                    {'method': 'browser', 'tool': observations['tool'], 'locator': scene['url'],
                     'observation': json.dumps({k: scene[k] for k in ('scenario', 'viewport', 'url', 'observations')}), 'exit_code': None}
                    for scene in row['observations']])
            if self.case == 'wrong-origin' and lens == 'ui':
                item = check['evidence'][0]; obs = json.loads(item['observation']); obs['url'] = 'http://127.0.0.1:1/index.html'
                item['observation'] = json.dumps(obs)
            if self.case == 'stale-report-after-repair' and iteration == 1 and lens == 'ui': value = self.old_reports[lens]
            values[lens] = value; record['reports'][lens] = value
        if iteration == 0: self.old_reports = values
        if self.case == 'one-timeout' and iteration == 0:
            # Prepare late bytes while the UI Attempt still exists.
            ui_template = self.call('session', 'submit', '--template', '--run', rid, '--attempt', tasks[0]['attempt_id'])
            output = Path(tasks[0]['workspace']) / tasks[0]['context']['outputs']['report']['path']
            raw = json.dumps(values['ui']).encode(); output.parent.mkdir(parents=True, exist_ok=True); output.write_bytes(raw)
            ui_template['result']['outputs']['report']['digest'] = p.w1.digest(raw)
            ui_template['result'].update(verdict='pass', summary='Late deterministic report')
            ui_template['answered_questions'] = []; ui_template['model_profile'] = {'outcome': 'unavailable', 'reason': 'Fixture'}
            late = self.root / 'late.json'; late.write_text(json.dumps(ui_template))
            time.sleep(31)
            self.call('run', 'drive', rid)
            assert [t['attempt_id'] for t in self.tasks(rid)] == [tasks[1]['attempt_id']]
            assert self.current.server is not None
            submit(self.call, rid, tasks[1], {'report': values['ux']})
            self.call('run', 'drive', rid)
            state = self.state(rid)
            assert state['outcome'] == 'rejected' and all(a.get('settled') for a in state['attempts'].values())
            assert 'attempt_deadline_expired' in [d['code'] for d in state['diagnostics']]
            refused = invoke(self.binary, self.authority, 'session', 'submit', '--file', late)
            assert refused['exit'] or refused['rejection']
            self.cleanup_environment(self.current)
            record['timeout_waited_for_sibling'] = True
            return False
        for lens, task in zip(p.LENSES, tasks):
            file = submit(self.call, rid, task, {'report': values[lens]})
            if lens == 'ui':
                self.call('run', 'drive', rid)
                assert [t['attempt_id'] for t in self.tasks(rid)] == [tasks[1]['attempt_id']], 'join ran before last reader'
                assert self.current.server is not None
                if self.case == 'cancel-after-first' and iteration == 0:
                    # Prepare an exact sibling submission before cancellation.
                    template = self.call('session', 'submit', '--template', '--run', rid, '--attempt', tasks[1]['attempt_id'])
                    self.cancel(rid)
                    template['result']['verdict'] = 'no_work'; template['result']['summary'] = 'Late cancelled reader'; template['result']['outputs'] = {}
                    template['answered_questions'] = []; template['model_profile'] = {'outcome': 'unavailable', 'reason': 'Fixture'}
                    late = self.root / 'late-cancel.json'; late.write_text(json.dumps(template))
                    refused = invoke(self.binary, self.authority, 'session', 'submit', '--file', late)
                    assert refused['exit'] or refused['rejection']
                    self.cleanup_environment(self.current)
                    return False
        assert p.w1.snapshot(self.tree, self.base) == before
        if self.case == 'intervening-edit': (self.tree / 'owner.txt').write_text('Owner edit after both reports, preserve it.\n')
        return True

    def collect(self, rid, task):
        assert not task.get('repository_workspace')
        raw = (Path(task['workspace']) / task['context']['inputs']['manifest']['path']).read_bytes()
        assert p.w1.digest(raw) == task['context']['inputs']['manifest']['ref']['digest']
        manifest = json.loads(raw)
        assert manifest['join_result'] == 'satisfied' and [b['id'] for b in manifest['branches']] == ['ui', 'ux']
        assert manifest['selected_branch_ids'] == ['ui', 'ux']
        values, provenance = {}, {'manifest_ref': task['context']['inputs']['manifest']['ref'], 'manifest': manifest, 'reports': []}
        for row in manifest['branches']:
            assert row['status'] == 'completed' and row['outcome'] == 'succeeded' and row['has_waivers'] is False
            assert set(row['output_refs']) == {'report'}
            data = export(self.call, self.root, row['output_refs']['report'], 'export-' + str(len(self.provenance)) + '-' + row['id'])
            values[row['id'] + '_report'] = data
            provenance['reports'].append({'lens': row['id'], 'ref': row['output_refs']['report'], 'raw_base64': base64.b64encode(data).decode()})
        assert len({json.dumps(r['ref'], sort_keys=True) for r in provenance['reports']}) == 2
        self.provenance.append(provenance)
        submit(self.call, rid, task, values, raw=True)

    def release(self, rid, task):
        env = read(task, 'environment')
        value = {'status': 'released', 'owner': env['owner'], 'session': env['session'], 'reason': ''}
        before = p.w1.snapshot(self.tree, self.base)
        if self.case == 'wrong-cleanup-owner':
            try: self.current.release('another-owner', self.current.session)
            except LifecycleError as error: assert 'ownership_mismatch' in str(error)
            else: raise AssertionError('foreign cleanup accepted')
            assert self.current.server is not None
            value.update(status='blocked', reason='Foreign owner refused; exact owner reconciles outside workflow')
        elif self.case == 'cleanup-interrupted':
            try: self.current.release(self.current.owner, self.current.session, interrupt=True)
            except LifecycleError as error: assert 'reconcile_required' in str(error)
            else: raise AssertionError('interrupted cleanup looked released')
            assert self.current.lease.exists() and port_closed(self.current.url)
            value.update(status='reconcile_required', reason='Process stopped but lease retained; exact owner reconciliation required')
        else: self.cleanup_environment(self.current)
        assert p.w1.snapshot(self.tree, self.base) == before
        submit(self.call, rid, task, {'release': value})

    def drive(self, rid, iteration):
        for _ in range(16):
            if self.case == 'shared-stand':
                driven = invoke(self.binary, self.authority, 'run', 'drive', rid)
                if driven['exit']:
                    assert driven['document']['code'] == 'resource_busy', driven
                    tasks = self.tasks(rid)
                    assert len(tasks) == 1, 'capacity-one resource must refuse the second reader'
                    assert self.current.server is not None and self.current.lease.exists()
                    self.refusals.append({'code': 'resource_busy', 'scope': 'one native slot counts Attempts, including siblings in this Run',
                        'safe_mode': 'sequential for this shared stand; no waiver, capacity change or automatic fallback', 'browser_pair_dispatched': False})
                    self.cancel(rid); self.cleanup_environment(self.current)
                    return self.state(rid)
                assert not driven['rejection'], driven
            else: self.call('run', 'drive', rid)
            tasks = self.tasks(rid)
            if not tasks: return self.state(rid)
            names = [t['skill_refs'][0]['id'].rsplit('/', 1)[-1].removesuffix('-bridge') for t in tasks]
            if set(names) == {'ui', 'ux'}:
                if not self.browsers(rid, tasks, iteration): return self.state(rid)
            else:
                assert len(tasks) == 1, names
                if names[0] == 'environment': self.environment(rid, tasks[0], iteration)
                elif names[0] == 'collect': self.collect(rid, tasks[0])
                elif names[0] == 'release': self.release(rid, tasks[0])
                else: raise AssertionError(names)
        raise AssertionError('fixture did not converge')

    def resume(self, source):
        assert self.current.server is None and not self.current.lease.exists()
        args = ('project', 'continue', '--repository', self.repo, '--launch', 'parallel-product', '--host', self.host,
                '--source-run', source, '--allow-execution')
        prepared = self.call(*args, '--prepare')
        rid = self.call(*args, '--expected-launch-digest', prepared['review_digest'])['run']['run']['id']
        self.runs.append(rid)
        return rid

    def close(self):
        # Stop/wait only actors created here before touching their environment.
        for process, out in self.actors:
            if process.poll() is None:
                (out / 'stop').write_text('Fixture finalizer\n')
                try: process.communicate(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL); process.communicate(timeout=10)
        try:
            clean(self.binary, self.authority, self.runs)
            assert not any(c['status'] == 'active' for c in self.call('claim', 'list')['claims'])
        finally:
            for env in self.envs:
                if env.server is not None or env.interrupted: self.cleanup_environment(env)
            verify.forget_authority(self.authority)


def check(binary, case, library, host='codex-cli'):
    with tempfile.TemporaryDirectory(prefix='w5-browser-native-') as directory:
        f = Fixture(binary, Path(directory), case, library, host)
        try:
            state = f.drive(f.rid, 0)
            first_outcome = state.get('outcome') or state['status']
            expected = 'cancelled' if f.cancelled else 'rejected' if case == 'one-timeout' else 'partial' if case in (
                'defect-repair', 'stale-report-after-repair', 'wrong-origin', 'wrong-cleanup-owner', 'cleanup-interrupted', 'missing-browser', 'intervening-edit') else 'succeeded'
            assert first_outcome == expected, (case, first_outcome, state.get('diagnostics'))
            gate = None
            if 'gate' in state.get('output_artifacts', {}):
                gate = json.loads(export(f.call, f.root, state['output_artifacts']['gate'], 'first-gate'))
                assert gate['status'] == ('failed' if case in ('defect-repair', 'stale-report-after-repair') else 'blocked' if expected == 'partial' else 'warnings'), gate
            if case in ('defect-repair', 'stale-report-after-repair', 'cancel-before', 'cancel-after-first', 'cancel-during-browser', 'one-timeout'):
                if case in ('defect-repair', 'stale-report-after-repair'):
                    assert f.current.server is None and not f.current.lease.exists()
                    (f.tree / 'index.html').write_text(f.good_html)
                rid = f.resume(f.rid); state = f.drive(rid, 1)
                assert state['outcome'] == ('partial' if case == 'stale-report-after-repair' else 'succeeded'), state.get('diagnostics')
                assert len(f.rounds) == 2 and not set(f.rounds[0]['attempts']) & set(f.rounds[1]['attempts'])
                assert f.rounds[0]['environment']['session'] != f.rounds[1]['environment']['session']
                if case in ('defect-repair', 'stale-report-after-repair'):
                    assert f.rounds[0]['candidate'] != f.rounds[1]['candidate']
                if case == 'stale-report-after-repair':
                    final_gate = json.loads(export(f.call, f.root, state['output_artifacts']['gate'], 'replay-gate'))
                    assert final_gate['status'] == 'blocked', final_gate
            if case == 'shared-stand':
                assert f.current.server is None and not f.current.lease.exists()
                fresh = OwnedEnvironment(f.root / 'environment-state', f.tree, 'new-reviewed-owner', shared='fixture-stand')
                f.envs.append(fresh); fresh.ensure()
                f.cleanup_environment(fresh)
                f.refusals[0]['external_lease_reacquired_after_owned_cleanup'] = True
            if case == 'intervening-edit': assert (f.tree / 'owner.txt').read_text().startswith('Owner edit')
            return {'case': case, 'host': host, 'first_outcome': first_outcome, 'final_outcome': state.get('outcome') or state['status'],
                'scope': 'native graph / actual Chromium / deterministic reports; no LLM or independent-model attestation',
                'gate': gate, 'rounds': f.rounds, 'provenance': f.provenance, 'refusals': f.refusals, 'cleaned': True}
        finally: f.close()


if __name__ == '__main__':
    if not __debug__: raise RuntimeError('Qualification requires assertions')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True, type=Path)
    parser.add_argument('--browser-library', required=True, type=Path)
    parser.add_argument('--case', choices=CASES)
    parser.add_argument('--cases', nargs='+', choices=CASES)
    parser.add_argument('--jobs', type=int, choices=(1, 2, 3), default=1)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.case and args.cases: parser.error('Choose --case or --cases')
    cases = (args.case,) if args.case else tuple(args.cases) if args.cases else CASES
    results = []

    def record(result):
        results.append(result)
        print(json.dumps({k: v for k, v in result.items() if k not in ('rounds', 'provenance')}), flush=True)

    def isolated(case):
        # Each subprocess owns its authority, registry, config and browser data.
        with tempfile.TemporaryDirectory(prefix='w5-browser-job-') as directory:
            root = Path(directory)
            fixture_env = os.environ.copy()
            if 'PLAYWRIGHT_BROWSERS_PATH' not in fixture_env:
                # Preserve the installing user's cache before isolating HOME.
                # Explicit PLAYWRIGHT_BROWSERS_PATH (including 0) is unchanged.
                if sys.platform == 'darwin': cache = Path.home() / 'Library/Caches'
                elif sys.platform == 'win32': cache = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local'))
                else: cache = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache'))
                fixture_env['PLAYWRIGHT_BROWSERS_PATH'] = str(cache / 'ms-playwright')
            fixture_env.update(HOME=str(root), XDG_CONFIG_HOME=str(root / 'config'))
            output = root / 'result.json'
            result = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), '--binary', str(args.binary.resolve()),
                '--browser-library', str(args.browser_library.resolve()), '--case', case, '--report', str(output)],
                env=fixture_env, text=True, capture_output=True, timeout=600)
            assert result.returncode == 0, (case, result.stdout, result.stderr)
            return json.loads(output.read_text())['cases'][0]

    if args.jobs == 1:
        for case in cases: record(check(args.binary.resolve(), case, args.browser_library.resolve()))
    else:
        with ThreadPoolExecutor(max_workers=args.jobs) as executor:
            futures = {executor.submit(isolated, case): case for case in cases}
            try:
                for future in as_completed(futures): record(future.result())
            except BaseException:
                for future in futures: future.cancel()
                raise
        results.sort(key=lambda r: cases.index(r['case']))
    if args.report:
        args.report.write_text(json.dumps({'prifly': verify.run(args.binary, 'version')['version'],
            'binary_sha256': hashlib.sha256(args.binary.read_bytes()).hexdigest(), 'cases': results}, indent=2) + '\n')
