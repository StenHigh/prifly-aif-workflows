"""Deterministic UI/UX transport, browser-grant validation and owned cleanup gate."""
import json
import os
from pathlib import Path
import sys

import evidence as w1
import product as w2
import parallel_reports as transport
import browser_contract as browser


def assess(config, candidate, environment, bindings, adapter, requests, request_digests,
           config_digest, adapter_digest, run_id, current, manifest=None, bundle=None, manifest_digest=None):
    reports = {}
    assessment = {'configuration': config, 'candidate': candidate, 'environment': environment,
        'browser_sessions': bindings, 'adapter_digest': adapter_digest, 'configuration_digest': config_digest,
        'requests': requests, 'request_digests': request_digests, 'reports': reports,
        'parallel': {'manifest': manifest, 'manifest_digest': manifest_digest, 'bundle': bundle}}
    try:
        browser.descriptor(adapter, required=True); browser.isolated(config)
        w2.receipt(config, candidate, environment, config_digest)
        for lens in browser.READERS:
            browser.binding(bindings[lens], lens=lens, run_id=run_id, config=config, candidate=candidate,
                environment=environment, config_digest=config_digest, request_digest=request_digests[lens], adapter_digest=adapter_digest)
        browser.distinct(bindings)
        if manifest is None: raise w1.Invalid('Parallel readers/evaluation did not yield a usable assessment; inspect native Run diagnostics')
        reports.update(transport.unpack(manifest, manifest_digest, bundle, browser.READERS))
        for lens in browser.READERS:
            if not requests[lens]['require_separate_session']:
                raise w1.Invalid('Parallel UI/UX requires separate reviewer sessions')
        gate = w2.evaluate(config, requests['ui'], requests['ux'], candidate, environment, reports,
                           current, config_digest, request_digests)
        if gate['status'] != 'blocked':
            lenses = [w1.evaluate(requests[l], candidate, reports[l], current, request_digests[l]) for l in browser.READERS]
            if any(g['blocking_owner_only'] for g in lenses):
                gate = w1.gate('warnings', gate['findings'], blocking=True, owner=True)
    except (ValueError, TypeError, KeyError, OSError) as error:
        gate = w1.gate('blocked', ['Parallel UI/UX cannot be accepted: ' + str(error)])
    assessment['gate'] = gate
    return assessment


def finalize(assessment, release, current):
    value = dict(assessment)
    value['release'] = release
    value['gate'] = w2.finalize(value['configuration'], value['candidate'], value['environment'], release, value['gate'], current)
    return value


def worker(operation):
    envelope = json.load(sys.stdin)
    context = json.loads(Path(os.environ['PRIFLY_CONTEXT_FILE']).read_text())
    result = {'schema_version': '1', **{k: envelope[k] for k in ('run_id', 'step_instance_id', 'attempt_id')},
        'envelope_digest': os.environ['PRIFLY_ENVELOPE_DIGEST'], 'verdict': 'pass', 'outputs': {},
        'evidence_refs': [], 'effect_receipt_refs': [], 'summary': 'Parallel product ' + operation}
    def read(port): return transport.strict_json(Path(context['inputs'][port]['path']).read_bytes())
    def digest(port): return w1.digest(Path(context['inputs'][port]['path']).read_bytes())
    def output(port, value):
        slot = context['outputs'][port]; data = w1.encoded(value) + b'\n'; Path(slot['path']).write_bytes(data)
        result['outputs'][port] = {k: slot[k] for k in ('artifact_id', 'revision')}
        result['outputs'][port]['digest'] = w1.digest(data)
    try:
        if operation == 'finalize':
            value = read('assessment')
            try: current = w1.snapshot(os.environ['PRIFLY_REPOSITORY_WORKSPACE'], value['candidate']['base_commit'])
            except (ValueError, OSError, w1.subprocess.SubprocessError): current = None
            value = finalize(value, read('release'), current)
            output('gate', value['gate']); output('evidence', value)
        else:
            candidate = read('candidate')
            try: current = w1.snapshot(os.environ['PRIFLY_REPOSITORY_WORKSPACE'], candidate['base_commit'])
            except (ValueError, OSError, w1.subprocess.SubprocessError): current = None
            value = assess(read('configuration'), candidate, read('environment'), {l: read(l + '_session') for l in browser.READERS},
                read('browser_adapter'), {l: read(l) for l in browser.READERS}, {l: digest(l) for l in browser.READERS},
                digest('configuration'), digest('browser_adapter'), envelope['run_id'], current,
                **({'manifest': read('manifest'), 'bundle': read('bundle'), 'manifest_digest': context['inputs']['manifest']['ref']['digest']}
                   if operation == 'evaluate' else {}))
            output('assessment', value)
    except (ValueError, KeyError, TypeError, OSError) as error:
        result.update(verdict='fail', outputs={}, summary=str(error))
    os.write(3, w1.encoded(result) + b'\n')


if __name__ == '__main__': worker(sys.argv[1])
