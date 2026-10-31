#!/usr/bin/env python3
"""Compile unpublished parallel UI/UX fixture; retain shipping W2 bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from parallel_product_fixture import install
import verify
from context_sources import assert_same_context


def check(binary):
    results = []
    with tempfile.TemporaryDirectory(prefix='w5-browser-compile-') as directory:
        root = Path(directory)
        repo, authority = verify.prepare_repository(binary, root)
        try:
            package = install(repo)
            for host in verify.HOSTS:
                result, docs = verify.compile_package(binary, authority, repo, 'parallel-product', root / host, host)
                for lens in ('ui', 'ux'):
                    step = docs['aif-product:step/' + lens]
                    assert step['repository_workspace'] == 'read_only' and step['effects']['class'] == 'none'
                pair = docs['w5-product:workflow/pair']['definition']['stages']['readers']
                assert [b['id'] for b in pair['branches']] == ['ui', 'ux']
                assert pair['join'] == {'mode': 'all', 'accept_outcomes': ['succeeded'], 'selection': 'all', 'remainder': 'wait'}
                for port in ('candidate', 'environment', 'configuration'):
                    assert pair['branches'][0]['input_bindings'][port] == pair['branches'][1]['input_bindings'][port]
                assert 'repository_workspace' not in docs['w5-product:step/collect']
                quality = docs['aif-product:workflow/quality']['definition']['stages']
                assert quality['readers']['on_error'] == 'abandoned'
                assert quality['evaluate']['on']['pass'] == 'release'
                assert quality['release']['on']['pass'] == 'finalize'
                results.append({'host': host, 'definitions': len(docs), 'build_key': result['build_key'], 'scope': 'compile; no live host/session claim'})
            for directory in ('files', 'schemas', 'contexts', 'steps', 'instructions'):
                for source in (verify.ROOT / 'aif-ui-ux' / directory).rglob('*'):
                    if source.is_file():
                        copied=package / source.relative_to(verify.ROOT / 'aif-ui-ux')
                        if directory=='contexts':assert_same_context(source,copied)
                        else:assert source.read_bytes()==copied.read_bytes(),source
        finally:
            verify.forget_authority(authority)
    return {'prifly': verify.run(binary, 'version')['version'], 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'cases': results}


if __name__ == '__main__':
    if not __debug__: raise RuntimeError('Qualification requires assertions')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = check(args.binary)
    if args.report: args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
