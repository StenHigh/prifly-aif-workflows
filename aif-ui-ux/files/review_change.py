"""Task/candidate applicability boundary for the public review-for-change Call.

Native schema validation is complemented by exact correlation and fresh Git
snapshots. Semantic applicability remains the reader's judgement.
"""
import copy
import json
import os
from pathlib import Path
import sys
import evidence as w1
import product


def assess(source, task_digest, captured, current):
    """Create a fresh assessment; never edit the reader's original report."""
    result = copy.deepcopy(source)
    reasons = []
    if "source_report" in source:
        reasons.append("The reader cannot assert a guard derivation")
    if source['task_digest'] != task_digest:
        reasons.append('Applicability report belongs to another task')
    if source['candidate'] != captured or captured != current:
        reasons.append('Candidate changed or applicability names another candidate')
    if reasons:
        result.update(status='unknown', reason='; '.join(reasons),
                      task_digest=task_digest, candidate=copy.deepcopy(current))
    status = 'blocked' if result['status'] == 'unknown' else 'passed'
    return result, w1.gate(status, [result['reason']], blocking=status == 'blocked')


def configuration(value, captured):
    if value is None:
        raise w1.Invalid('Required UI/UX review has no project environment/check configuration')
    product.configuration(value)
    if value['surface'] != 'frontend':
        raise w1.Invalid('Required UI/UX review needs an explicit frontend configuration')
    for lens in product.LENSES:
        if value[lens]['base_commit'] != captured['base_commit']:
            raise w1.Invalid('Configuration names another candidate base')
        if not any(c['enabled'] and c['applicable'] and c['required']
                   for c in value[lens]['checks']):
            raise w1.Invalid('Required UI/UX review needs an enabled required '+lens+' check')
    return value


def worker(operation):
    envelope = json.load(sys.stdin)
    context = json.loads(Path(os.environ['PRIFLY_CONTEXT_FILE']).read_text())
    result = {'schema_version': '1', 'run_id': envelope['run_id'],
              'step_instance_id': envelope['step_instance_id'],
              'attempt_id': envelope['attempt_id'],
              'envelope_digest': os.environ['PRIFLY_ENVELOPE_DIGEST'], 'verdict': 'pass',
              'outputs': {}, 'evidence_refs': [], 'effect_receipt_refs': [],
              'summary': 'Review-for-change '+operation}

    def read(port):
        return json.loads(Path(context['inputs'][port]['path']).read_text())

    def output(port, value):
        slot = context['outputs'][port]
        raw = w1.encoded(value)+b'\n'
        Path(slot['path']).write_bytes(raw)
        reference = {k: slot[k] for k in ('artifact_id', 'revision')}
        reference['digest'] = w1.digest(raw)
        result['outputs'][port] = reference
        return reference

    try:
        implementation = read('implementation')
        tree = os.environ['PRIFLY_REPOSITORY_WORKSPACE']
        if operation == 'capture':
            output('candidate', w1.snapshot(tree, implementation['base_commit']))
        elif operation == 'guard':
            captured = read('candidate')
            current = w1.snapshot(tree, implementation['base_commit'])
            task_digest = context['inputs']['task']['ref']['digest']
            assessment, gate = assess(read('applicability'), task_digest, captured, current)
            original = context['inputs']['applicability']['ref']
            assessment['source_report'] = original
            reference = output('applicability', assessment)
            carrier = copy.deepcopy(implementation)
            carrier['reports'] = carrier.get('reports', [])+[original, reference]
            output('implementation', carrier)
            output('gate', gate)
        elif operation == 'configure':
            try:
                value = configuration(read('configuration') if 'configuration' in context['inputs'] else None,
                                      read('candidate'))
            except (w1.Invalid, KeyError, ValueError, TypeError) as error:
                result['verdict'] = 'blocked'
                output('gate', w1.gate('blocked', [str(error)], blocking=True))
            else:
                output('configuration', value)
                for lens in product.LENSES:
                    output(lens, product.project(value, lens))
        elif operation == 'bundle':
            carrier = copy.deepcopy(implementation)
            carrier['reports'] = carrier.get('reports', [])+[
                context['inputs'][name]['ref'] for name in ('ui_report', 'ux_report', 'gate')]
            output('implementation', carrier)
        else:
            raise ValueError('Unknown review-for-change operation')
    except (ValueError, OSError, KeyError, TypeError, w1.subprocess.SubprocessError) as error:
        result.update(verdict='fail', outputs={}, summary=str(error))
    os.write(3, w1.encoded(result)+b'\n')


if __name__ == '__main__':
    worker(sys.argv[1])
