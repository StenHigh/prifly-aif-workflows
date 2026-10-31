"""W5 qualification fixture; unchanged W1 workers/schemas, explicit own graph."""
import shutil
import verify
from context_sources import relocate_instructions

OVERLAY = verify.ROOT / 'tests/probes/parallel-review'


def install(repository, *, parallelism=2, handle_errors=True, timeout=None, asymmetric=False, wrap_errors=True):
    package = repository / '.prifly/workflows/parallel-review'
    shutil.copytree(verify.ROOT / 'aif-review-evidence', package)
    relocate_instructions(package, 'aif-review-evidence')
    shutil.copytree(OVERLAY, package, dirs_exist_ok=True)
    if not wrap_errors:
        path = package / 'workflow.yaml'
        path.write_text(path.read_text().replace("workflow_quality: '{{workflow_round}}'", "workflow_quality: '{{workflow_quality}}'"))
    for name in ('workflow.yaml', 'workflows/quality.yaml', 'workflows/round.yaml'):
        path = package / name
        path.write_text(path.read_text().replace('max_parallelism: 2', 'max_parallelism: ' + str(parallelism)))
    if not handle_errors:
        for path in [package / 'workflow.yaml', *(package / 'workflows').glob('*.yaml')]:
            path.write_text(''.join(line for line in path.read_text().splitlines(keepends=True) if 'on_error:' not in line))
    if timeout is not None:
        path = package / 'steps/review.yaml'
        path.write_text(path.read_text().replace('active_timeout_ms: null', 'active_timeout_ms: ' + str(timeout)))
    if asymmetric:
        original = (verify.ROOT / 'aif-review-evidence/steps/review.yaml').read_text()
        (package / 'steps/review2.yaml').write_text(original.replace('id: aif-evidence:step/review', 'id: w5:step/review2'))
        branch = (package / 'workflows/reader.yaml').read_text()
        (package / 'workflows/reader2.yaml').write_text(branch.replace('id: w5:workflow/reader', 'id: w5:workflow/reader2').replace("'{{step_review}}'", "'{{step_review2}}'"))
        path = package / 'workflows/quality.yaml'
        value = path.read_text().replace("  workflow_reader: '{{workflow_reader}}'", "  workflow_reader: '{{workflow_reader}}'\n  workflow_reader2: '{{workflow_reader2}}'")
        path.write_text(value.replace('    - id: second\n      workflow_ref: workflow_reader', '    - id: second\n      workflow_ref: workflow_reader2'))
    profile = repository / '.prifly/project.yaml'
    value = profile.read_text().replace('packages:\n', 'packages:\n  parallel-review:\n    source: .prifly/workflows/parallel-review\n', 1)
    value = value.replace('launches:\n', 'launches:\n  parallel-review:\n    title: W5 qualification\n    description: Read-only implementation readers, never repair.\n    kind: workflow\n    workflow: .prifly/workflows/parallel-review/workflow.yaml\n', 1)
    profile.write_text(value)
    return package
