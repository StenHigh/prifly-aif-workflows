"""Compile W4 and its one-input extension on the released binary."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from integration_fixture import EXAMPLE, install, i
import verify


def check(binary):
    results = []
    with tempfile.TemporaryDirectory(prefix='w4-compile-') as directory:
        root = Path(directory)
        repository, authority = verify.prepare_repository(binary, root)
        try:
            install(repository)
            package = repository / '.prifly/workflows/verified-integration'
            for host in verify.HOSTS:
                compiled, documents = verify.compile_package(binary, authority, repository, 'verified-integration', root / host, host)
                steps = {k: v for k, v in documents.items() if ':step/' in k}
                assert steps['aif-integration:step/prepare']['schema_version'] == '14'
                assert steps['aif-integration:step/prepare']['effects']['class'] == 'external_write'
                assert steps['aif-integration:step/local-merge']['effects']['retry_class'] == 'reconcile_required'
                assert steps['aif-integration:step/final-reader']['repository_workspace'] == 'read_only'
                results.append({'case': 'full-graph', 'host': host, 'definitions': len(documents), 'build_key': compiled['build_key']})
            for folder in ('schemas', 'contexts'):
                names = ('candidate', 'gate', 'request', 'report') if folder == 'schemas' else ('aif-review', 'review-severity')
                for name in names:
                    assert (EXAMPLE / folder / (name + '.yaml')).read_bytes() == (verify.ROOT / 'aif-review-evidence' / folder / (name + '.yaml')).read_bytes()
            assert (EXAMPLE / 'files/evidence.py').read_bytes() == (verify.ROOT / 'aif-review-evidence/files/evidence.py').read_bytes()
            (package / 'workflow.yaml').write_bytes((EXAMPLE / 'extensions/one-input-workflow.yaml').read_bytes())
            initial = (EXAMPLE / 'extensions/extend.yaml').read_text()
            (package / 'extend.yaml').write_text(initial)
            compiled, documents = verify.compile_package(binary, authority, repository, 'verified-integration', root / 'one-input')
            stages = documents['aif-integration:workflow/one-input-example']['definition']['stages']
            assert stages['configure']['on']['pass'] == 'extension'
            binding = stages['extension']['input_bindings']['handoff']
            assert isinstance(binding, dict) and binding.get('stage_id') == 'configure' and binding.get('port') == 'handoff', stages['extension']
            results.append({'case': 'one-input', 'host': 'codex-cli', 'build_key': compiled['build_key']})
            negatives = {
                'unknown-producer': initial.replace('$stages.configure.handoff', '$stages.absent.handoff'),
                'unavailable-producer': initial.replace('to: done', 'to: later').replace('pass: done', 'pass: later').replace('$stages.configure.handoff', '$stages.later.handoff'),
                'unknown-output': initial.replace('$stages.configure.handoff', '$stages.configure.missing'),
                'incompatible-schema': initial,
                'multiple-bindings': initial.replace('handoff: $stages.configure.handoff', 'handoff: $stages.configure.handoff\n    second: $stages.configure.handoff'),
            }
            for case, extension in negatives.items():
                (package / 'extend.yaml').write_text(extension)
                workflow = (EXAMPLE / 'extensions/one-input-workflow.yaml').read_text()
                if case == 'unavailable-producer':
                    workflow = workflow.replace('pass: done', 'pass: later', 1).replace('  done:\n    kind: finish',
                        '  later:\n    kind: step\n    step_ref: step_configure\n    input_bindings: {handoff: $inputs.handoff}\n    on: {pass: done, fail: abandoned, needs_revision: abandoned, no_work: abandoned}\n    impossible_verdicts: [blocked]\n  done:\n    kind: finish', 1)
                (package / 'workflow.yaml').write_text(workflow)
                step = package / 'steps/extension.yaml'
                original = (EXAMPLE / 'steps/extension.yaml').read_text()
                if case == 'incompatible-schema':
                    original = original.replace('{{schema_handoff}}', '{{schema_report}}')
                step.write_text(original)
                failure = verify.run(binary, '--project', authority, 'project', 'compile', '--repository', repository,
                                     '--package', 'verified-integration', '--host', 'codex-cli', '--output', root / case, expect_ok=False)
                assert 'invalid_yaml' not in failure, failure
                expected = {'unknown-producer': 'project_extension_unknown_stage', 'unknown-output': 'unknown_port',
                            'incompatible-schema': 'port_type_mismatch', 'unavailable-producer': 'unavailable',
                            'multiple-bindings': 'project_extension_invalid'}[case]
                assert expected in failure, failure
                results.append({'case': case, 'refused': failure[-2500:]})
        finally:
            verify.forget_authority(authority)
    return {'prifly': verify.run(binary, 'version')['version'], 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'cases': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    value = check(args.binary)
    if args.report:
        args.report.write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(value, indent=2))


if __name__ == '__main__':
    main()
