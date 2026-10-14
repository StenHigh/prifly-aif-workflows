#!/usr/bin/env python3
"""W2 released runtime qualification; synthetic host or actual browser adapter.

The browser mode observes actual pages but has deterministic fixture assertions,
not an independent LLM verdict. Do not count it as an AI visual review.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verify
from test_product_review import configuration,p
from test_review_evidence import report
from evidence_check import read
from run_check import clean,git_out
from product_environment import OwnedEnvironment

CASES=('pass','backend','excluded','missing-browser','optional-ignore','optional-stop','missing-server','false-browser',
       'wrong-viewport','missing-scenario','stale-candidate','stale-environment','wrong-cleanup-owner','cleanup-interrupted',
       'defect-repair','cancel-resume','blocked-resume','shared-resource')
BROWSER_CASES=('pass','defect-repair','cancel-resume','missing-server')
LIVE_SKILLS=None
MANUAL_DIRECTORY=None
AUTO_REVIEW=False


def submit(binary,authority,rid,task,port,value,summary):
    template=verify.run(binary,'--project',authority,'session','submit','--template','--run',rid,'--attempt',task['attempt_id'])
    path=Path(task['workspace'])/task['context']['outputs'][port]['path'];data=json.dumps(value).encode();path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    template['result']['outputs'][port]['digest']=p.w1.digest(data);template['result']['verdict']='pass';template['result']['summary']=summary;template['answered_questions']=[]
    if task.get('model_profile'):template['model_profile']={'outcome':'unavailable','reason':'Deterministic fixture host; no independent model or session claimed.'}
    path=Path(task['workspace'])/'submission.json';path.write_text(json.dumps(template));verify.run(binary,'--project',authority,'session','submit','--file',path)


def live_reader(binary,authority,rid,task,library,artifacts,case,iteration):
    import shlex
    workspace=Path(task['workspace']);task_file=workspace/'task.json';task_file.write_text(json.dumps(task,indent=2))
    template=verify.run(binary,'--project',authority,'session','submit','--template','--run',rid,'--attempt',task['attempt_id'])
    (workspace/'submission-template.json').write_text(json.dumps(template,indent=2))
    browser_command=shlex.join(['node',str(Path(__file__).with_name('product_browser.cjs')),str(library),str(task_file),str(workspace/'browser')])
    prompt=f"""Execute exactly this delivered Pri-Fly assisted Attempt. Read {task_file}, every delivered skill/context reference and bound input artifact, and submission-template.json. Follow the sealed UI/UX bridge and pinned upstream review, using only the named read-only repository_workspace. No repair, policy changes, install, environment provision/release, next-stage execution or Pri-Fly control calls.
This is an isolated local notes fixture served by its declared owned loopback environment. The test-only browser adapter is available as this exact command: {browser_command}
Run it to inspect the actual declared scenarios. It launches fresh browser contexts at the sealed viewports, writes observations.json and screenshots into your task workspace. Read the observations and inspect screenshots visually with your available image tool. You may make additional read-only browser/code checks for the sealed criteria. The adapter's deterministic metrics are observations, not a reviewer decision. Derive your own assessment and don't claim independent model choice merely from a fresh session.
The report must follow the sealed W1 schema exactly. Each browser evidence observation is a JSON STRING with exactly scenario, viewport, url, observations; use the scenario ID, exact configured viewport and exact environment origin + scenario.path. Put human-readable observed facts (including actual failures if any) in observations. Cover exactly the scenarios assigned to this Attempt's lens and check_id in the delivered request. The shared configuration also contains the OTHER reader's scenarios; those must not appear in this report's evidence. Tool names the actual browser tool; locator equals the exact environment origin + scenario.path URL ONLY, without selectors or screenshot paths. Put those details in observations instead; exit_code null. Copy captured candidate unchanged and context.inputs.request.ref.digest. No fabricated checks or hidden skips.
Use submission-template.json authority/identity fields unchanged. Write the report to the allocated report output slot and compute its actual SHA-256 digest. Set a usable verdict based on your own assessment; diagnostic product failures belong in check results and are compatible with a usable report. Fill native submission model_profile according to actual capability: honoured uses outcome and nonempty named; unavailable/declined use outcome and nonempty reason (literal key reason, not unavailable_reason), with no named/model keys. This native object is distinct from the typed report model_profile string and model:null. No independent-review model translation is supplied; do not invent another model. answered_questions is [] if none were met. Write complete submission.json under this task workspace. Do not submit it yourself. The controller will submit the exact file unchanged, then test outcomes outside your context.
Shell commands remain sandboxed. If the host shell cannot start because bwrap or the environment refuses it, request automatic approval review for the exact same bounded read-only fixture command using require_escalated, with a concrete reason. Do not disable sandbox, access credentials/unrelated projects, or widen this task. A rejected command stays rejected; report unavailable honestly if this cannot be resolved.
No expected result is supplied. Finish with paths of files you wrote."""
    prefix=artifacts/(case+'-'+str(iteration)+'-'+task['skill_refs'][0]['id'].rsplit('/',1)[-1]);prefix.mkdir(parents=True,exist_ok=True)
    (prefix/'prompt.txt').write_text(prompt)
    shutil.copyfile(task_file,prefix/'task.json');shutil.copyfile(workspace/'submission-template.json',prefix/'submission-template.json')
    shutil.copytree(workspace/'inputs',prefix/'inputs',dirs_exist_ok=True)
    before_version=verify.run(binary,'--project',authority,'run','status',rid)['run_version']
    if MANUAL_DIRECTORY:
        import time
        delivery=MANUAL_DIRECTORY/(str(iteration)+'-'+task['skill_refs'][0]['id'].rsplit('/',1)[-1]);delivery.mkdir(parents=True,exist_ok=True)
        (delivery/'task.json').write_text(json.dumps(task,indent=2));(delivery/'prompt.txt').write_text(prompt)
        print(json.dumps({'manual_delivery':str(delivery),'workspace':str(workspace),'browser_command':browser_command}),flush=True)
        deadline=time.monotonic()+900
        while not (workspace/'submission.json').exists():
            if time.monotonic()>deadline:raise RuntimeError('Manual host did not submit within 15 minutes')
            time.sleep(0.2)
    else:
        with (prefix/'events.jsonl').open('w') as out,(prefix/'stderr.txt').open('w') as err:
            command=['codex','exec','--ephemeral','--json']
            if AUTO_REVIEW:command.append('--approve-for-me')
            else:command+=['--sandbox','workspace-write']
            command+=['-C',str(workspace),'--skip-git-repo-check','-o',str(workspace/'host-final.txt'),'-']
            proc=subprocess.run(command,input=prompt,text=True,stdout=out,stderr=err,timeout=480)
        assert proc.returncode==0,(proc.returncode,(prefix/'stderr.txt').read_text()[-2000:])
    assert verify.run(binary,'--project',authority,'run','status',rid)['run_version']==before_version,'Reader mutated authority'
    file=workspace/'submission.json';data=json.loads(file.read_text());report_path=workspace/task['context']['outputs']['report']['path'];value=json.loads(report_path.read_text())
    session_id=None
    if not MANUAL_DIRECTORY:
        assert value['session']=='separate','Fresh reader did not establish its separate session'
        for line in (prefix/'events.jsonl').read_text().splitlines():
            event=json.loads(line)
            if event.get('type')=='thread.started':session_id=event['thread_id']
        assert session_id,'Fresh host session identity missing'
    assert data['result']['outputs']['report']['digest']==p.w1.digest(report_path.read_bytes())
    shutil.copyfile(file,prefix/'submission.json');shutil.copyfile(report_path,prefix/'report.json')
    if (workspace/'browser').exists():shutil.copytree(workspace/'browser',prefix/'browser',dirs_exist_ok=True)
    receipt=verify.run(binary,'--project',authority,'session','submit','--file',file)
    (prefix/'receipt.json').write_text(json.dumps(receipt,indent=2))
    return {'lens':task['skill_refs'][0]['id'].rsplit('/',1)[-1].removesuffix('-bridge'),'iteration':iteration,'verdict':data['result']['verdict'],'report':value,'submission_digest':p.w1.digest(file.read_bytes()),'session_id':session_id,'approval_mode':'automatic review with workspace-write sandbox' if AUTO_REVIEW else 'default','session_mode':'current Codex app / shared session; no independent session/model' if MANUAL_DIRECTORY else 'fresh real Codex CLI, no other model attested'}


def run_case(binary,case,host='codex-cli',library=None,artifacts=None):
    with tempfile.TemporaryDirectory(prefix='w2-run-') as directory:
        root=Path(directory);repository,authority=verify.prepare_repository(binary,root);runs=[];envs=[];observed=[];snapshots=[];claims=set();trees=[];other=None
        browser=library is not None
        try:
            if LIVE_SKILLS:
                for host_root in verify.HOSTS.values():
                    shutil.copyfile(LIVE_SKILLS/'aif-review.md',repository/host_root/'aif-review/SKILL.md')
                    shutil.copyfile(LIVE_SKILLS/'severity.md',repository/host_root/'aif-review/references/SEVERITY.md')
            html=(verify.ROOT/'tests/fixtures/product/index.html').read_text()
            if case=='defect-repair':html=html.replace('/* DEFECT_OVERFLOW */','section { min-width: 800px; }').replace('/* DEFECT_FLOW */','return;')
            (repository/'index.html').write_text(html);(repository/'owner.txt').write_text('Preserve owner work\n')
            verify.git('-C',repository,'add','.');verify.git('-C',repository,'commit','-qm','Product fixture');base=git_out(repository,'rev-parse','HEAD')
            cfg=configuration(base,surface='backend' if case=='backend' else 'frontend',required=not case.startswith('optional'),optional_policy='stop' if case=='optional-stop' else 'ignore')
            if LIVE_SKILLS and not MANUAL_DIRECTORY:
                for lens in p.LENSES:cfg[lens]['require_separate_session']=True
            if case=='excluded':
                for lens in p.LENSES:cfg[lens]['checks'][0]['enabled']=False
            if case=='shared-resource':
                cfg['environment']['shared_resource']='fixture-stand'
                (repository/'.prifly/workflows/aif-ui-ux/extend.yaml').write_text('resources:\n  fixture-stand:\n    limit: 1\n    stages: [quality]\nextensions: []\n')
                verify.git('-C',repository,'add','.');verify.git('-C',repository,'commit','-qm','Shared resource fixture');base=git_out(repository,'rev-parse','HEAD')
                for lens in p.LENSES:cfg[lens]['base_commit']=base
            config_path=root/'configuration.json';config_path.write_text(json.dumps(cfg))
            verify.run(binary,'--project',authority,'project','local','set','--repository',repository,'--allow-executable','python='+str(Path(sys.executable).resolve()))
            args=('--project',authority,'project','start','--repository',repository,'--launch','aif-ui-ux','--host',host,'--workspace','worktree','--input','configuration='+str(config_path),'--allow-execution')
            prepared=verify.run(binary,*args[:3],'questionnaire',*args[4:],'--prepare')
            # User-reviewed input remains exact; prepare exposes its identity,
            # not a speculative per-field questionnaire renderer.
            rid=verify.run(binary,*args,'--expected-launch-digest',prepared['review_digest'])['run']['run']['id'];runs.append(rid)
            current_env=None

            def drive(rid,iteration):
                nonlocal current_env,other
                for _ in range(25):
                    verify.run(binary,'--project',authority,'run','drive',rid)
                    tasks=verify.run(binary,'--project',authority,'session','task','--run',rid,'--all')['tasks']
                    if not tasks:return verify.run(binary,'--project',authority,'run','status',rid)['run']
                    for task in tasks:
                        name=task['skill_refs'][0]['id'].rsplit('/',1)[-1].removesuffix('-bridge');tree=Path(task['repository_workspace']);trees.append(tree);claims.add(task['claim_id'])
                        config=read(task,'configuration');before=p.w1.snapshot(tree,base)
                        if name=='environment':
                            basis=read(task,'candidate');snapshots.append(basis['digest']);need=p.needed(config)
                            missing=case in ('missing-browser','missing-server','optional-ignore','optional-stop') or case=='blocked-resume' and iteration==0
                            status='not_needed' if not need else 'unavailable' if missing else 'ready'
                            current_env=None
                            if status=='ready':
                                if case=='shared-resource' and iteration==0:
                                    # A second Run cannot receive the same resource while
                                    # the first setup Attempt is active.
                                    refused=verify.run(binary,*args,'--expected-launch-digest',prepared['review_digest'],expect_ok=False)
                                    assert 'resource_busy' in refused,refused
                                    created=[r['run_id'] for r in verify.run(binary,'--project',authority,'run','list')['runs'] if r['run_id'] not in runs]
                                    assert len(created)==1,created
                                    other=created[0];runs.append(other)
                                    refused=verify.run(binary,'--project',authority,'run','drive',other,expect_ok=False)
                                    assert 'resource_busy' in refused,refused
                                    pending=verify.run(binary,'--project',authority,'session','task','--run',other,'--all')['tasks'];assert not pending,pending
                                current_env=OwnedEnvironment(root/'environment-state',tree,config['environment']['owner'],profile=config['environment']['profile'],shared=config['environment']['shared_resource']);envs.append(current_env);url=current_env.ensure()
                            receipt={'status':status,'owner':config['environment']['owner'],'profile':config['environment']['profile'],
                                     'configuration_digest':task['context']['inputs']['configuration']['ref']['digest'],'candidate_digest':basis['digest'],
                                     'session':current_env.session if current_env else None,'url':current_env.url if current_env else None,'reason':'' if current_env else 'Sealed scope has no browser checks' if not need else 'Missing declared browser/server'}
                            if case=='stale-environment':receipt['candidate_digest']='sha256:'+'a'*64
                            submit(binary,authority,rid,task,'environment',receipt,'Real owned loopback fixture, or declared unavailable')
                        elif name in p.LENSES:
                            rq=read(task,'request');basis=read(task,'candidate');environment=read(task,'environment');entry=report(rq,basis);entry['request_digest']=task['context']['inputs']['request']['ref']['digest'];check=entry['checks'][0];check['id']=name+'_acceptance'
                            if case=='cancel-resume' and iteration==0 and name=='ui':
                                verify.run(binary,'--project',authority,'run','cancel',rid,'--reason','Cancel fixture reader after owned setup');verify.run(binary,'--project',authority,'run','drive',rid)
                                # No cleanup tail ran. The operator uses exact ownership.
                                assert current_env.server is not None
                                with_preserved=p.w1.snapshot(tree,base);current_env.close();assert p.w1.snapshot(tree,base)==with_preserved
                                return verify.run(binary,'--project',authority,'run','status',rid)['run']
                            if LIVE_SKILLS:
                                accepted=live_reader(binary,authority,rid,task,library,artifacts,case,iteration)
                                observed.append(accepted)
                                assert p.w1.snapshot(tree,base)==before,'Live reader changed candidate'
                                continue
                            skip='excluded' if not rq['checks'][0]['enabled'] else 'not_applicable' if not rq['checks'][0]['applicable'] else 'unavailable' if environment['status']!='ready' else None
                            if skip:check.update(status=skip,result='not_run',reason=config['scope_reason'] if skip=='not_applicable' else environment['reason'] or 'Explicitly excluded reviewer',evidence=[])
                            else:
                                if browser:
                                    task_file=Path(task['workspace'])/'browser-task.json';task_file.write_text(json.dumps(task));out=root/(name+'-'+str(iteration));out.mkdir()
                                    proc=subprocess.run(['node',str(Path(__file__).with_name('product_browser.cjs')),str(library),str(task_file),str(out)],text=True,capture_output=True,timeout=90,env=os.environ.copy());assert proc.returncode==0,proc.stderr
                                    result=json.loads(proc.stdout);items=result['observations'];tool=result['tool'];observed.append({'lens':name,'iteration':iteration,'tool':tool,'observations':items})
                                    if artifacts:
                                        dst=artifacts/(case+'-'+host+'-'+str(iteration)+'-'+name);shutil.copytree(out,dst,dirs_exist_ok=True)
                                else:
                                    items=[{'scenario':s['id'],'viewport':s['viewport'],'url':environment['url']+s['path'],'observations':'Synthetic scenario report; no browser execution claimed','failures':['Injected product defect'] if case=='defect-repair' and iteration==0 else []} for s in config['scenarios'] if s['lens']==name];tool='synthetic-browser-report (no actual execution)'
                                failures=[f for item in items for f in item['failures']]
                                check.update(result='failed' if failures else 'passed',reason='; '.join(failures),evidence=[{'method':'browser','tool':tool,'locator':item['url'],'observation':json.dumps({k:item[k] for k in ('scenario','viewport','url','observations')}),'exit_code':None} for item in items])
                            if case=='false-browser':check.update(status='executed',result='passed',reason='',evidence=[{'method':'code','tool':'diff','locator':'index.html','observation':'Only code inspected','exit_code':None}])
                            if case in ('wrong-viewport','missing-scenario') and name=='ui':
                                if case=='missing-scenario':check['evidence'].pop()
                                else:
                                    item=check['evidence'][0];val=json.loads(item['observation']);val['viewport']['width']=640;item['observation']=json.dumps(val)
                            submit(binary,authority,rid,task,'report',entry,'Actual browser fixture observations; no LLM verdict' if browser else 'Synthetic report; no browser/model/session independence')
                            if case=='stale-candidate' and name=='ux':(tree/'owner.txt').write_text('Owner changed after readers\n')
                        elif name=='release':
                            receipt=read(task,'environment');status='not_needed';reason=''
                            if current_env:
                                if case=='cleanup-interrupted':
                                    try:current_env.release(current_env.owner,current_env.session,interrupt=True)
                                    except RuntimeError:status='reconcile_required';reason='Fixture interrupted after server stop, lease retained'
                                else:current_env.close();status='released'
                            release={'status':status,'owner':receipt['owner'],'session':receipt['session'],'reason':reason}
                            if case=='wrong-cleanup-owner':release['owner']='another-job'
                            submit(binary,authority,rid,task,'release',release,'Owned cleanup with honest interruption receipt')
                        else:raise AssertionError(name)
                        after=p.w1.snapshot(tree,base)
                        if not(case=='stale-candidate' and name=='ux'):assert after==before,(name,'changed claimed code')
                raise AssertionError('Product Run did not finish')
            state=drive(rid,0)
            if other:
                verify.run(binary,'--project',authority,'run','cancel',other,'--reason','Resource contention probe complete');verify.run(binary,'--project',authority,'run','drive',other)
            source_outcome=state.get('outcome') or state['status']
            if case in ('defect-repair','cancel-resume','blocked-resume'):
                assert source_outcome in ('partial','cancelled'),state
                tree=trees[-1]
                if case=='defect-repair':(tree/'index.html').write_text((verify.ROOT/'tests/fixtures/product/index.html').read_text())
                (tree/'owner.txt').write_text('Preserved owner edit across review continuation\n')
                args_continue=('--project',authority,'project','continue','--repository',repository,'--launch','aif-ui-ux','--source-run',rid,'--host',host,'--allow-execution')
                prep=verify.run(binary,*args_continue,'--prepare');rid=verify.run(binary,*args_continue,'--expected-launch-digest',prep['review_digest'])['run']['run']['id'];runs.append(rid);state=drive(rid,1)
                assert (tree/'owner.txt').read_text()=='Preserved owner edit across review continuation\n';assert snapshots[0]!=snapshots[-1]
            expected='succeeded' if case in ('pass','backend','excluded','optional-ignore','defect-repair','cancel-resume','blocked-resume','shared-resource') else 'partial'
            assert state.get('outcome')==expected,{k:state.get(k) for k in ('outcome','status','diagnostics')}
            assert {'gate','ui_report','ux_report','environment','release'}<=state['output_artifacts'].keys()
            assert len(claims)==1
            if LIVE_SKILLS and not MANUAL_DIRECTORY:
                assert len({item['session_id'] for item in observed})==len(observed),'Host reused reader session'
            return {'case':case,'host':host,'mode':'current Codex app / actual browser / shared session' if MANUAL_DIRECTORY else 'fresh real Codex CLI readers / actual browser' if LIVE_SKILLS else 'actual browser / deterministic test adapter' if browser else 'synthetic reports / real Git, lifecycle and evaluator',
                    'source_outcome':source_outcome,'outcome':state['outcome'],'runs':len(runs),'candidate_changed':len(set(snapshots))>1,
                    'browser_readers':len(observed),'browser_observations':observed,'cleaned':True}
        finally:
            for env in envs:env.close()
            # start may create a Run before resource_busy interrupts dispatch.
            runs=list(dict.fromkeys(runs+[r['run_id'] for r in verify.run(binary,'--project',authority,'run','list')['runs']]))
            clean(binary,authority,runs)
            assert not any(c['status']=='active' for c in verify.run(binary,'--project',authority,'claim','list')['claims']);verify.forget_authority(authority)


def main():
    if not __debug__:raise RuntimeError('Verification requires assertions')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--binary',type=Path,required=True);parser.add_argument('--case',choices=CASES);parser.add_argument('--browser-library',type=Path);parser.add_argument('--artifacts',type=Path);parser.add_argument('--report',type=Path);parser.add_argument('--live-skills',type=Path);parser.add_argument('--manual-directory',type=Path);parser.add_argument('--auto-review',action='store_true');args=parser.parse_args()
    global LIVE_SKILLS,MANUAL_DIRECTORY,AUTO_REVIEW
    LIVE_SKILLS=args.live_skills;MANUAL_DIRECTORY=args.manual_directory;AUTO_REVIEW=args.auto_review
    if AUTO_REVIEW and (not LIVE_SKILLS or MANUAL_DIRECTORY):parser.error('Automatic approval review is only for explicitly selected live CLI fixture sessions')
    if MANUAL_DIRECTORY and not LIVE_SKILLS:parser.error("Manual host requires exact live skills")
    if LIVE_SKILLS and (not args.browser_library or not args.artifacts or not args.case):parser.error('Live readers require --browser-library, --artifacts and one --case')
    if args.artifacts:args.artifacts.mkdir(parents=True,exist_ok=True)
    cases=(args.case,) if args.case else BROWSER_CASES if args.browser_library else CASES;results=[]
    for case in cases:
        result=run_case(args.binary,case,host='codex-app' if MANUAL_DIRECTORY else 'codex-cli' if LIVE_SKILLS else 'codex-app' if args.browser_library else 'codex-cli',library=args.browser_library,artifacts=args.artifacts);results.append(result);print(json.dumps({k:v for k,v in result.items() if k!='browser_observations'}),flush=True)
    if not args.case and not args.browser_library:
        for host in ('codex-app','claude-code'):
            result=run_case(args.binary,'pass',host);results.append(result);print(json.dumps({k:v for k,v in result.items() if k!='browser_observations'}),flush=True)
    if args.report:
        args.report.write_text(json.dumps({'prifly':verify.run(args.binary,'version')['version'],'binary_sha256':p.w1.digest(args.binary.read_bytes()),'cases':results},indent=2)+'\n')

if __name__=='__main__':main()
