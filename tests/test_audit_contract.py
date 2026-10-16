"""Compile the standalone audit and opt-in extension on the real runtime."""
import shutil

from verify import HOSTS, ROOT, compile_package, run


def check_test_audit(binary, authority, repository, root):
    package = repository / '.prifly/workflows/openclaw-test-audit'
    count = 0
    for host in HOSTS:
        result, documents = compile_package(binary, authority, repository, 'openclaw-test-audit', root / ('audit-' + host), host)
        assert result['package']['id'] == 'openclaw:package/test-audit'
        reader = documents['openclaw:step/audit']
        assert reader['repository_workspace'] == 'read_only'
        assert set(reader['inputs']) == {'request'}
        assert reader['outputs']['report']['required_for'] == ['pass', 'needs_revision', 'blocked']
        assert all(item['effects']['class'] == 'none' for name, item in documents.items() if ':step/' in name)
        count = len(documents)
    original = (package / 'workflow.yaml').read_bytes(), (package / 'extend.yaml').read_bytes()
    example = ROOT / 'examples/test-audit-extension'
    try:
        for name in ('workflow.yaml', 'extend.yaml'):
            shutil.copyfile(example / name, package / name)
        for host in HOSTS:
            _, documents = compile_package(binary, authority, repository, 'openclaw-test-audit', root / ('audit-extension-' + host), host)
            stages = documents['openclaw:workflow/test-audit-extension']['definition']['stages']
            assert stages['prepare']['on']['pass'] == 'audit'
            assert stages['audit']['input_bindings']['request']['stage_id'] == 'prepare'
            assert stages['evaluate']['input_bindings']['report']['stage_id'] == 'audit'
        overlay = (package / 'extend.yaml').read_text()
        (package / 'extend.yaml').write_text(overlay.replace('$stages.prepare.request', '$stages.prepare.report'))
        refused = run(binary, '--project', authority, 'project', 'compile', '--repository', repository,
                      '--package', 'openclaw-test-audit', '--host', 'codex-cli', '--output', root / 'audit-bad-binding', expect_ok=False)
        assert 'unavailable_output' in refused, refused
    finally:
        for name, raw in zip(('workflow.yaml', 'extend.yaml'), original):
            (package / name).write_bytes(raw)
    return count
