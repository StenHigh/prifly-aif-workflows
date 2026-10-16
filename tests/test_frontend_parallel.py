"""Safety boundaries for typed browser grants, original reports and cleanup."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'aif-feature/files'))
import browser_contract as browser
import frontend_host
import frontend_quality as quality
import feature
import evidence as w1
from test_product_review import configuration, fixture
from test_feature import task_input


def inputs(optional_policy='ignore'):
    config=configuration(optional_policy=optional_policy)
    for lens in browser.READERS: config[lens]['require_separate_session']=True
    cfg,ui,ux,candidate,env,reports,current,cfg_digest,rq_digests=fixture(config)
    adapter={'protocol':browser.PROTOCOL,'root':'/reviewed/adapter','entrypoint':'adapter.py',
             'files':{'adapter.py':'sha256:'+'a'*64},'settings':{}}
    adapter_digest=w1.digest(w1.encoded(adapter)+b'\n')
    bindings={l:{'protocol':browser.PROTOCOL,'status':'ready','reason':'','lens':l,'run_id':'run:fixture',
        'round':cfg[l]['round'],'owner':env['owner'],'environment_session':env['session'],
        'candidate_digest':candidate['digest'],'configuration_digest':cfg_digest,'request_digest':rq_digests[l],
        'adapter_digest':adapter_digest,'context_id':l+'-context','identity_id':l+'-identity','allocation':{}} for l in browser.READERS}
    manifest={'schema_version':'1','join_result':'satisfied','selected_branch_ids':['ui','ux'],'branches':[]}
    bundle={'schema_version':'1','manifest_digest':'sha256:'+'b'*64,'status':'ready','reason':'','reports':[]}
    for lens in browser.READERS:
        reports[lens]['session']='separate'
        raw=json.dumps(reports[lens],indent=2).encode()+b' \n'
        ref={'artifact_id':'artifact:'+lens,'revision':1,'digest':w1.digest(raw)}
        manifest['branches'].append({'id':lens,'status':'completed','outcome':'succeeded','has_waivers':False,'output_refs':{'report':ref}})
        bundle['reports'].append({'branch':lens,'ref':ref,'raw_base64':base64.b64encode(raw).decode()})
    return [cfg,candidate,env,bindings,adapter,{'ui':ui,'ux':ux},rq_digests,cfg_digest,adapter_digest,'run:fixture',current,manifest,bundle,bundle['manifest_digest']]


class FrontendParallelTest(unittest.TestCase):
    def test_cli_error_keeps_actors_unknown_until_evidence_callback_completed(self):
        for callback_completed in (False,True):
            with self.subTest(callback_completed=callback_completed),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);journal_path=root/'journal.json';journal={'actor_phase':'not_started','run_id':'run:fixture'}
                tasks=[]
                for lens in browser.READERS:
                    workspace=root/lens;(workspace/'outputs').mkdir(parents=True)
                    (workspace/'outputs/report').write_text(json.dumps({'checks':[{'status':'unavailable'}]}))
                    tasks.append({'workspace':str(workspace),'attempt_id':'attempt:'+lens,
                        'skill_refs':[{'id':'aif-feature:context/feature-'+lens}],
                        'context':{'outputs':{'report':{'path':'outputs/report'}}}})
                bindings=[{'context_id':l,'identity_id':l} for l in browser.READERS]
                def dispatch(binary,authority,deliveries,**kwargs):
                    if callback_completed:kwargs['before_submit'](deliveries,[{},{}])
                    raise ValueError('Native submit refused' if callback_completed else 'CLI actor failed before usable evidence')
                with patch.object(frontend_host,'validate_reader',side_effect=bindings),patch.object(frontend_host,'journal_for',return_value=(journal_path,journal)),patch.object(frontend_host.controller,'dispatch',side_effect=dispatch):
                    with self.assertRaises(ValueError):frontend_host.dispatch(None,None,tasks,root/'artifacts','codex')
                saved=json.loads(journal_path.read_text())
                self.assertEqual(saved['actor_phase'],'settled' if callback_completed else 'unknown')
                if not callback_completed:
                    with patch.object(frontend_host.controller,'call',return_value={'run':{'status':'cancelled','attempts':{}}}),patch.object(frontend_host,'release_value') as release:
                        with self.assertRaises(w1.Invalid):frontend_host.cleanup(None,None,journal_path)
                        release.assert_not_called()

    def test_round_guard_rechecks_limit_without_trusting_cached_admission(self):
        data=inputs();task=task_input(True)
        with self.assertRaises(w1.Invalid):feature.begin(task,'0'*40,0,'parallel-ui-ux',data[4],limit=8)
        for mode in ('sequential','parallel-backend'):
            self.assertEqual(feature.begin(task_input(),'0'*40,0,mode,limit=8)[0],1)

    def test_sealed_quality_limit_admission_does_not_lower_an_owner_request(self):
        def state(value):
            return {'workflow_configurations':{'sealed-digest':{
                'workflow_ref':{'id':'aif-feature:workflow/quality'},
                'inputs':{'limit':{'source':'default','value':value}}}}}
        for value in (1,2,3):self.assertEqual(frontend_host.quality_limit(state(value)),value)
        for value in (None,0,4,8,True,'3'):
            data=state(value);before=copy.deepcopy(data)
            with self.assertRaises(w1.Invalid):frontend_host.quality_limit(data)
            self.assertEqual(data,before)
        with self.assertRaises(w1.Invalid):frontend_host.quality_limit({})
        data=state(3);data['workflow_configurations']['second']=copy.deepcopy(data['workflow_configurations']['sealed-digest'])
        with self.assertRaises(w1.Invalid):frontend_host.quality_limit(data)

    def test_fixture_cleanup_releases_current_round_after_historical_sessions(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent / 'probes'))
        from feature_uiux_check import UIUXHost
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);state_root=root/'environment-state';state_root.mkdir()
            owner='owned-fixture'
            lease=state_root/('owner-'+hashlib.sha256(owner.encode()).hexdigest()[:24]+'.lease')
            lease.write_text(json.dumps({'owner':owner,'session':'environment-current'}))
            for session in ('environment-old','environment-current'):
                (state_root/(session+'.json')).write_text(json.dumps({'owner':owner,'session':session,'url':'http://127.0.0.1:12345'}))
            host=UIUXHost.__new__(UIUXHost);host.root=root;host.teardown=[]
            host.adapter={'settings':{'state_root':str(state_root)}}
            def release(adapter,config,env):
                self.assertEqual(env['session'],'environment-current')
                lease.unlink()
                return {'status':'released','owner':owner,'session':env['session'],'reason':''}
            with patch.object(frontend_host,'release_value',side_effect=release) as invoked:
                host.cleanup_fixture()
                self.assertEqual(invoked.call_count,1)
            self.assertEqual([x['session'] for x in host.teardown],['environment-current'])

    def test_complete_original_reports_and_grants(self):
        value=quality.assess(*inputs())
        self.assertEqual(value['gate']['status'],'warnings')
        self.assertEqual(set(value['reports']),{'ui','ux'})
        for row in value['parallel']['bundle']['reports']:
            self.assertEqual(w1.digest(base64.b64decode(row['raw_base64'])),row['ref']['digest'])

    def test_cross_run_round_candidate_request_adapter_and_environment_grants_block(self):
        for field,value in [('run_id','run:old'),('round',2),('candidate_digest','sha256:'+'f'*64),
                            ('configuration_digest','sha256:'+'f'*64),('request_digest','sha256:'+'f'*64),
                            ('adapter_digest','sha256:'+'f'*64),('environment_session','foreign'),('owner','foreign')]:
            data=inputs();data[3]['ui'][field]=value
            self.assertEqual(quality.assess(*data)['gate']['status'],'blocked',field)

    def test_shared_context_or_identity_never_qualifies(self):
        for field in ('context_id','identity_id'):
            data=inputs();data[3]['ux'][field]=data[3]['ui'][field]
            self.assertEqual(quality.assess(*data)['gate']['status'],'blocked')

    def test_missing_and_changed_raw_reports_do_not_create_placeholder_passes(self):
        for fault in ('missing','bytes','request','session'):
            data=inputs();bundle=data[12]
            if fault=='missing':bundle['reports'].pop()
            elif fault=='bytes':bundle['reports'][0]['raw_base64']='e30='
            else:
                entry=bundle['reports'][0];report=json.loads(base64.b64decode(entry['raw_base64']))
                if fault=='request':report['request_digest']='sha256:'+'f'*64
                else:report['session']='shared'
                raw=json.dumps(report).encode();entry['ref']['digest']=w1.digest(raw);entry['raw_base64']=base64.b64encode(raw).decode()
            self.assertEqual(quality.assess(*data)['gate']['status'],'blocked',fault)

    def test_unknown_native_pair_yields_blocked_assessment_without_reports(self):
        data=inputs();data[11:]=[None,None,None]
        value=quality.assess(*data)
        self.assertEqual(value['gate']['status'],'blocked');self.assertEqual(value['reports'],{})

    def test_candidate_and_cleanup_freshness(self):
        data=inputs();value=quality.assess(*data)
        release={'status':'released','owner':data[2]['owner'],'session':data[2]['session'],'reason':''}
        self.assertEqual(quality.finalize(value,release,data[1])['gate']['status'],'warnings')
        for field,bad in [('owner','foreign'),('session','foreign'),('status','reconcile_required')]:
            failed={**release,field:bad,'reason':'Cleanup requires inspection'}
            self.assertEqual(quality.finalize(value,failed,data[1])['gate']['status'],'blocked')
        self.assertEqual(quality.finalize(value,release,None)['gate']['status'],'blocked')

    def test_owner_decision_outranks_a_repairable_other_lens_defect(self):
        data=inputs(optional_policy='stop');entry=data[12]['reports'][0]
        value=json.loads(base64.b64decode(entry['raw_base64']));value['checks'][0].update(result='failed',reason='Observed UI overflow')
        raw=json.dumps(value).encode();entry['ref']['digest']=w1.digest(raw);entry['raw_base64']=base64.b64encode(raw).decode()
        gate=quality.assess(*data)['gate']
        self.assertTrue(gate['blocking_owner_only']);self.assertEqual(gate['status'],'warnings')

    def test_operator_cleanup_uses_native_adapter_not_edited_journal(self):
        data=inputs();env,cfg,adapter=data[2],data[0],data[4]
        raw={k:w1.encoded(v)+b'\n' for k,v in [('environment',env),('configuration',cfg),('browser_adapter',adapter)]}
        refs={k:{'artifact_id':'artifact:'+k,'revision':1,'digest':w1.digest(v)} for k,v in raw.items()}
        attempt={'step_instance_id':'s','settled':True,'accepted':{'outputs':{'environment':refs['environment']}},
                 'context':{'inputs':{k:{'ref':refs[k]} for k in ('configuration','browser_adapter')}}}
        state={'run':{'status':'cancelled','attempts':{'a':attempt},'steps':{'s':{'definition_ref':{'id':'aif-feature:step/frontend-environment'}}}}}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'journal.json'
            path.write_text(json.dumps({'run_id':'run:fixture','environment_attempt':'a','actor_phase':'settled','environment_ref':refs['environment'],
                'values':{'environment':env},'configuration':cfg,'adapter':{**adapter,'root':'/unreviewed'}}))
            def call(binary,authority,*args):
                if args[:2]==('run','status'):return state
                ref=json.loads(Path(args[args.index('--ref')+1]).read_text());port=ref['artifact_id'].split(':')[1]
                Path(args[args.index('--output')+1]).write_bytes(raw[port]);return {}
            with patch.object(frontend_host.controller,'call',side_effect=call),patch.object(frontend_host,'release_value') as release:
                with self.assertRaises(w1.Invalid):frontend_host.cleanup(None,None,path)
                release.assert_not_called()

    def test_mode_requires_explicit_adapter_isolated_frontend_and_fresh_sessions(self):
        data=inputs();task=task_input(True)
        with self.assertRaises(w1.Invalid):feature.configuration(task,'frontend','parallel-ui-ux')
        with self.assertRaises(w1.Invalid):feature.configuration(task_input(),'backend','parallel-ui-ux',data[4])
        task['product']['environment']['shared_resource']='stand'
        with self.assertRaises(w1.Invalid):feature.configuration(task,'frontend','parallel-ui-ux',data[4])
        task['product']['environment']['shared_resource']=None
        _,_,cfg=feature.begin(task,'0'*40,0,'parallel-ui-ux',data[4])
        self.assertTrue(all(cfg[l]['require_separate_session'] for l in browser.READERS))

    def test_project_adapter_drift_and_symlinks_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);file=root/'adapter.py';file.write_text('pass\n')
            adapter={'protocol':browser.PROTOCOL,'root':str(root),'entrypoint':'adapter.py','files':{'adapter.py':w1.digest(file.read_bytes())},'settings':{}}
            frontend_host.verify_project(adapter)
            file.write_text('raise SystemExit(1)\n')
            with self.assertRaises(w1.Invalid):frontend_host.verify_project(adapter)
            file.unlink();file.symlink_to(root/'missing.py')
            with self.assertRaises(w1.Invalid):frontend_host.verify_project(adapter)
        for name in ('../outside.py','/outside.py'):
            adapter=inputs()[4];adapter['files'][name]='sha256:'+'a'*64
            with self.assertRaises(w1.Invalid):browser.descriptor(adapter)

    def test_cleanup_does_not_trust_native_settlement_for_live_actual_actors(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'journal.json';file.write_text(json.dumps({'run_id':'run:fixture','actor_phase':'active'}))
            with patch.object(frontend_host.controller,'call',return_value={'run':{'status':'cancelled','attempts':{}}}),patch.object(frontend_host,'release_value') as release:
                with self.assertRaises(w1.Invalid):frontend_host.cleanup(None,None,file)
                release.assert_not_called()

    def test_release_refuses_unsettled_native_reader(self):
        state={'run':{'steps':{'s':{'definition_ref':{'id':'aif-feature:step/parallel-ui'}}},'attempts':{'a':{'step_instance_id':'s','settled':None}}}}
        with patch.object(frontend_host.controller,'verify_adapter'),patch.object(frontend_host,'journal_for',return_value=(Path('/unused'),{'actor_phase':'settled'})),patch.object(frontend_host.controller,'call',return_value=state),patch.object(frontend_host,'release_value') as release:
            with self.assertRaises(w1.Invalid):frontend_host.release(None,None,{'run_id':'run:fixture'},None)
            release.assert_not_called()


if __name__=='__main__':unittest.main()
