"""Real catalog install/update and standalone compilation without AI Factory skills."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile

import verify

NAME = 'openclaw-test-audit'
RELEASE = 'v1.55.0'


def check_install(binary, catalog=None, expected_commit=None):
    with tempfile.TemporaryDirectory(prefix='test-audit-install-') as directory:
        root = Path(directory)
        repository, authority = root / 'repository', root / 'authority'
        repository.mkdir()
        verify.git('-C', repository, 'init', '-q', '-b', 'main')
        hosts = [argument for host in verify.HOSTS for argument in ('--host', host)]
        verify.run(binary, 'project', 'init', '--repository', repository, '--state-root', authority, *hosts)
        try:
            source = None
            if catalog is None:
                source = root / 'source'
                source.mkdir()
                shutil.copytree(verify.ROOT / NAME, source / NAME, ignore=shutil.ignore_patterns('__pycache__'))
                manifest = (verify.ROOT / 'catalog' / (NAME + '.yaml')).read_text()
                manifest = manifest.replace('https://github.com/StenHigh/prifly-aif-workflows.git', source.as_uri())
                (source / 'catalog.yaml').write_text(manifest.replace('ref: ' + RELEASE, 'ref: main'))
                verify.git('-C', source, 'init', '-q', '-b', 'main')
                verify.git('-C', source, 'add', '.')
                verify.git('-C', source, 'commit', '-qm', 'Initial test audit catalog')
                catalog = source.as_uri()
            catalog_args = [] if catalog == 'default' else ['--catalog', catalog]

            def call(*args):
                return verify.run(binary, '--project', authority, 'project', 'workflows', *args)

            found = call('search', NAME, *catalog_args)
            assert NAME in json.dumps(found), found
            installed_result = call('add', NAME, *catalog_args, '--repository', repository)
            origin = installed_result['origin']
            assert installed_result['package']['id'] == 'openclaw:package/test-audit'
            assert installed_result['package']['version'] == '1.1.0'
            assert origin['path'] == NAME
            if source is None:
                assert origin['ref'] == RELEASE, origin
                if expected_commit:
                    assert origin['commit'] == expected_commit, origin
            folder = repository / '.prifly/workflows' / NAME
            paths = [path for path in (verify.ROOT / NAME).rglob('*') if path.is_file() and '__pycache__' not in path.parts]
            for path in paths:
                assert (folder / path.relative_to(verify.ROOT / NAME)).read_bytes() == path.read_bytes(), path
            for host in verify.HOSTS:
                assert not any((repository / verify.HOSTS[host] / skill).exists() for skill in verify.CLASSIC_SKILLS), 'Fixture supplies AI Factory skills'
                verify.compile_package(binary, authority, repository, NAME, root / host, host)
            extend = folder / 'extend.yaml'
            owner_settings = '# Project-owned settings\nexclude: []\nextensions: []\n'
            extend.write_text(owner_settings)
            overlay = folder / 'project/owner.txt'
            overlay.parent.mkdir()
            overlay.write_text('Preserve project-owned configuration\n')
            if source:
                readme = source / NAME / 'README.md'
                readme.write_text(readme.read_text() + '\nLocal install fixture update.\n')
                workflow = source / NAME / 'workflow.yaml'
                workflow.write_text(workflow.read_text().replace('version: 1.1.0', 'version: 1.1.1'))
                verify.git('-C', source, 'add', '.')
                verify.git('-C', source, 'commit', '-qm', 'Updated test audit fixture')
            updated = call('update', NAME, '--repository', repository)
            assert extend.read_text() == owner_settings
            assert overlay.read_text() == 'Preserve project-owned configuration\n'
            if source:
                assert (folder / 'README.md').read_bytes() == readme.read_bytes()
                assert updated['package']['version'] == '1.1.1'
            else:
                assert updated['origin']['commit'] == origin['commit']
            verify.compile_package(binary, authority, repository, NAME, root / 'updated')
            bridge = folder / 'instructions/audit-bridge.md'
            bridge.write_text(bridge.read_text() + '\n# Unreviewed local modification\n')
            refusal = verify.run(binary, '--project', authority, 'project', 'workflows', 'update', NAME,
                                 '--repository', repository, expect_ok=False)
            assert 'project_workflow_modified' in refusal and 'audit-bridge.md' in refusal, refusal
            return {'outcome': 'passed', 'origin': origin, 'installed_files': len(paths),
                    'hosts_without_ai_factory_skills': list(verify.HOSTS), 'installed_bytes': 'matched',
                    'update': 'preserved extend and project overlay', 'local_edit': 'refused'}
        finally:
            verify.forget_authority(authority)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--catalog', help='Catalog Git URL, or default for the public default catalog')
    parser.add_argument('--expected-commit')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    value = check_install(args.binary.resolve(strict=True), args.catalog, args.expected_commit)
    if args.report:
        args.report.write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(value))
