"""Read-only git-candidate/1 snapshot, copied from aif-review-evidence; stdlib only."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

DIGEST = re.compile(r'sha256:[0-9a-f]{64}\Z')
COMMIT = re.compile(r'[0-9a-f]{40}\Z')


class Invalid(ValueError):
    pass


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def digest(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def git(tree, *args):
    env = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0', 'GIT_NO_LAZY_FETCH': '1', 'GIT_TERMINAL_PROMPT': '0'}
    result = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false', '-C', str(tree), *args],
                            env=env, capture_output=True, timeout=60)
    if result.returncode:
        raise Invalid('Git candidate operation failed: ' + args[0])
    return result.stdout


def snapshot(tree, base):
    """Hash HEAD, logical index and tracked/nonignored untracked bytes/modes.

    Never follows symlinks; refuses gitlinks, unresolved index and unstable reads.
    Ignored build caches/dependencies and .git metadata are outside this basis.
    """
    tree = Path(tree).resolve(strict=True)
    if not COMMIT.fullmatch(base):
        raise Invalid('Expected a full SHA-1 base commit')
    git(tree, 'cat-file', '-e', base + '^{commit}')
    if Path(os.fsdecode(git(tree, 'rev-parse', '--show-toplevel').strip())).resolve() != tree:
        raise Invalid('Expected the claimed repository root')

    def once():
        head = git(tree, 'rev-parse', 'HEAD').decode().strip()
        if not COMMIT.fullmatch(head):
            raise Invalid('Unsupported Git object format')
        index = git(tree, 'ls-files', '--stage', '-z')
        paths = set()
        for entry in index.split(b'\0'):
            if not entry:
                continue
            metadata, path = entry.split(b'\t', 1)
            mode, blob, stage = metadata.split()
            if stage != b'0' or mode == b'160000':
                raise Invalid('Unmerged index or submodule requires separate candidate policy')
            paths.add(path)
        paths.update(p for p in git(tree, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0') if p)
        if len(paths) > 10000:
            raise Invalid('Candidate exceeds 10000 paths')
        records = []
        for raw in sorted(paths):
            relative = Path(os.fsdecode(raw))
            if relative.is_absolute() or '..' in relative.parts or '.git' in relative.parts:
                raise Invalid('Unsafe candidate path')
            current = tree
            for part in relative.parts[:-1]:
                current = current / part
                try:
                    if not stat.S_ISDIR(current.lstat().st_mode):
                        raise Invalid('Candidate parent is not a real directory')
                except FileNotFoundError:
                    # Removed directory: the tracked path below is missing.
                    break
            path = tree / relative
            record = {'path': base64.b64encode(raw).decode()}
            try:
                mode = path.lstat().st_mode
                record['mode'] = stat.S_IMODE(mode)
                if stat.S_ISLNK(mode):
                    record.update(kind='symlink', digest=digest(os.fsencode(os.readlink(path))))
                elif stat.S_ISREG(mode):
                    # O_NOFOLLOW closes the lstat/open symlink race on supported hosts.
                    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
                    with os.fdopen(fd, 'rb') as stream:
                        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                            raise Invalid('Candidate file changed kind')
                        hashed = hashlib.sha256()
                        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                            hashed.update(chunk)
                    record.update(kind='file', digest='sha256:' + hashed.hexdigest())
                else:
                    raise Invalid('Unsupported candidate file kind')
            except FileNotFoundError:
                record.update(kind='missing')
            records.append(record)
        return {'base_commit': base, 'head_commit': head, 'index_digest': digest(index), 'files_digest': digest(encoded(records))}

    first, second = once(), once()
    if first != second:
        raise Invalid('Candidate changed during snapshot')
    return {'algorithm': 'git-candidate/1', **first, 'digest': digest(encoded(first))}
