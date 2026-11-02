#!/usr/bin/env python3
"""Actual shipping /5 points on released Core; scripted host, real Git/check/artifacts.

This is native transport qualification. It does not attest an LLM judgement or
private application/browser acceptance. Each fixture owns and cleans its Run.
"""
import argparse, copy, hashlib, json, re, shutil, subprocess, sys, tempfile
from contextlib import contextmanager
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verify
import run_check as host
from readability_compare import input_value, submit
from verify_outcomes import start


@contextmanager
def owned_fixture(prefix):
 root=Path(tempfile.mkdtemp(prefix=prefix))
 try:
  yield root
 except BaseException:
  print('Preserved failed native fixture: '+str(root),file=sys.stderr)
  raise
 else:
  shutil.rmtree(root)


def digest(raw):return 'sha256:'+hashlib.sha256(raw).hexdigest()

def write(root,path,value):
 p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+'\n')


def configure(folder,package,disabled=False):
 points=json.loads((folder/'extension-points.yaml').read_text())['points']
 point='before-quality' if package=='aif-fix' else 'before-verify'
 ports={'schema_ref':'{{contract_schema_implementation}}'}
 write(folder,'project/contexts/measurement.yaml',{'id':'acceptance:context/measurement','version':'1.0.0','media_type':'text/plain','text':'Project-owned check. Preserve exact original ArtifactRefs; return new implementation with report/log refs. Scripted acceptance host; no LLM judgement.'})
 write(folder,'project/schemas/report.yaml',{'id':'acceptance:schema/report','version':'1.0.0','type':'object'})
 write(folder,'project/steps/measurement.yaml',{'authoring':'prifly-step/2','id':'acceptance:step/measurement','version':'1.0.0','title':'Project measurement before the reader','kind':'worker','repository_workspace':'read_only','inputs':{'implementation':ports,'task':{'schema_ref':'{{contract_schema_task}}'}},'outputs':{'implementation':{**ports,'required_for':['pass']},'report':{'schema_ref':'{{schema_report}}','required_for':['pass']},'log':{'schema_ref':'{{schema_report}}','required_for':['pass']}},'executor':{'adapter_ref':'{{assisted_adapter}}','operation':'session'},'instructions_ref':'{{context_measurement}}','effects':{'class':'external_write','retry_class':'never'},'external_write':{'system':'acceptance-measurement','operations':['measure'],'target':'Only this isolated fixture candidate; output reports stay in reserved slots.'},'result_schema_ref':'{{step_result_schema_v2}}'})
 ext={'id':'measure','point':point,'step':'measurement','output_bindings':{k:'implementation' for k in points[point]['consumers']}}
 if disabled:ext['enabled']=False
 write(folder,'extend.yaml',{'authoring':'prifly-extension/5','profile':'default' if package=='aif-fix' else 'fast','exclude':[] if package=='aif-fix' else ['improve'],'extensions':[ext]})
 return ext


def case(binary,package,scenario):
 with owned_fixture(prefix='unified-aif-') as tmp:
  root=Path(tmp);repo,authority=verify.prepare_repository(binary,root)
  runs=[];seen=[];reports=[];measurements=[];readers=[];repairs=0;current=None;original_source=None;refusals=[]
  def call(*args,**kw):return verify.run(binary,'--project',authority,*args,**kw)
  def status(rid):
   v=call('run','status',rid);return {k:v[k] for k in ('run_version','run')}
  def export(ref):
   f=root/'reference.json';out=root/'export.json';f.write_text(json.dumps(ref));out.unlink(missing_ok=True)
   call('artifact','export','--ref',f,'--output',out);raw=out.read_bytes();assert digest(raw)==ref['digest'];return json.loads(raw)
  try:
   # Isolated installation also verifies profiled works without classic.
   for p in (repo/'.prifly/workflows').iterdir():shutil.rmtree(p)
   folder=repo/'.prifly/workflows'/package;shutil.copytree(verify.ROOT/package,folder)
   profile=repo/'.prifly/project.yaml';s=profile.read_text()
   s=re.sub(r'(?ms)^packages:\n.*?(?=^\S|\Z)',f'packages:\n  {package}:\n    source: .prifly/workflows/{package}\n',s)
   s=re.sub(r'(?ms)^launches:\n.*?(?=^\S|\Z)',f'launches:\n  {package}:\n    title: Unified measurement acceptance\n    description: Scripted native acceptance on actual shipping workflow.\n    kind: workflow\n    workflow: .prifly/workflows/{package}/workflow.yaml\n',s);profile.write_text(s)
   extension=configure(folder,package,scenario=='disabled')
   taskfile=root/'task.json';taskfile.write_text(json.dumps({'title':'Add greeting','description':'Add hello.txt and preserve project measurement reports.'}))
   verify.git('-C',repo,'add','-A');verify.git('-C',repo,'commit','-qm','Configure unified acceptance')
   if package=='aif-fix':raise AssertionError('fix controller not implemented')
   rid=start(binary,authority,repo,package,taskfile);runs.append(rid)
   for turn in range(48):
    call('run','drive',rid);tasks=call('session','task','--run',rid,'--all')['tasks']
    if not tasks:
     state=call('run','status',rid)['run']
     if scenario=='continue' and len(runs)==1:
      assert state['outcome']=='partial',state
      original_source=status(rid)
      tree=Path(next(m['tree'] for m in measurements));(tree/'hello.txt').write_text('hello owner correction\n')
      args=('project','continue','--repository',repo,'--launch',package,'--source-run',rid,'--host','codex-cli')
      prep=call(*args,'--prepare');assert prep['recovery']['frontier_stage_id']=='verify'
      assert status(rid)==original_source
      rid=call(*args,'--expected-launch-digest',prep['review_digest'])['run']['run']['id'];runs.append(rid);continue
     raise AssertionError(('ended before reader boundary',state))
    for task in tasks:
     role=task['skill_refs'][0]['id'].rsplit('/',1)[-1];seen.append(role)
     if role=='measurement':
      incoming=input_value(task,'implementation');tree=Path(task['repository_workspace'])
      # Real regression command on this exact claimed candidate.
      result=subprocess.run([sys.executable,'-c',"from pathlib import Path; assert Path('hello.txt').read_text().startswith('hello')"],cwd=tree,capture_output=True,text=True,timeout=10)
      slots=call('session','submit','--template','--run',rid,'--attempt',task['attempt_id'])['result']['outputs']
      log={'stdout':result.stdout,'stderr':result.stderr,'exit':result.returncode}
      lograw=json.dumps(log).encode();logref={**slots['log'],'digest':digest(lograw)}
      report={'subject':{'head':host.git_out(tree,'rev-parse','HEAD'),'content_sha256':digest((tree/'hello.txt').read_bytes())},'basis':'acceptance:greeting-v1','method':'python startswith assertion','exit':result.returncode,'status':'passed' if result.returncode==0 else 'failed','logs':[logref]}
      reportref={**slots['report'],'digest':digest(json.dumps(report).encode())}
      current={**incoming,'reports':incoming.get('reports',[])+[reportref]}
      submit(binary,authority,rid,task,'pass',{'log':log,'report':report,'implementation':current})
      reports.append(reportref);measurements.append({'ref':reportref,'report':report,'tree':str(tree),'attempt':task['attempt_id'],'run':rid,'effects':task.get('permitted_effects')})
      # Consumers must survive removal of the producing Attempt directory.
      shutil.rmtree(task['workspace'])
      continue
     if role=='aif-verify-bridge':
      incoming=input_value(task,'implementation')
      if scenario=='disabled':assert 'reports' not in incoming
      else:
       assert incoming==current,(role,incoming,current)
       assert export(incoming['reports'][-1])==measurements[-1]['report']
       assert export(measurements[-1]['report']['logs'][0])['exit']==0
      if scenario=='permissions':
       tree=Path(task['repository_workspace']);original=(tree/'hello.txt').read_bytes()
       (tree/'hello.txt').write_text('unauthorised reader write\n')
       try:
        try:submit(binary,authority,rid,task,'pass',{'gate':host.GATE_PASSED})
        except AssertionError as error:
         assert 'effect_not_permitted' in str(error),str(error);refusals.append('effect_not_permitted')
        else:raise AssertionError('read-only write accepted')
       finally:(tree/'hello.txt').write_bytes(original)
       for mutation,expected in [({'digest':'sha256:'+'0'*64},'integrity_failure'),({'artifact_id':'artifact:'+'0'*64},'not_found'),({'revision':999999},'integrity_failure')]:
        ref={**reports[-1],**mutation};f=root/'negative-ref.json';f.write_text(json.dumps(ref))
        error=call('artifact','export','--ref',f,'--output',root/'negative-export',expect_ok=False)
        code=json.loads(error.strip().splitlines()[-1])['code'];assert code==expected,(mutation,code,expected);refusals.append(code)
      readers.append({'attempt':task['attempt_id'],'run':rid,'implementation':incoming})
      blocked=scenario=='blocked' or scenario=='continue' and len(runs)==1
      repair=scenario=='repair' and repairs==0
      gate=copy.deepcopy(host.GATE_BLOCKED if blocked else host.GATE_PASSED)
      if repair:gate.update(status='failed',blocking=True,findings=['Controlled repair needed'],suggested_next='/aif-fix')
      submit(binary,authority,rid,task,'blocked' if blocked else 'needs_revision' if repair else 'pass',{'gate':gate});continue
     if role=='aif-fix-bridge':
      incoming=input_value(task,'implementation');assert incoming==current
      tree=Path(task['repository_workspace']);(tree/'hello.txt').write_text('hello repaired\n');host.git_out(tree,'add','hello.txt');host.git_out(tree,'-c','user.name=probe','-c','user.email=probe@example.invalid','commit','-qm','Repair greeting')
      current={**incoming,'head_commit':host.git_out(tree,'rev-parse','HEAD')};repairs+=1
      submit(binary,authority,rid,task,'pass',{'implementation':current});continue
     if role=='aif-security-bridge':
      incoming=input_value(task,'implementation');assert incoming==current
      if scenario=='repair':assert len(measurements)==2 and reports[0]!=reports[1] and measurements[0]['report']['subject']!=measurements[1]['report']['subject']
      elif scenario=='continue':assert len(runs)==2 and len(measurements)==2 and reports[0]!=reports[1];assert status(runs[0])==original_source
      elif scenario=='disabled':assert not measurements
      else:assert len(measurements)==1
      return {'package':package,'case':scenario,'runs':runs,'measurement_count':len(measurements),'reader_count':len(readers),'repair_count':repairs,'refusals':refusals,'measurements':measurements,'readers':readers,'boundary':'Reached real downstream security reader with exact latest carrier; synthetic assessments, no commit or live LLM claimed.'}
     _,verdict,values=host.answer(task,'pass');assert verdict is not None,role
     if role=='aif-implement-bridge':current=values['implementation']
     submit(binary,authority,rid,task,verdict,values)
   raise AssertionError('turn limit')
  finally:
   host.clean(binary,authority,runs)
   assert not any(c['status']=='active' for c in call('claim','list')['claims'])
   verify.forget_authority(authority)


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',required=True,type=Path);p.add_argument('--package',choices=['aif-classic','aif-profiled'],default='aif-classic');p.add_argument('--case',choices=['clean','repair','disabled','continue','permissions'],default='repair');p.add_argument('--report',type=Path);a=p.parse_args()
 result=case(a.binary.resolve(strict=True),a.package,a.case);result.update(binary_sha256=digest(a.binary.read_bytes()),prifly=verify.run(a.binary,'version')['version'],cleaned=True)
 if a.report:a.report.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('measurements','readers')}))
if __name__=='__main__':main()
