"""Run fresh Codex CLI reader Attempts against the published aif-fix 1.0.2.

Reader verdicts are chosen by actual LLM hosts, never by the controller.
Warmup/fix/commit are deterministic fixture setup. This manual probe uses the
user-configured Codex model and real AI Factory 2.19.0 skills.
"""
import argparse,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verify
from fix_check import Host,BAD,git_out
from run_check import clean
BINARY=SKILLS=ARTIFACTS=None
CORE_VERSION=None
COMMIT='0e93c36672e23ac404463f815cb89c7c3ffe31fe'
GATES={'check-change':'verify','aif-security':'security','review-task':'review'}

def digest(p):return 'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()

def read_llm(h,task,step,number):
 workspace=Path(task['workspace']); (workspace/'task.json').write_text(json.dumps(task,indent=2))
 template=h.call('session','submit','--template','--run',task['run_id'],'--attempt',task['attempt_id'])
 (workspace/'submission-template.json').write_text(json.dumps(template,indent=2))
 prompt=f'''You are the host executing exactly one delivered Pri-Fly assisted-session Attempt.
Read {workspace/'task.json'} and every delivered instruction/context in its skill_refs and context_refs. Read the bound input artifacts and submission-template.json. Follow this Attempt's sealed bridge and supporting skills, including project config and skill-context. Inspect the actual repository_workspace read-only and run applicable required commands. This is an isolated Python repository; no external network or dependency installation is needed.
The claimed repository is read-only for this Attempt: do not fix code, edit policy, restore resources, run the next stage, commit, or write review/audit files into the repository. Output artifacts and the report belong only in the allocated task workspace, as the task specifies.
Derive your own verdict, gate, findings and summary from the instructions and observed facts. The controller supplies no expected verdict. Report unperformed checks honestly. Use the given template unchanged for authority/identity fields; write your gate to the allocated output port path, compute its actual SHA-256 digest, and write a complete submission.json under {workspace}. Answer questions/model_profile only according to what actually happened and the declared contracts. For a model profile, this is a new CLI session without author conversation, but no project mapping of independent-review to a different model has been supplied; do not invent such a mapping or another model.
Submission protocol for model_profile, only if task declares it: outcome is honoured, unavailable or declined. Honoured requires a nonempty named model and no reason. Unavailable/declined require a nonempty dedicated reason and no named model; a reason only in gate.findings does not satisfy this field. Select the outcome from observed host capability; these are serialization constraints, not a requested assessment.
Do not invoke Pri-Fly submit/drive/start/continue. The controller will submit your exact file without editing it. Finish with the paths you wrote. No expected gate or test assertion is available to you.'''
 prefix=ARTIFACTS/f'{h.target}-{number:02d}-{step}'
 (prefix.with_suffix('.prompt.txt')).write_text(prompt)
 before=h.snapshot();version=h.call('run','status',task['run_id'])['run_version']
 with prefix.with_suffix('.events.jsonl').open('w') as out,prefix.with_suffix('.stderr.txt').open('w') as err:
  proc=subprocess.run(['codex','exec','--ephemeral','--json','--sandbox','workspace-write','-C',str(workspace),'--skip-git-repo-check','-o',str(workspace/'host-final.txt'),'-'],input=prompt,text=True,stdout=out,stderr=err,timeout=600)
 assert proc.returncode==0,(proc.returncode,prefix.with_suffix('.stderr.txt').read_text()[-2500:])
 assert h.snapshot()==before,'reader changed claimed tree'
 assert h.call('run','status',task['run_id'])['run_version']==version,'host mutated authority'
 report=workspace/'submission.json';data=json.loads(report.read_text())
 gate_path=workspace/task['context']['outputs']['gate']['path'];gate=json.loads(gate_path.read_text())
 assert data['result']['outputs']['gate']['digest']==digest(gate_path)
 shutil.copyfile(report,prefix.with_suffix('.submission.json'));shutil.copyfile(gate_path,prefix.with_suffix('.gate.json'))
 (prefix.with_suffix('.task.json')).write_text(json.dumps(task,indent=2))
 done=subprocess.run([str(BINARY),'--json','--project',str(h.authority),'session','submit','--file',str(report)],capture_output=True,text=True,timeout=120)
 (prefix.with_suffix('.receipt.json')).write_text(done.stdout or done.stderr)
 assert done.returncode==0,done.stderr
 receipt=json.loads(done.stdout);assert not (receipt.get('receipt') or {}).get('rejection'),receipt
 # Assertions are in the controller, after the unedited submission was accepted.
 accepted={'step':step,'attempt_id':task['attempt_id'],'run_id':task['run_id'],'verdict':data['result']['verdict'],'gate':gate,'gate_digest':digest(gate_path),'report_digest':digest(report),'tree_unchanged':True,'model_profile':data.get('model_profile'),'event_file':prefix.with_suffix('.events.jsonl').name}
 h.live.append(accepted)
 print(json.dumps({'target':h.target,'phase':h.phase,'step':step,'verdict':accepted['verdict'],'gate_status':gate['status'],'gate_digest':accepted['gate_digest']},ensure_ascii=False),flush=True)
 return accepted

class ReaderHost(Host):
 def __init__(self,*args,target,dependency):
  super().__init__(*args);self.target=target;self.dependency=dependency;self.live=[];self.phase='source';self.counter=0;self.setup=[]
 def drive_live(self,rid):
  for _ in range(80):
   self.call('run','drive',rid);tasks=self.call('session','task','--run',rid,'--all')['tasks']
   if not tasks:return self.call('run','status',rid)['run']
   for task in tasks:
    step=task['skill_refs'][0]['id'].rsplit('/',1)[-1].removesuffix('-bridge')
    self.seen.append({'run':rid,'step':step});self.tree=Path(task['repository_workspace'])
    self.generations.append(task['claim_generation']);self.claims.add(task['claim_id'])
    if step in GATES:
     self.counter+=1;read_llm(self,task,step,self.counter)
    else:
     verdict,values=self.answer(task,step);refused=self.submit(rid,task,verdict,values);assert not refused,refused
     self.setup.append({'step':step,'verdict':verdict,'mode':'deterministic setup/commit, not a reader verdict'})
     if step=='fix-task':
      self.dependency.unlink()
      (self.tree/'owner.txt').write_text('Preserve this dirty owner work.\n')
      (self.tree/'owner-scratch.txt').write_text('Preserve this untracked owner work.\n')
  raise AssertionError('Run did not settle')

def run(target):
 with tempfile.TemporaryDirectory(prefix='aif-fix-live-reader-') as tmp:
  root=Path(tmp);repo,authority=verify.prepare_repository(BINARY,root);external=root/'external';external.mkdir();dependency=external/'control.txt';dependency.write_text('fixture-control-v1\n')
  h=ReaderHost(BINARY,authority,'direct','default',target=target,dependency=dependency)
  try:
   h.call('project','workflows','remove','aif-fix','--repository',repo)
   installed=h.call('project','workflows','add','StenHigh/prifly-aif-workflows','--path','aif-fix','--ref','v1.51.2','--repository',repo)
   assert installed['origin']['commit']==COMMIT
   for name in ('aif-warmup','aif-fix','aif-security-checklist','aif-review','aif-commit'):
    dst=repo/'.codex/skills'/name;shutil.rmtree(dst);shutil.copytree(SKILLS/name,dst)
   (repo/'calc.py').write_text(BAD);(repo/'owner.txt').write_text('Original owner file.\n')
   (repo/'client_a.py').write_text('from calc import total\ndef price():\n    return total(2)\n')
   (repo/'client_b.py').write_text('from calc import total\ndef empty():\n    return total(None)\n')
   (repo/'regression.py').write_text('from calc import total\nfrom client_a import price\nfrom client_b import empty\nassert total(None) == 0\nassert total(0) == 0\nassert total(2) == 2\nassert price() == 2\nassert empty() == 0\nprint("PASS total and both consumers")\n')
   (repo/'required_check.py').write_text(f'from pathlib import Path\ncontrol = Path({str(dependency)!r})\nassert control.read_text() == "fixture-control-v1\\n"\nprint("PASS required external control")\n')
   (repo/'.gitignore').write_text('.env\n__pycache__/\n*.pyc\n')
   context=repo/'.ai-factory';context.mkdir(exist_ok=True)
   (context/'DESCRIPTION.md').write_text(f'''# Arithmetic library fixture\nExpected behavior: total(None)=0; other numbers unchanged. Two consumers use total.\nRegression: python3 -B regression.py. This is a Python standard-library project, with no dependency manifests, network, authentication, database, financial transactions, browser or deployment surface.\nThe {target} stage must additionally run `python3 -B required_check.py`. This is a mandatory in-scope control for that stage; it reads a fixture-managed file outside the claimed tree. The file is maintained by the environment owner, not by readers or repair. That control is not an optional acceptance deferred until publication. Other stages perform their own normal checks and do not require this additional control.\nOwner files owner.txt and owner-scratch.txt belong to separate work and must remain unchanged/uncommitted.\n''')
   (context/'ARCHITECTURE.md').write_text('# Architecture\nOne pure arithmetic module; two consumers. Gates read code; environment owns the external control.\n')
   (context/'RULES.md').write_text('# Rules\nPreserve unrelated owner work. Reader stages are read-only. Do not create or modify external control data.\n')
   (context/'config.yaml').write_text('language: {ui: en, artifacts: en}\n')
   verify.git('-C',repo,'add','-A');verify.git('-C',repo,'commit','-q','-m','Live reader fixture with frozen acceptance contract')
   task=root/'task.json';task.write_text(json.dumps({'title':'Correct arithmetic offset','description':'total currently subtracts one. None must yield zero and other inputs remain unchanged. Follow DESCRIPTION.md required checks for their declared stages; preserve unrelated owner work.'}))
   q=h.call('project','questionnaire','--repository',repo,'--launch','aif-fix')
   start=h.call('project','start','--repository',repo,'--launch','aif-fix','--host','codex-cli','--workspace','worktree','--input',f'task={task}','--preflight-answer','short_checks=""','--preflight-answer','gate_warnings="ignore"','--runtime-answer','fix_plan_execution=true','--expected-decision-catalog-digest',q['catalog_digest'])
   rid=start['run']['run']['id'];h.runs.append(rid);source=h.drive_live(rid)
   assert source['outcome']=='partial',source
   last=h.live[-1];assert last['step']==target and last['verdict']=='pass',last
   assert last['gate']['status']=='blocked' and last['gate']['blocking'] is False,last
   assert source['output_artifacts']['gate']['digest']==last['gate_digest']
   assert not any(e['step'] in ('repair','commit') for e in h.seen)
   source_version=h.call('run','status',rid)['run_version'];owner_hashes={p:digest(h.tree/p) for p in ('owner.txt','owner-scratch.txt')}
   dependency.write_text('fixture-control-v1\n');h.phase='resume'
   child=h.resume(repo,rid,'codex-cli');offset=len(h.seen);final=h.drive_live(child)
   assert final['outcome']=='succeeded' and [e['step'] for e in h.seen[offset:]]==['check-change','aif-security','review-task','commit']
   assert len(h.claims)==1 and sorted(set(h.generations))==[1,2]
   assert owner_hashes=={p:digest(h.tree/p) for p in owner_hashes}
   assert h.call('run','status',rid)['run_version']==source_version
   report={'outcome':'passed','target':target,'prifly':CORE_VERSION,'source_commit':COMMIT,'installed_origin':installed['origin'],'supporting_skills':'lee-to/ai-factory@2.19.0 e144f95c89de0d0cb6c9b38dbe8c2907b00dc5ce','skills_sha256':{name:digest(SKILLS/name/'SKILL.md') for name in ('aif-review','aif-security-checklist','aif-fix')},'source_run':rid,'source_version':source_version,'source_outcome':source['outcome'],'source_gate_digest':last['gate_digest'],'child_run':child,'final_outcome':final['outcome'],'claim_generations':sorted(set(h.generations)),'owner_hashes':owner_hashes,'base_commit':h.base,'head_commit':git_out(h.tree,'rev-parse','HEAD'),'reader_reports':h.live,'other_steps':h.setup,'boundary':'Real fresh Codex CLI readers with sealed released bridges and actual pinned upstream skills. Warmup/fix/commit use deterministic fixture setup; no manual verdict/gate edits or expected-result instructions to reader hosts. No different model claimed.'}
   # All experiment paths are under this fixture; redact them from public report.
   text=json.dumps(report,indent=2,ensure_ascii=False).replace(str(root.resolve()),'$FIXTURE').replace(str(root),'$FIXTURE')
   (ARTIFACTS/f'{target}-result.json').write_text(text+'\n')
   print(json.dumps({'target':target,'outcome':'passed','source':source['outcome'],'final':final['outcome']}),flush=True)
  finally:
   clean(BINARY,authority,h.runs)
   for r in h.runs:
    for aid,a in h.call('run','status',r)['run']['attempts'].items():
     if a['status']=='uncertain':h.call('run','resolve',r,'--attempt',aid,'--outcome','applied','--reason','Fixture host exited; previously synchronous local operations returned, no external effect.')
   clean(BINARY,authority,h.runs)
   assert not any(c['status']=='active' for c in h.call('claim','list')['claims'])
   assert verify.forget_authority(authority)==1

if __name__=='__main__':
 if not __debug__:raise RuntimeError('Verification requires Python assertions')
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--binary',required=True,type=Path)
 p.add_argument('--skills-root',required=True,type=Path,help='AI Factory 2.19.0 skills directory, with scripts and references')
 p.add_argument('--evidence-root',required=True,type=Path,help='Private destination for exact prompts, reports, receipts and CLI events')
 p.add_argument('--target',choices=GATES);args=p.parse_args()
 BINARY=args.binary.resolve(strict=True);SKILLS=args.skills_root.resolve(strict=True)
 ARTIFACTS=args.evidence_root.resolve();ARTIFACTS.mkdir(parents=True,exist_ok=True)
 CORE_VERSION=verify.run(BINARY,'version')['version']
 for target in ([args.target] if args.target else list(GATES)):run(target)
