"""Unpublished W5 browser qualification, built on byte-identical W2 workers.

Only this disposable copy has parallel readers. No installed package is changed.
The transport Attempt copies exact public exports; W2 programs make the gate.
"""
import json
import shutil

import verify


def write(package, name, value):
    (package / name).write_text(json.dumps(value, indent=2) + '\n')


def install(repository, timeout=None):
    package = repository / '.prifly/workflows/parallel-product'
    shutil.copytree(verify.ROOT / 'aif-ui-ux', package)
    root = package / 'workflow.yaml'
    text = root.read_text().replace('max_step_instances: 8', 'max_step_instances: 9')
    text = text.replace('max_parallelism: 1', 'max_parallelism: 2').replace('max_child_depth: 2', 'max_child_depth: 4')
    text = text.replace('    policy: core:policy/local@4.0.0',
                        '    aggregate_manifest: core:schema/aggregate-manifest@1.0.0\n    policy: core:policy/local@4.0.0')
    root.write_text(text)
    quality = package / 'workflows/quality.yaml'
    text = quality.read_text().replace('max_step_instances: 7', 'max_step_instances: 8')
    text = text.replace('max_control_transitions: 25', 'max_control_transitions: 48')
    text = text.replace('max_parallelism: 1', 'max_parallelism: 2').replace('max_child_depth: 1', 'max_child_depth: 3')
    text = text.replace("  policy: '{{policy}}'", "  policy: '{{policy}}'\n  workflow_pair: '{{workflow_pair}}'\n  step_collect: '{{step_collect}}'")
    start, end = text.index('  ui:\n    kind: step'), text.index('  evaluate:\n    kind: step')
    stages = {
        'readers': {'kind': 'call', 'workflow_ref': 'workflow_pair', 'input_bindings': {
            'configuration': '$inputs.configuration', 'ui': '$inputs.ui', 'ux': '$inputs.ux',
            'candidate': '$stages.capture.candidate', 'environment': '$stages.environment.environment'},
            'on': {'succeeded': 'collect', 'partial': 'abandoned'}, 'on_error': 'abandoned'},
        'collect': {'kind': 'step', 'step_ref': 'step_collect', 'input_bindings': {'manifest': '$stages.readers.manifest'},
            'on': {'pass': 'evaluate', 'needs_revision': 'abandoned', 'blocked': 'abandoned', 'fail': 'abandoned', 'no_work': 'abandoned'}}}
    # JSON is valid YAML; indent a mapping's entries under the existing stages.
    snippet = ''.join('  ' + json.dumps(k) + ': ' + json.dumps(v) + '\n' for k, v in stages.items())
    text = text[:start] + snippet + text[end:]
    text = text.replace('pass: ui', 'pass: readers')
    text = text.replace('$stages.ui.report', '$stages.collect.ui_report').replace('$stages.ux.report', '$stages.collect.ux_report')
    quality.write_text(text)

    inputs = {'configuration': 'schema_configuration', 'candidate': 'schema_candidate', 'environment': 'schema_environment'}
    refs = {name: '{{' + name + '}}' for name in ('policy', 'schema_configuration', 'schema_candidate', 'schema_environment', 'schema_request', 'schema_report')}
    for lens in ('ui', 'ux'):
        write(package, 'workflows/reader-' + lens + '.yaml', {
            'authoring': 'prifly-workflow/1', 'schema_version': '6', 'id': 'w5-product:workflow/reader-' + lens,
            'version': '1.0.0', 'title': 'Qualification ' + lens, 'refs': {**refs, 'step_reader': '{{step_' + lens + '}}'},
            'inputs': {**inputs, 'request': 'schema_request'},
            'outputs': {'report': {'schema_ref': 'schema_report', 'required_for': ['succeeded']}},
            'entry': 'reader', 'policy_ref': 'policy',
            'limits': {'max_step_instances': 1, 'max_control_transitions': 8, 'max_parallelism': 1, 'max_child_depth': 1},
            'stages': {
                'reader': {'kind': 'step', 'step_ref': 'step_reader', 'input_bindings': {k: '$inputs.' + k for k in (*inputs, 'request')},
                           'on': {'pass': 'done', 'needs_revision': 'done', 'blocked': 'done', 'fail': 'abandoned', 'no_work': 'abandoned'}},
                'done': {'kind': 'finish', 'outcome': 'succeeded', 'output_bindings': {'report': '$stages.reader.report'}},
                'abandoned': {'kind': 'finish', 'outcome': 'rejected'}}})
    write(package, 'workflows/pair.yaml', {
        'authoring': 'prifly-workflow/1', 'schema_version': '6', 'id': 'w5-product:workflow/pair', 'version': '1.0.0',
        'title': 'Qualification all-join browser readers', 'refs': {**refs, 'manifest': '{{aggregate_manifest}}',
            **{'reader_' + l: '{{workflow_reader-' + l + '}}' for l in ('ui', 'ux')}},
        'inputs': {**inputs, 'ui': 'schema_request', 'ux': 'schema_request'},
        'outputs': {'manifest': {'schema_ref': 'manifest', 'required_for': ['succeeded', 'partial']}},
        'entry': 'readers', 'policy_ref': 'policy',
        'limits': {'max_step_instances': 2, 'max_control_transitions': 24, 'max_parallelism': 2, 'max_child_depth': 2},
        'stages': {'readers': {'kind': 'parallel', 'max_parallelism': 2, 'branches': [
            {'id': l, 'workflow_ref': 'reader_' + l, 'input_bindings': {**{k: '$inputs.' + k for k in inputs}, 'request': '$inputs.' + l}} for l in ('ui', 'ux')],
            'join': {'mode': 'all', 'accept_outcomes': ['succeeded'], 'selection': 'all', 'remainder': 'wait'},
            'on': {'satisfied': 'done', 'unsatisfied': 'standing'}},
            'done': {'kind': 'finish', 'outcome': 'succeeded', 'output_bindings': {'manifest': '$stages.readers.results'}},
            'standing': {'kind': 'finish', 'outcome': 'partial', 'output_bindings': {'manifest': '$stages.readers.results'}}}})
    write(package, 'steps/collect.yaml', {
        'authoring': 'prifly-step/2', 'id': 'w5-product:step/collect', 'version': '1.0.0', 'title': 'Qualification exact report transport',
        'kind': 'worker', 'inputs': {'manifest': {'schema_ref': '{{aggregate_manifest}}'}},
        'outputs': {l + '_report': {'schema_ref': '{{schema_report}}', 'required_for': ['pass']} for l in ('ui', 'ux')},
        'executor': {'adapter_ref': '{{session}}', 'operation': 'session'},
        'instructions_ref': '{{context_collect}}', 'effects': {'class': 'none', 'retry_class': 'pure'},
        'result_schema_ref': '{{result_v2}}', 'session_limits': {'active_timeout_ms': None}})
    write(package, 'contexts/collect.yaml', {'id': 'w5-product:context/collect', 'version': '1.0.0',
        'media_type': 'text/plain; charset=utf-8',
        'text': 'Qualification controller only: export each exact selected UI/UX report ref after all-join using public artifact export; verify original digest and copy bytes unchanged. No gate decision, source access, repair or cleanup. Missing/unavailable bytes stop acceptance.'})
    if timeout is not None:
        path = package / 'steps/ui.yaml'
        path.write_text(path.read_text().replace('active_timeout_ms: null', 'active_timeout_ms: ' + str(timeout)))
    profile = repository / '.prifly/project.yaml'
    text = profile.read_text().replace('packages:\n', 'packages:\n  parallel-product:\n    source: .prifly/workflows/parallel-product\n', 1)
    text = text.replace('launches:\n', 'launches:\n  parallel-product:\n    title: W5 parallel browser qualification\n    description: Unpublished test composition.\n    kind: workflow\n    workflow: .prifly/workflows/parallel-product/workflow.yaml\n', 1)
    profile.write_text(text)
    return package
