#!/usr/bin/env python3
"""Project /5 measurement on shipping fix, using real regression/repair/Run artifacts."""
import argparse,hashlib,json,shutil,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verify
import fix_check
from readability_compare import submit,input_value
from unified_measurement import configure,digest,owned_fixture


def case(binary,scenario):
 with owned_fixture(prefix='unified-fix-') as tmp:
  root=Path(tmp);repo,authority=verify.prepare_repository(binary,root);runs=[];reports=[];checks=[];seen=[];current=None
  actor=fix_check.Host(binary,authority,'repair-check' if scenario=='repair' else 'direct','default')
  def call(*args):return verify.run(binary,'--project',authority,*args)
  def export(ref):
   f=root/'ref.json';f.write_text(json.dumps(ref));out=root/'export';out.unlink(missing_ok=True);call('artifact','export','--ref',f,'--output',out);raw=out.read_bytes();assert digest(raw)==ref['digest'];return json.loads(raw)
  try:
   (repo/'calc.py').write_text(fix_check.BAD);(repo/'tracked.txt').write_text('original\n')
   folder=repo/'.prifly/workflows/aif-fix';configure(folder,'aif-fix',scenario=='disabled')
   verify.git('-C',repo,'add','-A');verify.git('-C',repo,'commit','-qm','Configure /5 fix acceptance')
   taskfile=root/'task.json';taskfile.write_text(json.dumps({'title':'Fix arithmetic offset','description':'total(2) must be 2; None means zero.'}))
   options=('--repository',repo,'--launch','aif-fix','--host','codex-cli','--workspace','worktree','--package-profile','default','--input',f'task={taskfile}','--preflight-answer','short_checks=""','--preflight-answer','gate_warnings="ignore"','--runtime-answer','fix_plan_execution=true')
   prep=call('project','questionnaire',*options,'--prepare');rid=call('project','start',*options,'--expected-launch-digest',prep['review_digest'])['run']['run']['id'];runs.append(rid)
   for turn in range(80):
    call('run','drive',rid);tasks=call('session','task','--run',rid,'--all')['tasks']
    if not tasks:
     state=call('run','status',rid)['run'];assert state['outcome']=='succeeded',state
     final=export(state['output_artifacts']['implementation'])
     if scenario=='disabled':assert not reports and 'reports' not in final
     else:
      assert final['reports']==reports
      assert len(reports)==(2 if scenario=='repair' else 1)
      assert [x['exit'] for x in checks]==([1,0] if scenario=='repair' else [0])
      for ref,original in zip(reports,checks):assert export(ref)==original
     return {'package':'aif-fix','case':scenario,'runs':runs,'status':state['status'],'outcome':state['outcome'],'reports':reports,'checks':checks,'seen':seen,'original_reports_preserved':True,'boundary':'Scripted host, actual regression commands and native repaired shipping graph; no live LLM judgement claimed.'}
    for task in tasks:
     role=task['skill_refs'][0]['id'].rsplit('/',1)[-1].removesuffix('-bridge');seen.append(role)
     if role=='measurement':
      incoming=input_value(task,'implementation');tree=Path(task['repository_workspace'])
      rc,text=fix_check.command(tree)
      slots=call('session','submit','--template','--run',rid,'--attempt',task['attempt_id'])['result']['outputs']
      log={'exit':rc,'raw':text};logref={**slots['log'],'digest':digest(json.dumps(log).encode())}
      report={'subject':{'head':fix_check.git_out(tree,'rev-parse','HEAD'),'calc_sha256':digest((tree/'calc.py').read_bytes())},'basis':'acceptance:total(2)==2','method':'python assertion','exit':rc,'status':'failed' if rc else 'passed','logs':[logref]}
      ref={**slots['report'],'digest':digest(json.dumps(report).encode())};current={**incoming,'reports':incoming.get('reports',[])+[ref]}
      submit(binary,authority,rid,task,'pass',{'implementation':current,'report':report,'log':log});checks.append(report);reports.append(ref);shutil.rmtree(task['workspace']);continue
     actor.seen.append({'step':role,'run':rid})
     if role in ('check-change','aif-security','review-task','repair') and scenario!='disabled':assert input_value(task,'implementation')==current
     if role=='check-change' and scenario!='disabled':
      report=export(reports[-1]);assert report==checks[-1]
      verdict,values='pass',{'gate':fix_check.gate('verify',failed=bool(report['exit']),findings=['Original declared regression report failed'] if report['exit'] else [])}
     else:verdict,values=actor.answer(task,role)
     if 'implementation' in values:
      if 'implementation' in task['context']['inputs']:
       inherited=input_value(task,'implementation').get('reports')
       if inherited is not None:values['implementation']['reports']=inherited
      current=values['implementation']
     assert not actor.submit(rid,task,verdict,values)
   raise AssertionError('turn limit')
  finally:
   fix_check.clean(binary,authority,runs)
   assert not any(c['status']=='active' for c in call('claim','list')['claims'])
   verify.forget_authority(authority)


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',required=True,type=Path);p.add_argument('--case',choices=['clean','repair','disabled'],default='repair');p.add_argument('--report',type=Path);a=p.parse_args();result=case(a.binary.resolve(),a.case);result.update(binary_sha256=digest(a.binary.read_bytes()),prifly=verify.run(a.binary,'version')['version'],cleaned=True)
 if a.report:a.report.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('checks','seen')}))
if __name__=='__main__':main()
