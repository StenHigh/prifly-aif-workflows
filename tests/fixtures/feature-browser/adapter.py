"""Reviewed test-only adapter: private loopback server, separate browser grants.

No production accounts, backend writes, dependencies installed or shared stand.
The daemon serves only its captured fixture tree and owns a capability-protected
shutdown endpoint. A failed/foreign lease is never removed by another owner.
"""
import functools
import hashlib
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time
from urllib.request import Request, urlopen
import uuid

PROTOCOL = 'aif-feature-browser/1'
CAPABILITIES = {'contexts': 'isolated', 'identities': 'isolated', 'environment': 'owned-loopback', 'cleanup': 'exact-owner-session'}


def write(path, value):
    temporary = path.with_suffix('.next-' + uuid.uuid4().hex)
    temporary.write_text(json.dumps(value))
    temporary.replace(path)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, state, **kwargs):
        self.state = state
        super().__init__(*args, **kwargs)

    def log_message(self, *_): pass

    def respond(self, code, body):
        data = json.dumps(body).encode(); self.send_response(code)
        self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(data)))
        self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        if self.path != '/__identity': return super().do_GET()
        cookie = SimpleCookie(); cookie.load(self.headers.get('Cookie', ''))
        token = cookie.get('aif_identity')
        matches = [r for r in self.state['readers'].values() if token and r['allocation']['token'] == token.value]
        if len(matches) != 1: return self.respond(403, {'error': 'unissued fixture identity'})
        row = matches[0]
        return self.respond(200, {'identity_id': row['identity_id'], 'context_id': row['context_id'], 'session': self.state['session']})

    def do_POST(self):
        if self.path != '/__shutdown' or self.headers.get('X-Owner-Token') != self.state['control_secret']:
            return self.respond(403, {'error': 'not an owned lifecycle operation'})
        self.respond(200, {'stopping': True})
        threading.Thread(target=self.server.shutdown, daemon=True).start()


def serve(path):
    state = json.loads(path.read_text())
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=state['repository_workspace'], state=state))
    state.update(url='http://127.0.0.1:' + str(server.server_port), pid=os.getpid(), ready=True)
    write(path, state)
    try: server.serve_forever()
    finally:
        server.server_close()
        state.update(server_stopped=True); write(path, state)


def owner_lease(root, owner): return root / ('owner-' + hashlib.sha256(owner.encode()).hexdigest()[:24] + '.lease')


def browser(request, settings):
    lock = json.loads(Path(__file__).with_name('tool-lock.json').read_text())
    expected = lock['packages']['']['devDependencies']['playwright']
    installed = json.loads((Path(settings['library']) / 'package.json').read_text())['version']
    if installed != expected: raise ValueError('Browser library differs from pinned tool lock')
    result = subprocess.run([settings['node'], str(Path(__file__).with_name('browser.cjs')), settings['library']],
                            input=json.dumps(request), capture_output=True, text=True, timeout=75)
    if result.returncode: raise ValueError(result.stderr[-1800:])
    return json.loads(result.stdout)


def dispatch(request):
    operation, settings = request['operation'], request['settings']
    if request['protocol'] != PROTOCOL: raise ValueError('Wrong project adapter protocol')
    fault = settings.get('fault')
    if operation == 'admit':
        if fault in ('unsupported-browser', 'shared-context', 'shared-identity'):
            return {'protocol': PROTOCOL, 'status': 'unavailable', 'reason': 'Fixture deliberately lacks required browser isolation/capability', 'capabilities': {}}
        try:
            browser({'operation': 'admit'}, settings)
            return {'protocol': PROTOCOL, 'status': 'ready', 'reason': 'Actual Chromium is available; separate private contexts and anonymous identities', 'capabilities': CAPABILITIES}
        except (ValueError, OSError, subprocess.SubprocessError) as error:
            return {'protocol': PROTOCOL, 'status': 'unavailable', 'reason': str(error), 'capabilities': {}}
    root = Path(settings['state_root']).resolve(); root.mkdir(parents=True, exist_ok=True)
    if operation == 'ensure':
        config = request['configuration']; owner = config['environment']['owner']
        if root.is_relative_to(Path(request['repository_workspace']).resolve()): raise ValueError('Fixture state must be outside the candidate')
        if fault == 'missing-environment': return {'protocol': PROTOCOL, 'status': 'unavailable', 'reason': 'Fixture environment unavailable; no setup attempted', 'session': None, 'url': None}
        lease = owner_lease(root, owner)
        session = 'environment-' + uuid.uuid4().hex
        state = {'owner': owner, 'session': session, 'run_id': request['run_id'], 'attempt_id': request['attempt_id'],
            'candidate_digest': request['candidate']['digest'], 'repository_workspace': request['repository_workspace'],
            'control_secret': uuid.uuid4().hex, 'ready': False, 'server_stopped': False,
            'readers': {l: {'context_id': 'context-' + uuid.uuid4().hex, 'identity_id': 'identity-' + uuid.uuid4().hex,
                'allocation': {'token': uuid.uuid4().hex}} for l in ('ui', 'ux')}}
        try:
            with lease.open('x') as file: json.dump({'owner': owner, 'session': session}, file)
        except FileExistsError:
            return {'protocol': PROTOCOL, 'status': 'owner_required', 'reason': 'Existing owner lease; no resource adopted or stopped', 'session': None, 'url': None}
        path = root / (session + '.json'); write(path, state)
        try:
            with (root / (session + '.log')).open('w') as log:
                process = subprocess.Popen([sys.executable, '-I', '-B', str(Path(__file__).resolve()), '--serve', str(path)],
                    stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
            deadline = time.monotonic() + 10
            while not (state := json.loads(path.read_text()))['ready']:
                if process.poll() is not None or time.monotonic() > deadline: raise ValueError('Own fixture daemon did not become ready')
                time.sleep(.03)
            # Own child is intentionally persistent; the exact receipt controls release.
            return {'protocol': PROTOCOL, 'status': 'ready', 'reason': '', 'session': session,
                    'url': state['url'], 'readers': state['readers']}
        except BaseException:
            if 'process' in locals() and process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=5)
            lease.unlink(); path.unlink(missing_ok=True)
            raise
    env = request['environment']
    if env['session'] is None:
        if operation != 'release': raise ValueError('Browser environment unavailable')
        return {'protocol': PROTOCOL, 'release': {'status': 'not_needed', 'owner': env['owner'], 'session': None, 'reason': ''}}
    if not env['session'].startswith('environment-') or '/' in env['session']: raise ValueError('Invalid owned session')
    path = root / (env['session'] + '.json'); state = json.loads(path.read_text())
    if state['owner'] != env['owner'] or state['session'] != env['session'] or state['url'] != env['url']:
        raise ValueError('Exact owned receipt mismatch')
    lease = owner_lease(root, state['owner'])
    if operation == 'observe':
        binding = request['browser_session']; lens = binding['lens']
        if binding['environment_session'] != state['session'] or binding['run_id'] != state['run_id'] or binding['candidate_digest'] != state['candidate_digest']:
            raise ValueError('Stale environment/browser grant')
        row = state['readers'][lens]
        if any(binding[k] != row[k] for k in ('context_id', 'identity_id', 'allocation')): raise ValueError('Wrong per-reader allocation')
        if state['server_stopped']: raise ValueError('Owned environment already stopped')
        if fault == 'runtime-browser-unavailable':
            return {'protocol': PROTOCOL, 'status': 'unavailable', 'reason': 'Browser became unavailable after admission; no code substitution'}
        if fault == 'hold-browser' and lens == 'ux' and not Path(settings['control_release']).exists(): request['_hold'] = True
        return browser(request, settings)
    if operation != 'release': raise ValueError('Unsupported lifecycle operation')
    value = {'status': 'released', 'owner': env['owner'], 'session': env['session'], 'reason': ''}
    if not lease.exists():
        if not state['server_stopped']: raise ValueError('Missing lease while owned daemon may be active')
        return {'protocol': PROTOCOL, 'release': value}
    if json.loads(lease.read_text()) != {'owner': state['owner'], 'session': state['session']}:
        raise ValueError('Foreign lease; nothing stopped')
    if fault == 'wrong-cleanup-owner' and not state.get('fault_seen'):
        state['fault_seen'] = True; write(path, state)
        value.update(status='blocked', reason='Injected foreign-owner cleanup was refused; exact owner reconciliation required')
        return {'protocol': PROTOCOL, 'release': value}
    if not state['server_stopped']:
        req = Request(state['url'] + '/__shutdown', data=b'', method='POST', headers={'X-Owner-Token': state['control_secret']})
        with urlopen(req, timeout=5) as response: assert response.status == 200
        deadline = time.monotonic() + 10
        while not (state := json.loads(path.read_text()))['server_stopped']:
            if time.monotonic() > deadline: raise ValueError('Owned shutdown is uncertain; keep lease')
            time.sleep(.03)
        with socket.socket() as client:
            client.settimeout(1)
            assert client.connect_ex(('127.0.0.1', int(state['url'].rsplit(':', 1)[1]))) != 0
    if fault == 'cleanup-interrupted' and not state.get('fault_seen'):
        state['fault_seen'] = True; write(path, state)
        value.update(status='reconcile_required', reason='Own server stopped, exact lease retained; reconcile before replay')
        return {'protocol': PROTOCOL, 'release': value}
    lease.unlink()
    return {'protocol': PROTOCOL, 'release': value}


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--serve': serve(Path(sys.argv[2]))
    else:
        try: print(json.dumps(dispatch(json.load(sys.stdin))))
        except BaseException as error:
            print(str(error), file=sys.stderr); sys.exit(1)
