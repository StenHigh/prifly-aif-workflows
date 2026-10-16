"""Test-only identity-scoped notes API; no external account or shared data."""
from http.cookies import SimpleCookie
import json
from urllib.parse import urlsplit

from product_environment import QuietHandler


class ProductHandler(QuietHandler):
    def __init__(self, *args, identities, notes, lock, **kwargs):
        self.identities, self.notes, self.lock = identities, notes, lock
        super().__init__(*args, **kwargs)

    def identity(self):
        cookie = SimpleCookie()
        cookie.load(self.headers.get('Cookie', ''))
        token = cookie.get('w5_identity')
        return token.value if token and token.value in self.identities else None

    def respond(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path not in ('/whoami', '/notes'):
            return super().do_GET()
        identity = self.identity()
        if identity is None: return self.respond(403, {'error': 'fixture identity required'})
        with self.lock:
            self.respond(200, {'identity': identity, 'notes': list(self.notes.get(identity, []))})

    def do_POST(self):
        if self.path != '/notes': return self.respond(404, {})
        identity = self.identity()
        if identity is None: return self.respond(403, {'error': 'fixture identity required'})
        size = int(self.headers.get('Content-Length', 0))
        if not 0 < size <= 4096: return self.respond(400, {})
        body = json.loads(self.rfile.read(size))
        if set(body) != {'text'} or not isinstance(body['text'], str): return self.respond(400, {})
        with self.lock:
            self.notes.setdefault(identity, []).append(body['text'])
            self.respond(200, {'identity': identity, 'notes': list(self.notes[identity])})
