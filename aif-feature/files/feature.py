"""W3 request projection and whole-round freshness; no repository writes."""
import copy
import json
import os
from pathlib import Path
import sys
import evidence as w1
import product as w2

LENSES = ('checks', 'security', 'review')


def configuration(task, surface=None):
    w1.obj(task, ('title', 'description', 'scope', 'assumptions', *LENSES,
                  'optional_policy', 'require_separate_session', 'product'), 'feature task')
    for field, bound in (('title', 400), ('description', 12000)):
        if not isinstance(task[field], str) or not task[field].strip() or len(task[field]) > bound:
            raise w1.Invalid('Invalid ' + field)
    for field in ('scope', 'assumptions'):
        items = task[field]
        if not isinstance(items, list) or len(items) > 40 or field == 'scope' and not items:
            raise w1.Invalid('Invalid ' + field)
        for item in items:
            w1.text(item, field)
    for lens in LENSES:
        request = {'base_commit': '0' * 40, 'round': 1, 'checks': task[lens],
                   'optional_policy': task['optional_policy'],
                   'require_separate_session': task['require_separate_session']}
        w1.request(request)
        if any(c['method'] == 'browser' for c in task[lens]):
            raise w1.Invalid('Browser criteria belong to the sealed product configuration')
    # A small feature still requires executable acceptance and a code review.
    for lens, method in (('checks', 'command'), ('review', 'code')):
        if not any(c['required'] and c['enabled'] and c['applicable'] and c['method'] == method for c in task[lens]):
            raise w1.Invalid('Missing required enabled ' + lens + ' acceptance')
    product = task['product']
    if product is not None:
        w2.configuration(product)
        if product['surface'] != 'frontend':
            raise w1.Invalid('Product configuration must declare frontend')
        for lens in w2.LENSES:
            for field in ('optional_policy','require_separate_session'):
                if product[lens][field] != task[field]:
                    raise w1.Invalid('Product '+lens+' disagrees with feature '+field)
            if not any(c['required'] and c['enabled'] and c['applicable'] for c in product[lens]['checks']):
                raise w1.Invalid('Frontend requires both UI and UX acceptance')
    if surface is not None and (surface not in ('backend', 'frontend') or (product is not None) != (surface == 'frontend')):
        raise w1.Invalid('Package profile disagrees with task surface')


def begin(task, base, previous):
    configuration(task)
    if type(previous) is not int or not 0 <= previous < 8:
        raise w1.Invalid('Round counter is outside the declared limit')
    round_number = previous + 1
    requests = {lens: {'base_commit': base, 'round': round_number, 'checks': task[lens],
                      'optional_policy': task['optional_policy'],
                      'require_separate_session': task['require_separate_session']} for lens in LENSES}
    for request in requests.values():
        w1.request(request)
    product = copy.deepcopy(task['product'])
    if product is None:
        # This projection is never sent to a product worker on the backend path.
        excluded = {'id': 'no_interface', 'description': 'Sealed backend scope has no interface',
                    'method': 'browser', 'required': False, 'enabled': False, 'applicable': False}
        product = {'surface': 'backend', 'scope_reason': 'Sealed task has no product surface',
                   'environment': {'owner': 'unused-backend', 'profile': 'unused', 'setup': 'Not applicable',
                                   'cleanup': 'Not applicable', 'browser_adapter': 'Not applicable',
                                   'test_identity': 'Not applicable', 'allowed_operations': ['navigate'], 'shared_resource': None},
                   'scenarios': [], **{lens: {**requests['checks'], 'checks': [excluded]} for lens in w2.LENSES}}
    for lens in w2.LENSES:
        product[lens].update(base_commit=base, round=round_number,
                             optional_policy=task['optional_policy'],
                             require_separate_session=task['require_separate_session'])
    w2.configuration(product)
    return round_number, requests, product


def feature_gate(status, findings, blocking=False, owner=False):
    return {'gate': 'feature', 'status': status, 'blocking': blocking,
            'blocking_owner_only': owner, 'findings': [f[:4000] for f in findings[:240]],
            'suggested_next': 'owner' if status == 'blocked' or owner else 'repair' if blocking else 'continue'}


def aggregate(task, captured, current, requests, reports, digests, product=None):
    configuration(task)
    results = []
    for lens in LENSES:
        # W1 validates report identity, request digest, round, candidate and coverage.
        results.append((lens, w1.evaluate(requests[lens], captured, reports[lens], current, digests[lens])))
    if product is not None:
        results.append(('product', product['gate']))
    findings = [lens + ': ' + finding for lens, gate in results for finding in gate['findings']]
    if any(g['status'] == 'blocked' for _, g in results):
        return feature_gate('blocked', findings)
    # An owner decision outranks an otherwise repairable defect in another lens.
    if any(g['blocking_owner_only'] for _, g in results):
        return feature_gate('warnings', findings, blocking=True, owner=True)
    if any(g['blocking'] for _, g in results):
        return feature_gate('failed', findings, blocking=True)
    return feature_gate('warnings' if findings else 'passed', findings)


def guard(captured, current, gate):
    if captured != current:
        return feature_gate('blocked', ['Candidate changed before commit'] + gate['findings'])
    return gate


def worker(operation):
    envelope = json.load(sys.stdin)
    context = json.loads(Path(os.environ['PRIFLY_CONTEXT_FILE']).read_text())
    result = {'schema_version': '1', **{k: envelope[k] for k in ('run_id', 'step_instance_id', 'attempt_id')},
              'envelope_digest': os.environ['PRIFLY_ENVELOPE_DIGEST'], 'verdict': 'pass', 'outputs': {},
              'evidence_refs': [], 'effect_receipt_refs': [], 'summary': 'Feature ' + operation}
    def read(port):
        return json.loads(Path(context['inputs'][port]['path']).read_text())
    def output(port, value):
        slot = context['outputs'][port]
        raw = w1.encoded(value) + b'\n'
        Path(slot['path']).write_bytes(raw)
        result['outputs'][port] = {k: slot[k] for k in ('artifact_id', 'revision')}
        result['outputs'][port]['digest'] = w1.digest(raw)
    try:
        base = read('implementation')['base_commit']
        if operation == 'configure':
            configuration(read('task'), read('surface'))
            output('round', 0)
        elif operation == 'begin':
            count, requests, config = begin(read('task'), base, read('round'))
            output('round', count)
            for lens in LENSES:
                output(lens + '_request', requests[lens])
            output('configuration', config)
            for lens in w2.LENSES:
                output(lens, w2.project(config, lens))
        elif operation == 'capture':
            output('candidate', w1.snapshot(os.environ['PRIFLY_REPOSITORY_WORKSPACE'], base))
        elif operation.startswith('aggregate-'):
            task = read('task')
            captured = read('candidate')
            requests = {lens: read(lens + '_request') for lens in LENSES}
            reports = {lens: read(lens + '_report') for lens in LENSES}
            digests = {lens: w1.digest(Path(context['inputs'][lens + '_request']['path']).read_bytes()) for lens in LENSES}
            product = None if operation.endswith('backend') else {
                'gate': read('product_gate'), **{p: read(p) for p in ('ui_report', 'ux_report', 'environment', 'release')}}
            try:
                current = w1.snapshot(os.environ['PRIFLY_REPOSITORY_WORKSPACE'], base)
                gate = aggregate(task, captured, current, requests, reports, digests, product)
            except (w1.Invalid, OSError, w1.subprocess.SubprocessError) as error:
                gate = feature_gate('blocked', ['Candidate cannot be assessed: ' + str(error)])
            output('gate', gate)
            output('evidence', {'round': read('round'), 'task_digest': w1.digest(Path(context['inputs']['task']['path']).read_bytes()),
                                'candidate': captured, 'requests': requests, 'reports': reports, 'product': product, 'gate': gate})
        elif operation == 'guard':
            try:
                gate = guard(read('candidate'), w1.snapshot(os.environ['PRIFLY_REPOSITORY_WORKSPACE'], base), read('gate'))
            except (w1.Invalid, OSError, w1.subprocess.SubprocessError) as error:
                gate = feature_gate('blocked', ['Candidate cannot be assessed before commit: ' + str(error)])
            output('gate', gate)
        else:
            raise w1.Invalid('Unknown feature operation')
    except (ValueError, OSError, KeyError, TypeError, w1.subprocess.SubprocessError) as error:
        result.update(verdict='fail', outputs={}, summary=str(error))
    os.write(3, w1.encoded(result) + b'\n')


if __name__ == '__main__':
    worker(sys.argv[1])
