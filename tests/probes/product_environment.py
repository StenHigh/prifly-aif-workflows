"""Disposable loopback fixture; ownership/lease are independent of Git claims.

This is a test adapter, not a production environment manager or a bundled worker.
All state lives in its explicitly allocated private directory outside the repo.
"""
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import uuid

class LifecycleError(RuntimeError):pass

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

class OwnedEnvironment:
    def __init__(self, state_root, repository, owner, profile='all-checks', shared=None):
        self.root=Path(state_root);self.root.mkdir(parents=True,exist_ok=True)
        self.repository=Path(repository);self.owner=owner;self.profile=profile
        self.session='fixture-'+uuid.uuid4().hex;self.server=None;self.thread=None
        self.lease=self.root/((shared or self.session)+'.lease.json');self.interrupted=False

    def ensure(self,profile=None,transition=False,owner=None):
        if owner is not None and owner!=self.owner:raise LifecycleError('ownership_mismatch')
        if self.interrupted:raise LifecycleError('reconcile_required')
        desired=profile or self.profile
        if self.server:
            if desired==self.profile:return self.url
            if not transition:raise LifecycleError('release_required')
            # Explicit scoped transition, preserving repository and evidence root.
            self.release(self.owner,self.session)
        data={'owner':self.owner,'session':self.session,'profile':desired}
        try:
            with self.lease.open('x') as f:json.dump(data,f)
        except FileExistsError:raise LifecycleError('owner_required: existing environment lease')
        try:
            self.server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(self.repository)))
            self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
            self.profile=desired;self.url='http://127.0.0.1:'+str(self.server.server_port)
            return self.url
        except BaseException:
            self.lease.unlink();raise

    def release(self,owner,session,interrupt=False):
        if owner!=self.owner or session!=self.session:raise LifecycleError('ownership_mismatch')
        if self.interrupted:raise LifecycleError('reconcile_required')
        if not self.server:
            if self.lease.exists():raise LifecycleError('reconcile_required')
            return
        data=json.loads(self.lease.read_text())
        if data['owner']!=owner or data['session']!=session:raise LifecycleError('ownership_mismatch')
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=5)
        self.server=None;self.thread=None
        if interrupt:
            self.interrupted=True;raise LifecycleError('reconcile_required')
        self.lease.unlink()

    def reconcile(self,owner,session):
        if owner!=self.owner or session!=self.session:raise LifecycleError('ownership_mismatch')
        if not self.interrupted:return
        data=json.loads(self.lease.read_text())
        if data['owner']!=owner or data['session']!=session or self.server:raise LifecycleError('ownership_mismatch')
        # In this fixture only this object starts the server, and shutdown joined.
        # Production adapters must discover their actual process/container state.
        self.lease.unlink();self.interrupted=False

    def close(self):
        if self.interrupted:self.reconcile(self.owner,self.session)
        if self.server:self.release(self.owner,self.session)
