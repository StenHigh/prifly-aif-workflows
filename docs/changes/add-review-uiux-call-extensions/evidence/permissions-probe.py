"""W6 native root limits, policy and program consent/allowlist refusals."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
sys.path[:0]=[str(Path('tests').resolve()),str(Path('examples/review-uiux-extensions').resolve())]
import verify,install

binary=Path('/tmp/aif-prifly-01380/prifly');results=[]
with tempfile.TemporaryDirectory(prefix='w6-permissions-') as temporary:
 root=Path(temporary);repo,authority=verify.prepare_repository(binary,root)
 try:
  folder=repo/'.prifly/workflows/w6-consumer';shutil.copytree(install.HERE/'consumer',folder)
  profile_path=repo/'.prifly/project.yaml';profile=install.load(profile_path.read_text());profile['packages']['w6-consumer']={'source':'.prifly/workflows/w6-consumer'};profile['launches']['w6-consumer']={'title':'Controlled limits','description':'No actors dispatched','kind':'workflow','workflow':'.prifly/workflows/w6-consumer/workflow.yaml'};profile_path.write_text(json.dumps(profile))
  summary,changes=install.plan(repo,'w6-consumer',install.HERE/'configurations/combined.json','combined','write','commit','abandoned','done','implementation');install.apply(repo,summary,changes)
  rootfile=folder/'workflow.yaml';canonical=rootfile.read_bytes();extendfile=folder/'extend.yaml';overlay=extendfile.read_bytes();reader=folder/'project/steps/w6-review-review.yaml';canonical_reader=reader.read_bytes()
  verify.run(binary,'--project',authority,'project','local','set','--repository',repo,'--allow-executable','python='+str(Path(sys.executable).resolve()))
  compile_args=['--project',authority,'project','compile','--repository',repo,'--package','w6-consumer','--host','codex-cli']
  for field,value in [('max_child_depth',1),('max_step_instances',1),('max_control_transitions',1)]:
   data=json.loads(canonical);data['limits'][field]=value;rootfile.write_text(json.dumps(data))
   refused=verify.run(binary,*compile_args,'--output',root/field,expect_ok=False);problem=json.loads(refused.strip().splitlines()[-1]);assert problem['code']=='limit_exceeded',problem
   assert not (root/field/'prifly.package.json').exists()
   results.append({'case':field,'code':problem['code'],'dispatched':False})
  rootfile.write_bytes(canonical)
  verify.git('-C',repo,'add','.');verify.git('-C',repo,'commit','-qm','Explicit W6 project fixture')
  base=__import__('subprocess').check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip();task=root/'task.json';task.write_text(json.dumps({'title':'No execution','description':'Permission denial probe','base_commit':base}))
  args=['--project',authority,'project','questionnaire','--repository',repo,'--launch','w6-consumer','--host','codex-cli','--workspace','worktree','--input','task='+str(task),'--prepare']
  refused=verify.run(binary,*args,expect_ok=False);problem=json.loads(refused.strip().splitlines()[-1]);assert problem['code']=='project_execution_approval_required',problem;results.append({'case':'missing-execution-consent','code':problem['code'],'dispatched':False})
  data=json.loads(overlay);data['execution_bindings']['steps']['w6-combined-prepare']['executable']='untrusted';extendfile.write_text(json.dumps(data))
  refused=verify.run(binary,*args,'--allow-execution',expect_ok=False);problem=json.loads(refused.strip().splitlines()[-1]);assert problem['code']=='project_execution_not_allowed',problem;results.append({'case':'untrusted-executable','code':problem['code'],'dispatched':False});extendfile.write_bytes(overlay)
  data=json.loads(canonical);data['package']['references']['policy']='core:policy/local@1.0.0';rootfile.write_text(json.dumps(data))
  refused=verify.run(binary,*args,'--allow-execution',expect_ok=False);problem=json.loads(refused.strip().splitlines()[-1]);assert problem['code']=='resource_limit',problem;results.append({'case':'parent-policy-not-escalated-by-child','code':problem['code'],'dispatched':False});rootfile.write_bytes(canonical)
  data=json.loads(canonical_reader);data['effects']={'class':'destructive','retry_class':'never'};reader.write_text(json.dumps(data))
  refused=verify.run(binary,*args,'--allow-execution',expect_ok=False);problem=json.loads(refused.strip().splitlines()[-1]);assert problem['code']=='unsupported',problem;results.append({'case':'destructive-effect-refused','code':problem['code'],'dispatched':False});reader.write_bytes(canonical_reader)
  assert not verify.run(binary,'--project',authority,'run','list')['runs']
  assert rootfile.read_bytes()==canonical
  Path('/tmp/aif-w6-permissions80.json').write_text(json.dumps({'cases':results,'root_restored':True,'runs':0,'prifly':'0.13.80'},indent=2)+'\n');print(json.dumps(results))
 finally:verify.forget_authority(authority)
