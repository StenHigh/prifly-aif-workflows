#!/usr/bin/env python3
"""Compile W5's minimal own graphs with unchanged W1 readers on three hosts."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from parallel_fixture import install
import verify


def check(binary):
    results = []
    with tempfile.TemporaryDirectory(prefix='w5-compile-') as directory:
        root = Path(directory)
        repo, authority = verify.prepare_repository(binary, root)
        try:
            package = install(repo)
            for host in verify.HOSTS:
                result, docs = verify.compile_package(binary, authority, repo, 'parallel-review', root / host, host)
                assert len(docs) == 8
                assert docs['aif-evidence:step/review']['repository_workspace'] == 'read_only'
                assert all(d['effects']['class'] == 'none' for k, d in docs.items() if ':step/' in k)
                quality = docs['w5:workflow/quality']['definition']['stages']
                parallel = quality['readers']
                assert parallel['kind'] == 'parallel' and parallel['max_parallelism'] == 2
                assert parallel['join'] == {'mode': 'all', 'accept_outcomes': ['succeeded'], 'selection': 'all', 'remainder': 'wait'}
                assert parallel['branches'][0]['input_bindings'] == parallel['branches'][1]['input_bindings']
                root_workflow = docs['w5:workflow/parallel-review']
                assert root_workflow['resumable']['from_cancelled']
                assert root_workflow['definition']['stages']['quality']['kind'] == 'call'
                assert docs['w5:workflow/round']['definition']['stages']['quality']['on_error'] == 'abandoned'
                results.append({'host': host, 'definitions': len(docs), 'build_key': result['build_key'],
                                'scope': 'compile only; not actual host execution or overlap'})
            for directory in ('files', 'schemas', 'contexts', 'steps'):
                for original in (verify.ROOT / 'aif-review-evidence' / directory).rglob('*'):
                    if original.is_file():
                        assert original.read_bytes() == (package / directory / original.relative_to(verify.ROOT / 'aif-review-evidence' / directory)).read_bytes()
        finally: verify.forget_authority(authority)
    return {'prifly': verify.run(binary, 'version')['version'],
            'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'cases': results}


def main():
    if not __debug__: raise RuntimeError('Qualification requires enabled assertions')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', required=True, type=Path)
    p.add_argument('--report', type=Path)
    args = p.parse_args(); result = check(args.binary)
    if args.report: args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
