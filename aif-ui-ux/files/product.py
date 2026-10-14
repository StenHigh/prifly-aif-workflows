"""W2 sealed scenario projection, W1 coverage and owned-environment diagnostics."""
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit
import evidence as w1

LENSES = ('ui', 'ux')


def needed(config):
    return any(c['enabled'] and c['applicable'] for lens in LENSES for c in config[lens]['checks'])


def configuration(value):
    w1.obj(value, ('surface', 'scope_reason', 'ui', 'ux', 'environment', 'scenarios'), 'configuration')
    if value['surface'] not in ('frontend', 'backend'):
        raise w1.Invalid('Unknown product surface')
    w1.text(value['scope_reason'], 'scope reason')
    for lens in LENSES:
        w1.request(value[lens])
        for check in value[lens]['checks']:
            if check['method'] != 'browser':
                raise w1.Invalid('Product readers require declared browser checks')
            if check['applicable'] != (value['surface'] == 'frontend'):
                raise w1.Invalid('Applicability must follow sealed surface, not browser availability')
    for field in ('base_commit', 'round', 'optional_policy', 'require_separate_session'):
        if value['ui'][field] != value['ux'][field]:
            raise w1.Invalid('UI/UX disagree about ' + field)
    env = value['environment']
    w1.obj(env, ('owner', 'profile', 'setup', 'cleanup', 'browser_adapter', 'test_identity', 'allowed_operations', 'shared_resource'), 'environment contract')
    for field in ('owner', 'profile', 'setup', 'cleanup', 'browser_adapter', 'test_identity'):
        w1.text(env[field], field)
    operations = env['allowed_operations']
    if not isinstance(operations, list) or not operations or len(set(operations)) != len(operations) or any(x not in ('navigate', 'input', 'submit_test') for x in operations):
        raise w1.Invalid('Invalid test operations')
    resource = env['shared_resource']
    if resource is not None and (not isinstance(resource, str) or not w1.re.fullmatch('[a-z][a-z0-9_-]{0,63}', resource)):
        raise w1.Invalid('Invalid shared resource')
    scenes = value['scenarios']
    if not isinstance(scenes, list) or len(scenes) > 160:
        raise w1.Invalid('Invalid scenarios')
    ids = set()
    for scene in scenes:
        w1.obj(scene, ('id', 'lens', 'check_id', 'path', 'viewport', 'actions', 'expectations'), 'scenario')
        if not isinstance(scene['id'], str) or not w1.re.fullmatch('[a-z][a-z0-9_-]{0,79}', scene['id']) or scene['id'] in ids:
            raise w1.Invalid('Invalid or duplicate scenario ID')
        ids.add(scene['id'])
        if scene['lens'] not in LENSES or scene['check_id'] not in {c['id'] for c in value[scene['lens']]['checks']}:
            raise w1.Invalid('Scenario references unknown lens/check')
        if not isinstance(scene['path'], str) or not w1.re.fullmatch(r'/[^\s]*', scene['path']) or scene['path'].startswith('//') or '#' in scene['path']:
            raise w1.Invalid('Scenario must name a relative test page path')
        w1.obj(scene['viewport'], ('width', 'height'), 'viewport')
        if any(type(v) is not int or not 240 <= v <= 4096 for v in scene['viewport'].values()):
            raise w1.Invalid('Invalid viewport')
        for field in ('actions', 'expectations'):
            items = scene[field]
            if not isinstance(items, list) or len(items) > 40 or field == 'expectations' and not items:
                raise w1.Invalid('Invalid scenario ' + field)
            for item in items:
                w1.text(item, field)
    for lens in LENSES:
        for check in value[lens]['checks']:
            if check['enabled'] and check['applicable'] and not any(s['lens'] == lens and s['check_id'] == check['id'] for s in scenes):
                raise w1.Invalid('Applicable check has no scenario: ' + check['id'])


def project(value, lens):
    """Each W1 request seals the lens, scenario catalog and environment contract."""
    result = json.loads(json.dumps(value[lens]))
    for check in result['checks']:
        bundle = {'lens': lens, 'scope_reason': value['scope_reason'], 'environment': value['environment'],
                  'scenarios': [s for s in value['scenarios'] if s['lens'] == lens and s['check_id'] == check['id']]}
        check['description'] += '\nSealed product contract: ' + w1.encoded(bundle).decode()
    w1.request(result)  # Bound descriptions retain W1's 4000-byte text limit.
    return result


def receipt(config, captured, env, config_digest):
    w1.obj(env, ('status', 'owner', 'profile', 'configuration_digest', 'candidate_digest', 'session', 'url', 'reason'), 'environment receipt')
    if env['status'] not in ('ready', 'unavailable', 'not_needed', 'owner_required', 'reconcile_required'):
        raise w1.Invalid('Invalid environment status')
    if env['owner'] != config['environment']['owner'] or env['profile'] != config['environment']['profile'] or env['configuration_digest'] != config_digest or env['candidate_digest'] != captured['digest']:
        raise w1.Invalid('Environment receipt belongs to another contract/owner/profile/candidate')
    if not isinstance(env['reason'], str):
        raise w1.Invalid('Invalid environment reason')
    if env['status'] == 'ready':
        w1.text(env['session'], 'owned session')
        w1.text(env['url'], 'test URL')
        parsed = urlsplit(env['url'])
        if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
            raise w1.Invalid('Expected explicit test origin without credentials')
    else:
        w1.text(env['reason'], 'environment unavailable reason')
        if env['url'] is not None or env['session'] is not None and not isinstance(env['session'], str):
            raise w1.Invalid('Unavailable environment claims a URL/invalid session')
    if env['status'] == 'not_needed' and needed(config):
        raise w1.Invalid('Applicable browser checks cannot use not_needed environment')


def scenarios(config, lens, env, report):
    """Verify complete scenario declarations; browser observations remain host claims."""
    specs = {s['id']: s for s in config['scenarios'] if s['lens'] == lens}
    for check in report['checks']:
        if check['status'] != 'executed':
            continue
        if env['status'] != 'ready':
            raise w1.Invalid('Browser execution claimed without a ready environment')
        seen = set()
        for item in check['evidence']:
            observation = json.loads(item['observation'])
            w1.obj(observation, ('scenario', 'viewport', 'url', 'observations'), 'browser observation')
            sid = observation['scenario']
            spec = specs.get(sid)
            if not spec or spec['check_id'] != check['id'] or sid in seen:
                raise w1.Invalid('Unknown/duplicate/wrong-check scenario observation')
            seen.add(sid)
            expected_url = env['url'].rstrip('/') + spec['path']
            if observation['viewport'] != spec['viewport'] or observation['url'] != expected_url or item['locator'] != expected_url:
                raise w1.Invalid('Wrong scenario viewport or test page')
            w1.text(observation['observations'], 'browser observations')
        expected = {sid for sid, spec in specs.items() if spec['check_id'] == check['id']}
        if seen != expected:
            raise w1.Invalid('Missing declared browser scenarios')


def evaluate(config, ui, ux, captured, env, reports, current, config_digest, request_digests):
    try:
        configuration(config)
        if ui != project(config, 'ui') or ux != project(config, 'ux'):
            raise w1.Invalid('Projected UI/UX request differs from sealed configuration')
        receipt(config, captured, env, config_digest)
        gates = []
        for lens, request in zip(LENSES, (ui, ux)):
            assessment = w1.evaluate(request, captured, reports[lens], current, request_digests[lens])
            # W1 first validates report fields before the scenario-level inspection.
            if assessment['status'] != 'blocked':
                scenarios(config, lens, env, reports[lens])
            gates.append(assessment)
        findings = [lens + ': ' + item for lens, result in zip(LENSES, gates) for item in result['findings']]
        if env['status'] not in ('ready', 'not_needed') and needed(config):
            findings.insert(0, 'Environment ' + env['status'] + ': ' + env['reason'])
        if any(g['status'] == 'blocked' for g in gates):
            return w1.gate('blocked', findings)
        if any(g['status'] == 'failed' for g in gates):
            return w1.gate('failed', findings, blocking=True)
        if findings:
            stop = config['ui']['optional_policy'] == 'stop'
            return w1.gate('warnings', findings, blocking=stop, owner=stop)
        return w1.gate('passed', [])
    except (w1.Invalid, KeyError, TypeError, ValueError) as error:
        return w1.gate('blocked', ['Product review cannot be accepted: ' + str(error)])


def finalize(config, captured, env, release, assessment, current):
    try:
        if current != captured:
            raise w1.Invalid('Candidate changed after review/cleanup')
        w1.obj(release, ('status', 'owner', 'session', 'reason'), 'release receipt')
        if release['owner'] != config['environment']['owner'] or release['owner'] != env['owner'] or release['session'] != env['session']:
            raise w1.Invalid('Release receipt does not bind the exact owned environment')
        if release['status'] not in ('released', 'not_needed', 'blocked', 'reconcile_required'):
            raise w1.Invalid('Invalid release status')
        if release['status'] in ('blocked', 'reconcile_required'):
            w1.text(release['reason'], 'cleanup failure')
            raise w1.Invalid('Cleanup ' + release['status'] + ': ' + release['reason'])
        if env['session'] is not None and release['status'] != 'released' or env['session'] is None and release['status'] != 'not_needed':
            raise w1.Invalid('Cleanup outcome does not match owned session')
        return assessment
    except (w1.Invalid, KeyError, TypeError) as error:
        return w1.gate('blocked', [str(error)] + assessment['findings'])


def worker(operation):
    envelope = json.load(sys.stdin)
    context = json.loads(Path(os.environ['PRIFLY_CONTEXT_FILE']).read_text())
    result = {'schema_version': '1', **{k: envelope[k] for k in ('run_id','step_instance_id','attempt_id')},
              'envelope_digest': os.environ['PRIFLY_ENVELOPE_DIGEST'], 'verdict': 'pass', 'outputs': {},
              'evidence_refs': [], 'effect_receipt_refs': [], 'summary': 'Product review ' + operation}
    def read(port):return json.loads(Path(context['inputs'][port]['path']).read_text())
    def digest(port):return w1.digest(Path(context['inputs'][port]['path']).read_bytes())
    def output(port, value):
        slot=context['outputs'][port];data=w1.encoded(value)+b'\n';Path(slot['path']).write_bytes(data)
        result['outputs'][port]={k:slot[k] for k in ('artifact_id','revision')};result['outputs'][port]['digest']=w1.digest(data)
    try:
        config=read('configuration');configuration(config)
        if operation=='configure':
            output('configuration',config)
            for lens in LENSES:output(lens,project(config,lens))
        elif operation=='capture':output('candidate',w1.snapshot(os.environ['PRIFLY_REPOSITORY_WORKSPACE'],config['ui']['base_commit']))
        elif operation in ('evaluate','finalize'):
            captured=read('candidate')
            try:
                current=w1.snapshot(os.environ['PRIFLY_REPOSITORY_WORKSPACE'],config['ui']['base_commit'])
                if operation=='evaluate':
                    assessment=evaluate(config,read('ui'),read('ux'),captured,read('environment'),{lens:read(lens+'_report') for lens in LENSES},current,digest('configuration'),{lens:digest(lens) for lens in LENSES})
                else:assessment=finalize(config,captured,read('environment'),read('release'),read('gate'),current)
            except (w1.Invalid,OSError,w1.subprocess.SubprocessError) as error:assessment=w1.gate('blocked',['Candidate cannot be assessed: '+str(error)])
            output('gate',assessment)
        else:raise w1.Invalid('Unknown product operation')
    except (ValueError,OSError,KeyError,TypeError,w1.subprocess.SubprocessError) as error:
        result.update(verdict='fail',outputs={},summary=str(error))
    os.write(3,w1.encoded(result)+b'\n')


if __name__=='__main__':worker(sys.argv[1])
