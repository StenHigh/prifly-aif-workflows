"""Controlled project binding timeout; shipped recipes and classic remain unchanged."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path('tests/probes').resolve()))
import call_review_check as probe

original_apply = probe.overlay.apply


def install_timed_fixture(repo, summary, changes):
    backup = original_apply(repo, summary, changes)
    file = repo / '.prifly/workflows/aif-classic/extend.yaml'
    value = json.loads(file.read_text())
    binding = value['execution_bindings']['steps']['w6-review-capture']
    binding['timeout_ms'] = 1500
    binding['args'] = ['-c', 'import time; time.sleep(3)']
    file.write_text(json.dumps(value))  # Explicitly sealed before prepare/start.
    return backup


original_collect = probe.collect_evidence


def collect(binary, authority, runs):
    value = original_collect(binary, authority, runs)
    state = probe.verify.run(binary, '--project', authority, 'run', 'status', runs[-1])['run']
    Path('/tmp/aif-w6-timeout-state.json').write_text(json.dumps(state))
    value['failed_invocations'] = [{k:v[k] for k in ('workflow_ref','status','outcome')} for v in state['invocations'].values() if v['status']=='failed']
    assert value['failed_invocations'] and state['outcome']=='rejected'
    outcomes = [a.get('process_outcome') for a in state['attempts'].values() if a['status']=='failed']
    assert outcomes and outcomes[-1]['started'], outcomes
    value['process_outcomes'] = outcomes
    value['diagnostics'] = state['diagnostics']
    return value


probe.overlay.apply = install_timed_fixture
probe.collect_evidence = collect
result = probe.case(Path('/tmp/aif-prifly-01380/prifly'), 'review', 'classic', 'program-timeout')
result['fixture_change'] = 'Project binding w6-review-capture: timeout_ms=1500 and explicit Python sleep(3) fixture command, sealed before prepare; canonical sources unchanged'
Path('/tmp/aif-w6-timeout80.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('evidence','live_sessions')}))
