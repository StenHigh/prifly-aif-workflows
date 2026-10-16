"""Opt-in owned browser lifecycle and independent UI/UX host handoffs.

Project adapter code is explicitly reviewed and source-pinned in a Run input.
This module never interprets setup/cleanup prose as shell commands, changes
Run control, retries an external write, or repairs a candidate.
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

import evidence as w1
import product as w2
import browser_contract as browser
import parallel_host as controller


def input_value(task, port):
    path = Path(task['workspace']) / task['context']['inputs'][port]['path']
    raw = path.read_bytes()
    if w1.digest(raw) != task['context']['inputs'][port]['ref']['digest']:
        raise w1.Invalid('Delivered browser input differs from sealed ref: ' + port)
    return controller.transport.strict_json(raw)


def verify_project(adapter):
    browser.descriptor(adapter, required=True)
    root = Path(adapter['root'])
    if root.is_symlink() or not root.is_dir(): raise w1.Invalid('Reviewed adapter root is unavailable or a symlink')
    root = root.resolve()
    for name, expected in adapter['files'].items():
        path = root / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
            raise w1.Invalid('Adapter file is missing or escapes reviewed bundle: ' + name)
        if w1.digest(path.read_bytes()) != expected:
            raise w1.Invalid('Reviewed project adapter source drift: ' + name)
    return root / adapter['entrypoint']


def project_call(adapter, operation, payload, timeout=90):
    entrypoint = verify_project(adapter)
    request = {'protocol': browser.PROTOCOL, 'operation': operation,
               'settings': adapter['settings'], **payload}
    result = subprocess.run([sys.executable, '-I', '-B', str(entrypoint)], cwd=adapter['root'],
        input=w1.encoded(request), capture_output=True, timeout=timeout)
    if result.returncode:
        raise w1.Invalid('Project browser adapter ' + operation + ' failed; inspect owned effects before retry: '
                         + result.stderr.decode(errors='replace')[-1800:])
    if len(result.stdout) > 4 * 1024 * 1024: raise w1.Invalid('Browser adapter response exceeds 4 MiB')
    value = controller.transport.strict_json(result.stdout)
    if not isinstance(value, dict) or value.get('protocol') != browser.PROTOCOL:
        raise w1.Invalid('Project browser adapter protocol mismatch')
    return value


def owned_root(artifacts, task):
    if artifacts is None: raise w1.Invalid('An owned artifact directory outside the claimed repository is required')
    root = Path(artifacts).resolve()
    if task.get('repository_workspace') and root.is_relative_to(Path(task['repository_workspace']).resolve()):
        raise w1.Invalid('Browser journal/artifacts cannot be inside the read-only candidate')
    root = root / 'frontend' / task['run_id'].replace(':', '-')
    root.mkdir(parents=True, exist_ok=True)
    return root


def save(path, value):
    # Only this controller owns the journal. Atomic replacement preserves intent
    # on interruption; native artifact refs below remain the authoritative bytes.
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as file:
        file.write(w1.encoded(value) + b'\n'); temporary = Path(file.name)
    temporary.replace(path)


def exclusive(path, attempt):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w') as file: file.write(attempt + '\n')


def quality_limit(state):
    # Public Run configuration is sealed before admission. Do not reread live
    # extend.yaml or silently replace the owner's requested number of rounds.
    configurations = [c for c in (state.get('workflow_configurations') or {}).values()
        if c.get('workflow_ref', {}).get('id') == 'aif-feature:workflow/quality']
    if len(configurations) != 1:
        raise w1.Invalid('Exact sealed quality configuration unavailable or ambiguous')
    limit = configurations[0].get('inputs', {}).get('limit', {}).get('value')
    if type(limit) is not int or not 1 <= limit <= 3:
        raise w1.Invalid('parallel-ui-ux is qualified for 1-3 full quality rounds on released Pri-Fly; '
                         '4-8 rounds exceed its qualified storage envelope. Select sequential or review a limit of 1-3')
    return limit


def admit(binary, authority, task, artifacts=None):
    owned_root(artifacts, task)
    task_input = input_value(task, 'task'); config = task_input['product']
    w2.configuration(config); browser.isolated(config)
    adapter = input_value(task, 'browser_adapter'); verify_project(adapter)
    state = controller.call(binary, authority, 'run', 'status', task['run_id'])['run']
    quality_limit(state)
    for name in state.get('stage_resources', {}).get('quality', []):
        if state['resource_limits'][name] < 2:
            raise w1.Invalid('Quality resource ' + name + ' admits one Attempt; select sequential UI/UX')
    reply = project_call(adapter, 'admit', {'configuration': config}, timeout=30)
    expected = {'contexts': 'isolated', 'identities': 'isolated', 'environment': 'owned-loopback', 'cleanup': 'exact-owner-session'}
    if reply.get('status') != 'ready' or reply.get('capabilities') != expected:
        raise w1.Invalid('Browser capability unavailable: ' + str(reply.get('reason', 'Unsupported isolation/lifecycle')))


def environment(task, artifacts):
    controller.verify_adapter(task)
    config = input_value(task, 'configuration'); candidate = input_value(task, 'candidate')
    adapter = input_value(task, 'browser_adapter'); browser.isolated(config)
    root = owned_root(artifacts, task)
    path = root / (task['attempt_id'].replace(':', '-') + '.json')
    exclusive(path.with_suffix('.claim'), task['attempt_id'])
    journal = {'run_id': task['run_id'], 'environment_attempt': task['attempt_id'], 'adapter': adapter,
        'configuration': config, 'candidate': candidate, 'repository_workspace': task['repository_workspace'],
        'state': 'ensure_intent', 'actor_phase': 'not_started'}
    save(path, journal)
    reply = project_call(adapter, 'ensure', {'configuration': config, 'candidate': candidate,
        'repository_workspace': task['repository_workspace'], 'run_id': task['run_id'], 'attempt_id': task['attempt_id']})
    journal.update(state='ensure_returned', adapter_response=reply); save(path, journal)
    if reply.get('status') not in ('ready', 'unavailable', 'owner_required', 'reconcile_required'):
        raise w1.Invalid('Unsupported environment result; preserve intent and reconcile exact owned effects')
    env = {'status': reply['status'], 'owner': config['environment']['owner'], 'profile': config['environment']['profile'],
        'configuration_digest': task['context']['inputs']['configuration']['ref']['digest'], 'candidate_digest': candidate['digest'],
        'session': reply.get('session'), 'url': reply.get('url'), 'reason': reply.get('reason', '')}
    w2.receipt(config, candidate, env, env['configuration_digest'])
    bindings = {}
    for lens in browser.READERS:
        allocation = (reply.get('readers') or {}).get(lens, {})
        binding = {'protocol': browser.PROTOCOL, 'status': 'ready' if env['status'] == 'ready' else 'unavailable',
            'reason': '' if env['status'] == 'ready' else env['reason'], 'lens': lens, 'run_id': task['run_id'],
            'round': config[lens]['round'], 'owner': env['owner'], 'environment_session': env['session'],
            'candidate_digest': candidate['digest'], 'configuration_digest': env['configuration_digest'],
            'request_digest': task['context']['inputs'][lens]['ref']['digest'],
            'adapter_digest': task['context']['inputs']['browser_adapter']['ref']['digest'],
            'context_id': allocation.get('context_id'), 'identity_id': allocation.get('identity_id'),
            'allocation': allocation.get('allocation', {})}
        if env['status'] == 'ready':
            browser.binding(binding, lens=lens, run_id=task['run_id'], config=config, candidate=candidate,
                environment=env, config_digest=env['configuration_digest'], request_digest=binding['request_digest'],
                adapter_digest=binding['adapter_digest'])
        bindings[lens] = binding
    if env['status'] == 'ready': browser.distinct(bindings)
    values = {'environment': env, **{l + '_session': bindings[l] for l in browser.READERS}}
    slot = task['context']['outputs']['environment']
    journal.update(state='environment_ready', values=values,
        environment_ref={**{k: slot[k] for k in ('artifact_id', 'revision')}, 'digest': w1.digest(w1.encoded(env) + b'\n')})
    save(path, journal)
    return values


def journal_for(task, artifacts):
    env = input_value(task, 'environment')
    matches = []
    for path in owned_root(artifacts, task).glob('*.json'):
        journal = controller.transport.strict_json(path.read_bytes())
        if journal.get('values', {}).get('environment') == env: matches.append((path, journal))
    if len(matches) != 1: raise w1.Invalid('Exact owned environment journal unavailable; reconciliation required')
    path, journal = matches[0]
    if journal['environment_ref']['digest'] != task['context']['inputs']['environment']['ref']['digest']:
        raise w1.Invalid('Environment journal differs from native receipt')
    return path, journal


def validate_reader(task):
    controller.verify_adapter(task)
    config, candidate, env = (input_value(task, n) for n in ('configuration', 'candidate', 'environment'))
    adapter = input_value(task, 'browser_adapter'); verify_project(adapter)
    w2.configuration(config); browser.isolated(config)
    binding = input_value(task, 'browser_session'); lens = controller.role(task)
    browser.binding(binding, lens=lens, run_id=task['run_id'], config=config, candidate=candidate, environment=env,
        config_digest=task['context']['inputs']['configuration']['ref']['digest'],
        request_digest=task['context']['inputs']['request']['ref']['digest'],
        adapter_digest=task['context']['inputs']['browser_adapter']['ref']['digest'])
    if not input_value(task, 'request')['require_separate_session']:
        raise w1.Invalid('Parallel product reader requires a separate session')
    return binding


def dispatch(binary, authority, tasks, artifacts, codex):
    bindings = {controller.role(t): validate_reader(t) for t in tasks}; browser.distinct(bindings)
    journals = [journal_for(task, artifacts) for task in tasks]
    if journals[0][0] != journals[1][0]: raise w1.Invalid('Readers have different owned environment journals')
    path, journal = journals[0]
    exclusive(path.with_suffix('.actors'), ','.join(t['attempt_id'] for t in tasks))
    if journal['actor_phase'] != 'not_started': raise w1.Invalid('Browser actors already dispatched; inspect before retry')
    instructions = {}
    for task in tasks:
        command = shlex.join([sys.executable, '-B', str(Path(__file__).resolve()), 'observe',
            '--task', str(Path(task['workspace']) / 'parallel-task.json'), '--output', str(Path(task['workspace']) / 'browser')])
        instructions[controller.role(task)] = '\nUse this reviewed browser adapter command: ' + command + '''
Run it to execute only this lens's sealed scenarios in its own browser context and
test identity. Read observations.json and inspect the screenshots with your image
tool. DOM metrics and fixture failures are observations, not your review verdict.
Assess the declared UI/UX criteria yourself, using the pinned product bridge.
Each evidence observation must be a JSON STRING with exactly scenario, viewport,
url, observations. Copy the exact configured viewport and environment origin plus
scenario.path. locator is that exact page URL, not a screenshot/selector. tool names
the actual browser. Include visual findings and screenshot references in observations.
Do not include the other lens's scenarios. Unavailable browser/visual checks remain
unavailable, never substitute code-only inspection for required browser evidence.
Typed report session is separate (fresh CLI), model_profile unavailable, model null;
this does not attest a different model. Do not provision/release environments or
invoke the adapter for another operation. The controller owns the lifecycle.
'''
    journal.update(actor_phase='active', reader_attempts=[t['attempt_id'] for t in tasks]); save(path, journal)
    def archive(deliveries, observations):
        # Transport provenance is checked before either native report is sent.
        # Actual check/visual verdicts still belong to the readers and W1/W2.
        for task, observation in zip(deliveries, observations):
            source = Path(task['workspace']) / 'browser'
            report_path = Path(task['workspace']) / task['context']['outputs']['report']['path']
            report = controller.transport.strict_json(report_path.read_bytes())
            if any(c['status'] == 'executed' for c in report['checks']):
                receipt = controller.transport.strict_json((source / 'browser-session-receipt.json').read_bytes())
                for port in ('browser_session', 'environment', 'browser_adapter'):
                    if receipt[port + '_ref'] != task['context']['inputs'][port]['ref']:
                        raise w1.Invalid('Browser observation receipt belongs to another native input')
                if receipt['run_id'] != task['run_id'] or receipt['attempt_id'] != task['attempt_id']:
                    raise w1.Invalid('Browser receipt belongs to another Attempt')
                value, binding = receipt['result'], input_value(task, 'browser_session')
                if value.get('status') != 'ready' or any(value.get(k) != binding[k] for k in ('lens','context_id','identity_id')):
                    raise w1.Invalid('Browser observation does not bind this reader grant')
                config, request, env = (input_value(task, p) for p in ('configuration','request','environment'))
                enabled = {c['id'] for c in request['checks'] if c['enabled'] and c['applicable']}
                expected = {s['id']: s for s in config['scenarios'] if s['lens'] == binding['lens'] and s['check_id'] in enabled}
                items = value.get('observations', [])
                if len(items) != len(expected) or {i['scenario'] for i in items} != set(expected):
                    raise w1.Invalid('Browser receipt misses declared scenarios')
                for item in items:
                    spec = expected[item['scenario']]
                    if item['url'] != env['url'].rstrip('/') + spec['path'] or item['viewport'] != spec['viewport']:
                        raise w1.Invalid('Browser receipt uses another page/viewport')
                    image = Path(item['screenshot']).resolve()
                    if not image.is_relative_to(source.resolve()) or not image.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
                        raise w1.Invalid('Expected original PNG evidence inside this Attempt')
                    if w1.digest(image.read_bytes()) != item['screenshot_sha256']:
                        raise w1.Invalid('Browser screenshot digest changed')
            files = [p for p in source.rglob('*') if p.is_file()]
            if any(p.is_symlink() or not p.resolve().is_relative_to(source.resolve()) for p in source.rglob('*')):
                raise w1.Invalid('Browser evidence cannot contain symlinks or escape the Attempt')
            if len(files) > 256 or sum(p.stat().st_size for p in files) > 32 * 1024 * 1024:
                raise w1.Invalid('Browser evidence exceeds its 256-file/32-MiB Attempt bound')
            destination = Path(artifacts) / 'browser-evidence' / task['attempt_id'].replace(':', '-')
            source.mkdir(exist_ok=True)
            shutil.copytree(source, destination)
            observation['browser_evidence'] = {'directory': str(destination),
                'files': {str(p.relative_to(source)): w1.digest(p.read_bytes()) for p in files}}
        # This callback runs only after both CLI actors returned and original
        # browser evidence was validated, before any native submission. A later
        # submit refusal cannot make those actors live again.
        journal.update(actor_phase='settled', reader_observations=observations)
        save(path, journal)
    try:
        observations = controller.dispatch(binary, authority, tasks, codex=codex, artifacts=Path(artifacts) / 'uiux-readers',
            readers=browser.READERS, instructions=instructions, before_submit=archive)
        journal['reader_observations'] = observations
        return observations
    finally:
        # A CLI error/timeout is not an attestation that every external browser
        # descendant stopped. Preserve uncertainty unless the complete evidence
        # callback established settlement. Operator inspection is required.
        if journal['actor_phase'] != 'settled': journal['actor_phase'] = 'unknown'
        save(path, journal)


def release_value(adapter, config, env):
    reply = project_call(adapter, 'release', {'configuration': config, 'environment': env})
    value = reply.get('release')
    w1.obj(value, ('status', 'owner', 'session', 'reason'), 'release receipt')
    if value['owner'] != env['owner'] or value['session'] != env['session']:
        raise w1.Invalid('Project cleanup does not bind exact owner/session')
    if value['status'] not in ('released', 'not_needed', 'blocked', 'reconcile_required'):
        raise w1.Invalid('Invalid project cleanup status')
    return value


def release(binary, authority, task, artifacts):
    controller.verify_adapter(task)
    path, journal = journal_for(task, artifacts)
    state = controller.call(binary, authority, 'run', 'status', task['run_id'])['run']
    readers = [a for a in state['attempts'].values()
        if state['steps'][a['step_instance_id']]['definition_ref']['id'] in ('aif-feature:step/parallel-ui', 'aif-feature:step/parallel-ux')]
    if any(not a.get('settled') for a in readers) or readers and journal['actor_phase'] != 'settled':
        raise w1.Invalid('Reader actors must be settled before owned environment cleanup')
    adapter = input_value(task, 'browser_adapter')
    if adapter != journal['adapter']: raise w1.Invalid('Cleanup adapter differs from owned setup')
    exclusive(Path(task['workspace']) / 'frontend-release.claim', task['attempt_id'])
    journal['state'] = 'release_intent'; save(path, journal)
    value = release_value(adapter, input_value(task, 'configuration'), input_value(task, 'environment'))
    journal.update(state='release_returned', release=value); save(path, journal)
    return value


def cleanup(binary, authority, path):
    """Explicit operator cleanup after terminal cancel/failure, never Run control."""
    path = Path(path); journal = controller.transport.strict_json(path.read_bytes())
    state = controller.call(binary, authority, 'run', 'status', journal['run_id'])['run']
    if state['status'] not in ('completed', 'cancelled', 'failed') or any(not a.get('settled') for a in state['attempts'].values()):
        raise w1.Invalid('Native Run/Attempts must be settled before operator cleanup')
    if journal['actor_phase'] not in ('not_started', 'settled'):
        raise w1.Invalid('Actual reader actors are unknown; inspect and stop them before cleanup')
    attempt = state['attempts'].get(journal['environment_attempt'])
    if (not attempt or state['steps'][attempt['step_instance_id']]['definition_ref']['id'] != 'aif-feature:step/frontend-environment'
            or (attempt.get('accepted') or {}).get('outputs', {}).get('environment') != journal['environment_ref']):
        raise w1.Invalid('Journal does not name this Run\'s accepted environment Attempt')
    with tempfile.TemporaryDirectory(prefix='owned-receipt-', dir=path.parent) as directory:
        for port, expected in (('environment', journal['values']['environment']), ('configuration', journal['configuration']), ('browser_adapter', journal['adapter'])):
            native_ref = journal['environment_ref'] if port == 'environment' else attempt['context']['inputs'][port]['ref']
            ref, output = Path(directory) / (port+'-ref.json'), Path(directory) / (port+'.json')
            ref.write_bytes(w1.encoded(native_ref))
            controller.call(binary, authority, 'artifact', 'export', '--ref', ref, '--output', output)
            if w1.digest(output.read_bytes()) != native_ref['digest'] or controller.transport.strict_json(output.read_bytes()) != expected:
                raise w1.Invalid('Cleanup journal differs from native accepted ' + port)
    value = release_value(journal['adapter'], journal['configuration'], journal['values']['environment'])
    journal.update(state='operator_cleanup', release=value); save(path, journal)
    return value


def observe(task, output):
    binding = validate_reader(task)
    output = Path(output).resolve()
    if not output.is_relative_to(Path(task['workspace']).resolve()):
        raise w1.Invalid('Browser observations must stay in this Attempt workspace')
    output.mkdir(parents=True, exist_ok=True)
    value = project_call(input_value(task, 'browser_adapter'), 'observe', {
        'configuration': input_value(task, 'configuration'), 'request': input_value(task, 'request'),
        'candidate': input_value(task, 'candidate'), 'environment': input_value(task, 'environment'),
        'browser_session': binding, 'attempt_id': task['attempt_id'], 'output_directory': str(output)})
    receipt = {'protocol': browser.PROTOCOL, 'run_id': task['run_id'], 'attempt_id': task['attempt_id'], 'result': value,
        **{p + '_ref': task['context']['inputs'][p]['ref'] for p in ('browser_session','environment','browser_adapter')}}
    save(output / 'browser-session-receipt.json', receipt)
    return value


def service(binary, authority, tasks, *, host: str, codex, artifacts):
    roles = [controller.role(t) for t in tasks]
    if host != 'codex-cli': raise w1.Invalid('Parallel UI/UX is qualified only for the explicit codex-cli adapter')
    if roles == ['frontend-environment']:
        values = environment(tasks[0], artifacts)
        controller.submit_values(binary, authority, tasks[0], values)
    elif roles == ['frontend-release']:
        value = release(binary, authority, tasks[0], artifacts)
        controller.submit_values(binary, authority, tasks[0], {'release': value})
    elif roles == ['collect-uiux']:
        controller.submit_values(binary, authority, tasks[0], {'bundle': controller.collect(binary, authority, tasks[0], browser.READERS)})
    elif len(roles) == 2 and set(roles) == set(browser.READERS):
        return {'handled': True, 'role': 'parallel-uiux', 'observations': dispatch(binary, authority, tasks, artifacts, codex)}
    else: return {'handled': False}
    return {'handled': True, 'role': roles[0]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='operation', required=True)
    ob = commands.add_parser('observe'); ob.add_argument('--task', type=Path, required=True); ob.add_argument('--output', type=Path, required=True)
    cl = commands.add_parser('cleanup'); cl.add_argument('--binary', type=Path, required=True); cl.add_argument('--project', type=Path, required=True); cl.add_argument('--journal', type=Path, required=True)
    args = parser.parse_args()
    value = observe(controller.transport.strict_json(args.task.read_bytes()), args.output) if args.operation == 'observe' else cleanup(args.binary, args.project, args.journal)
    print(json.dumps(value))
