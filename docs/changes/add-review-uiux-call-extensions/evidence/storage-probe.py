"""Finite storage rejection on W6; only a new owned fixture authority is seeded.

Initializer is built from unmodified released0.13.80 source. All tested controls
and workflow execution use the official released0.13.80 binary. Recovery is an
explicit controlled-owner prepare/set, never a recipe action.
"""
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path('tests/probes').resolve()))
import call_review_check as probe

BINARY=Path('/tmp/aif-prifly-01380/prifly')
original_prepare=probe.verify.prepare_repository
original_run=probe.verify.run
original_clean=probe.clean
active_authority=None
observation=None

class StorageObserved(Exception):
    pass


def prepare(binary, root):
    global active_authority
    active_authority=root/'authority'
    subprocess.run(['/tmp/aif-w6-storage-init',str(active_authority),str(8*1024*1024)],check=True,capture_output=True,text=True)
    return original_prepare(binary,root)


def run(binary,*args,**kwargs):
    global observation
    try:
        return original_run(binary,*args,**kwargs)
    except AssertionError as error:
        if 'storage_budget_exhausted' not in str(error) or observation is not None:
            raise
        authority=active_authority
        before=original_run(binary,'--project',authority,'storage','budget','show')
        runs=original_run(binary,'--project',authority,'run','list')['runs']
        snapshots={r['run_id']:original_run(binary,'--project',authority,'run','status',r['run_id'])['run'] for r in runs}
        reason='Controlled W6 fixture owner: retain accepted evidence, settle and clean this isolated authority'
        review=original_run(binary,'--project',authority,'storage','budget','set','--bytes',str(64*1024*1024),'--reason',reason,'--prepare')
        raised=original_run(binary,'--project',authority,'storage','budget','set','--bytes',str(64*1024*1024),'--reason',reason,'--expected-review-digest',review['review_digest'],'--command','command:w6-fixture-storage-recovery')
        after=original_run(binary,'--project',authority,'storage','budget','show')
        preserved=[]
        for rid,old in snapshots.items():
            new=original_run(binary,'--project',authority,'run','status',rid)['run']
            accepted=lambda s:{k:v['accepted'] for k,v in s['attempts'].items() if v.get('accepted')}
            assert accepted(old)==accepted(new)
            preserved.append({'run_id':rid,'accepted_attempts':len(accepted(old)),'accepted_prefix_unchanged':True,'outcome':new.get('outcome')})
        observation={'code':'storage_budget_exhausted','blocked_command':[str(a) for a in args],'before':before,'owner_review':review,'explicit_owner_set':raised,'after':after,'preserved':preserved,'recipe_raised_budget':False,'fixture_initializer_source_release':'v0.13.80'}
        raise StorageObserved()


def clean(binary,authority,runs):
    all_runs=original_run(binary,'--project',authority,'run','list')['runs']
    return original_clean(binary,authority,[r['run_id'] for r in all_runs])


probe.verify.prepare_repository=prepare
probe.verify.run=run
probe.clean=clean
try:
    probe.case(BINARY,'combined','classic','storage-ceiling')
    raise AssertionError('W6 fixture did not reach the finite ceiling')
except StorageObserved:
    assert observation is not None
    observation['cleaned']=True
    Path('/tmp/aif-w6-storage80.json').write_text(json.dumps(observation,indent=2)+'\n')
    print(json.dumps({'outcome':'passed','code':observation['code'],'blocked_command':observation['blocked_command'],'preserved':observation['preserved'],'cleaned':True}))
