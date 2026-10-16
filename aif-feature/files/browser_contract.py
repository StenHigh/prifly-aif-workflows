"""Sealed project adapter and per-lens browser grants; no environment effects."""
from pathlib import PurePosixPath
from urllib.parse import urlsplit

import evidence as w1

PROTOCOL = 'aif-feature-browser/1'
READERS = ('ui', 'ux')


def descriptor(value, required=False):
    if value is None:
        if required: raise w1.Invalid('parallel-ui-ux requires an explicitly reviewed browser_adapter')
        return
    w1.obj(value, ('protocol', 'root', 'entrypoint', 'files', 'settings'), 'browser adapter')
    if value['protocol'] != PROTOCOL: raise w1.Invalid('Unsupported browser adapter protocol')
    if not isinstance(value['root'], str) or not value['root'].startswith('/'):
        raise w1.Invalid('Browser adapter root must be an absolute reviewed bundle directory')
    files = value['files']
    if not isinstance(files, dict) or not 1 <= len(files) <= 32:
        raise w1.Invalid('Browser adapter must pin its source files')
    for name, digest in files.items():
        path = PurePosixPath(name)
        if not isinstance(name, str) or path.is_absolute() or '..' in path.parts or str(path) != name:
            raise w1.Invalid('Invalid adapter bundle path')
        if not isinstance(digest, str) or not w1.DIGEST.fullmatch(digest):
            raise w1.Invalid('Invalid adapter source digest')
    if value['entrypoint'] not in files or not value['entrypoint'].endswith('.py'):
        raise w1.Invalid('Adapter entrypoint must be a pinned Python source file')
    if not isinstance(value['settings'], dict) or len(w1.encoded(value)) > 65536:
        raise w1.Invalid('Invalid or oversized adapter settings')


def isolated(config):
    if config['surface'] != 'frontend' or config['environment']['shared_resource'] is not None:
        raise w1.Invalid('parallel-ui-ux requires an isolated owned stand; shared_resource must be null')


def origin(value):
    parsed = urlsplit(value)
    if (parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', '::1') or not parsed.port
            or parsed.username or parsed.password or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
        raise w1.Invalid('Qualified browser adapter requires an owned loopback HTTP origin')


def binding(value, *, lens, run_id, config, candidate, environment, config_digest, request_digest, adapter_digest):
    w1.obj(value, ('protocol', 'status', 'reason', 'lens', 'run_id', 'round', 'owner', 'environment_session',
                  'candidate_digest', 'configuration_digest', 'request_digest', 'adapter_digest',
                  'context_id', 'identity_id', 'allocation'), 'browser session')
    expected = {'protocol': PROTOCOL, 'lens': lens, 'run_id': run_id, 'round': config[lens]['round'],
                'owner': environment['owner'], 'environment_session': environment['session'],
                'candidate_digest': candidate['digest'], 'configuration_digest': config_digest,
                'request_digest': request_digest, 'adapter_digest': adapter_digest}
    for key, val in expected.items():
        if value[key] != val: raise w1.Invalid('Browser session belongs to another ' + key)
    if value['status'] != 'ready' or environment['status'] != 'ready':
        raise w1.Invalid('Browser session unavailable: ' + str(value['reason']))
    if value['reason'] != '': raise w1.Invalid('Ready browser session has an unavailable reason')
    for key in ('context_id', 'identity_id'): w1.text(value[key], key)
    if not isinstance(value['allocation'], dict): raise w1.Invalid('Invalid adapter allocation')
    origin(environment['url'])


def distinct(bindings):
    for field in ('context_id', 'identity_id'):
        if len({bindings[lens][field] for lens in READERS}) != 2:
            raise w1.Invalid('UI/UX cannot share browser ' + field)
