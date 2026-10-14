"""W2 negative acceptance and real owned environment transition/cleanup."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'aif-ui-ux/files'))
import product as p
from test_review_evidence import config,report
sys.path.insert(0,str(ROOT/'tests/probes'))
from product_environment import OwnedEnvironment,LifecycleError


def configuration(base='0'*40,surface='frontend',required=True,optional_policy='ignore'):
    v={'surface':surface,'scope_reason':'Declared interface change' if surface=='frontend' else 'Pure arithmetic backend, no UI surface',
       'environment':{'owner':'fixture-owned','profile':'all-checks','setup':'fixture ensure owned claimed tree',
       'cleanup':'fixture release exact owned session','browser_adapter':'project Playwright adapter',
       'test_identity':'isolated anonymous test only','allowed_operations':['navigate','input','submit_test'],'shared_resource':None},'scenarios':[]}
    for lens in p.LENSES:
        v[lens]=config(base,method='browser',required=required,optional_policy=optional_policy)
        v[lens]['checks'][0].update(id=lens+'_acceptance',description=lens+' acceptance',applicable=surface=='frontend')
        if surface=='frontend':
            for sid,width in ([('desktop',1280),('mobile',375)] if lens=='ui' else [('flow',375)]):
                v['scenarios'].append({'id':sid,'lens':lens,'check_id':lens+'_acceptance','path':'/index.html',
                'viewport':{'width':width,'height':800},'actions':[] if lens=='ui' else ['Use keyboard and submit isolated test form'],
                'expectations':['No overflow; readable consistent design'] if lens=='ui' else ['Observe empty/loading/error/success states and labelled keyboard flow']})
    return v


def captured():
    b={'base_commit':'0'*40,'head_commit':'1'*40,'index_digest':'sha256:'+'2'*64,'files_digest':'sha256:'+'3'*64}
    return {'algorithm':'git-candidate/1',**b,'digest':p.w1.digest(p.w1.encoded(b))}


def fixture(v=None,status='ready'):
    v=v or configuration();b=captured();ui,ux=(p.project(v,l) for l in p.LENSES)
    env={'status':status,'owner':v['environment']['owner'],'profile':v['environment']['profile'],
         'configuration_digest':p.w1.digest(p.w1.encoded(v)+b'\n'),'candidate_digest':b['digest'],
         'session':'owned-session' if status=='ready' else None,'url':'http://127.0.0.1:12345' if status=='ready' else None,'reason':'' if status=='ready' else 'No browser installed'}
    reports={}
    for lens,rq in zip(p.LENSES,(ui,ux)):
        r=report(rq,b);entry=r['checks'][0];entry['id']=lens+'_acceptance'
        if v['surface']=='backend' or status!='ready':
            entry.update(status='not_applicable' if v['surface']=='backend' else 'unavailable',result='not_run',reason=v['scope_reason'] if v['surface']=='backend' else env['reason'],evidence=[])
        else:
            entry['evidence']=[{'method':'browser','tool':'fixture declared browser observation','locator':env['url']+s['path'],
              'observation':json.dumps({'scenario':s['id'],'viewport':s['viewport'],'url':env['url']+s['path'],'observations':'Synthetic observation; no actual browser claimed'}),'exit_code':None} for s in v['scenarios'] if s['lens']==lens]
        reports[lens]=r
    args=[v,ui,ux,b,env,reports,copy.deepcopy(b),env['configuration_digest'],{l:p.w1.digest(p.w1.encoded(rq)+b'\n') for l,rq in zip(p.LENSES,(ui,ux))}]
    return args

class ProductReviewTest(unittest.TestCase):
    def test_complete_scenario_projection(self):
        a=fixture();self.assertEqual(p.evaluate(*a)['status'],'warnings')
        a[5]['ui']['model_profile']='honoured';a[5]['ui']['model']='fixture-declaration'
        a[5]['ux']['model_profile']='honoured';a[5]['ux']['model']='fixture-declaration'
        self.assertEqual(p.evaluate(*a)['status'],'passed')
    def test_missing_browser_required_and_optional(self):
        self.assertEqual(p.evaluate(*fixture(status='unavailable'))['status'],'blocked')
        for policy,blocking in [('ignore',False),('stop',True)]:
            gate=p.evaluate(*fixture(configuration(required=False,optional_policy=policy),status='unavailable'))
            self.assertEqual(gate['status'],'warnings');self.assertEqual(gate['blocking'],blocking)
    def test_backend_only_explicit_scope(self):
        a=fixture(configuration(surface='backend'),status='not_needed');self.assertEqual(p.evaluate(*a)['status'],'warnings')
        a[0]['ui']['checks'][0]['applicable']=True
        with self.assertRaises(p.w1.Invalid):p.configuration(a[0])
    def test_missing_wrong_viewport_and_wrong_origin(self):
        for change in ('missing','viewport','url','scenario'):
            a=fixture();items=a[5]['ui']['checks'][0]['evidence']
            if change=='missing':items.pop()
            else:
                val=json.loads(items[0]['observation']);val[change]={'width':800,'height':800} if change=='viewport' else 'wrong'
                items[0]['observation']=json.dumps(val)
            self.assertEqual(p.evaluate(*a)['status'],'blocked',change)
    def test_no_browser_substitution(self):
        a=fixture();a[5]['ui']['checks'][0]['evidence'][0]['method']='code';self.assertEqual(p.evaluate(*a)['status'],'blocked')
    def test_sealed_scenario_and_environment_changes(self):
        for where,key in [('env','candidate_digest'),('env','configuration_digest'),('env','owner'),('config','expectations')]:
            a=fixture()
            if where=='env':a[4][key]='wrong'
            else:a[0]['scenarios'][0][key]=['Different requirement']
            self.assertEqual(p.evaluate(*a)['status'],'blocked')
    def test_no_false_execution_on_unavailable_env(self):
        a=fixture();a[4].update(status='unavailable',url=None,session=None,reason='Missing server');self.assertEqual(p.evaluate(*a)['status'],'blocked')
    def test_product_defect_is_failed(self):
        a=fixture();a[5]['ux']['checks'][0].update(result='failed',reason='Required flow dead end')
        g=p.evaluate(*a);self.assertEqual(g['status'],'failed');self.assertTrue(g['blocking'])
    def test_candidate_changed_after_readers_or_cleanup(self):
        a=fixture();a[6]['head_commit']='f'*40;self.assertEqual(p.evaluate(*a)['status'],'blocked')
        r={'status':'released','owner':a[4]['owner'],'session':a[4]['session'],'reason':''}
        self.assertEqual(p.finalize(a[0],a[3],a[4],r,p.w1.gate('passed',[]),a[6])['status'],'blocked')
    def test_scoped_cleanup_and_uncertain_outcome(self):
        a=fixture();r={'status':'released','owner':a[4]['owner'],'session':a[4]['session'],'reason':''}
        good=p.finalize(a[0],a[3],a[4],r,p.w1.gate('passed',[]),a[3]);self.assertEqual(good['status'],'passed')
        for key,val in [('owner','another-job'),('session','another-session'),('status','not_needed'),('status','reconcile_required')]:
            bad={**r,key:val,'reason':'Interrupted cleanup'}
            self.assertEqual(p.finalize(a[0],a[3],a[4],bad,good,a[3])['status'],'blocked')
    def test_invalid_catalog(self):
        for mutation in ('duplicate','unknown','no-scenario','cross-surface','base'):
            v=configuration()
            if mutation=='duplicate':v['scenarios'].append(copy.deepcopy(v['scenarios'][0]))
            elif mutation=='unknown':v['scenarios'][0]['check_id']='unknown'
            elif mutation=='no-scenario':v['scenarios']=[]
            elif mutation=='cross-surface':v['surface']='backend'
            else:v['ux']['base_commit']='f'*40
            with self.assertRaises(p.w1.Invalid):p.configuration(v)

class EnvironmentTest(unittest.TestCase):
    def test_common_profile_and_authorized_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);tree=root/'tree';tree.mkdir();(tree/'owner.txt').write_text('keep')
            env=OwnedEnvironment(root/'state',tree,'job')
            try:
                first=env.ensure();self.assertEqual(env.ensure(),first)
                with self.assertRaisesRegex(LifecycleError,'release_required'):env.ensure('php')
                self.assertEqual(env.url,first)
                env.ensure('php',transition=True,owner='job');self.assertEqual(env.profile,'php')
                env.ensure('tests',transition=True,owner='job');self.assertEqual((tree/'owner.txt').read_text(),'keep')
            finally:env.close()
            self.assertFalse(env.lease.exists())
    def test_unique_jobs_and_shared_lease(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a=OwnedEnvironment(root,root,'a');b=OwnedEnvironment(root,root,'b')
            try:self.assertNotEqual(a.ensure(),b.ensure());self.assertNotEqual(a.session,b.session)
            finally:a.close();b.close()
            a=OwnedEnvironment(root,root,'a',shared='stand');b=OwnedEnvironment(root,root,'b',shared='stand')
            try:
                a.ensure()
                with self.assertRaisesRegex(LifecycleError,'owner_required'):b.ensure()
                with self.assertRaisesRegex(LifecycleError,'ownership_mismatch'):a.release('b',a.session)
                a.release('a',a.session);b.ensure()
            finally:a.close();b.close()
    def test_interrupted_release_reconciles_exact_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a=OwnedEnvironment(root,root,'a');a.ensure()
            with self.assertRaisesRegex(LifecycleError,'reconcile_required'):a.release('a',a.session,interrupt=True)
            with self.assertRaisesRegex(LifecycleError,'reconcile_required'):a.ensure()
            with self.assertRaisesRegex(LifecycleError,'ownership_mismatch'):a.reconcile('b',a.session)
            self.assertTrue(a.lease.exists());a.reconcile('a',a.session);self.assertFalse(a.lease.exists())

if __name__=='__main__':unittest.main()
