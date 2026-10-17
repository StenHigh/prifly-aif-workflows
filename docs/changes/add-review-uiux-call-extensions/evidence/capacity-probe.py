"""A W6 reader holds the one finite admission slot; another Run must queue."""
import json
from pathlib import Path
import sys
sys.path[:0]=[str(Path('tests/probes').resolve()),str(Path('tests').resolve())]
import call_review_check as probe
from compatibility import launch_answers

original_prepare=probe.verify.prepare_repository
original_submit=probe.Host.submit
original_clean=probe.clean
repository=None
observed=None

class CapacityObserved(Exception):
    pass


def prepare(binary,root):
    global repository
    repository,authority=original_prepare(binary,root)
    probe.verify.run(binary,'--project',authority,'capacity','set','--capacity','1','--reason','Controlled W6 fixture owner: test finite admission capacity')
    return repository,authority


def submit(self,rid,task,verdict,values,omit=False):
    global observed
    if observed is None and task['skill_refs'][0]['id'].endswith('/w6-review-review-bridge'):
        binary=self.binary;authority=self.authority
        capacity=probe.verify.run(binary,'--project',authority,'capacity','show')
        taskfile=repository.parent/'second-task.json';taskfile.write_text(json.dumps({'title':'Another independent feature','description':'Must queue while the W6 reader holds capacity'}))
        args=['--project',authority,'project','start','--repository',repository,'--launch','aif-classic','--host','codex-cli','--workspace','worktree','--input','task='+str(taskfile),'--allow-execution']
        answers,digest=launch_answers(binary,authority,repository,None);args+=answers+['--expected-decision-catalog-digest',digest]
        preview=probe.verify.run(binary,*args[:3],'questionnaire',*args[4:],'--prepare')
        refused=probe.verify.run(binary,*args,'--expected-launch-digest',preview['review_digest'],expect_ok=False)
        assert 'capacity_conflict' in refused,refused
        runs=probe.verify.run(binary,'--project',authority,'run','list')['runs']
        others=[r['run_id'] for r in runs if r['run_id']!=rid];assert len(others)==1
        queued=probe.verify.run(binary,'--project',authority,'run','status',others[0])['run']
        assert not queued['active_attempt_ids'] and not queued['attempts']
        after=probe.verify.run(binary,'--project',authority,'capacity','show')
        observed={'code':'capacity_conflict','held_by_w6_reader':task['attempt_id'],'before':capacity,'after':after,'queued_run_id':others[0],'queued_attempts':0,'recipe_increased_capacity':False}
        raise CapacityObserved()
    return original_submit(self,rid,task,verdict,values,omit)


def clean(binary,authority,runs):
    all_runs=probe.verify.run(binary,'--project',authority,'run','list')['runs']
    return original_clean(binary,authority,[r['run_id'] for r in all_runs])


probe.verify.prepare_repository=prepare
probe.Host.submit=submit
probe.clean=clean
try:
    probe.case(Path('/tmp/aif-prifly-01380/prifly'),'combined','classic','pass')
    raise AssertionError('Expected finite capacity observation')
except CapacityObserved:
    assert observed is not None
    Path('/tmp/aif-w6-capacity80.json').write_text(json.dumps({'observation':observed,'parent_boundary':'Paused at its W6 reader; both controlled Runs cancelled/settled for cleanup. No fairness/completion claim for concurrent Runs.','cleaned':True},indent=2)+'\n')
    print(json.dumps({'code':observed['code'],'queued_attempts':0,'recipe_increased_capacity':False,'cleaned':True}))
