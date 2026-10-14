"""W3 admission, complete-round binding and owner-first repair diagnostics."""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'aif-feature/files'))
import feature as f
sys.path.insert(0, str(ROOT/'tests/probes'))
from feature_check import task_input
from test_review_evidence import report
from test_product_review import captured


class FeatureTest(unittest.TestCase):
    def test_profile_has_required_acceptance(self):
        for frontend in (False, True):
            task=task_input(frontend)
            f.configuration(task, 'frontend' if frontend else 'backend')
            with self.assertRaises(f.w1.Invalid):f.configuration(task, 'backend' if frontend else 'frontend')
        for lens in ('checks','review'):
            for field in ('required','enabled','applicable'):
                task=task_input();task[lens][0][field]=False
                with self.assertRaises(f.w1.Invalid):f.configuration(task)
        for lens in ('ui','ux'):
            task=task_input(True);task['product'][lens]['checks'][0]['required']=False
            with self.assertRaises(f.w1.Invalid):f.configuration(task)

    def test_round_reprojects_every_lens_from_original_base(self):
        for frontend in (False,True):
            task=task_input(frontend);before=copy.deepcopy(task)
            for previous in (0,7):
                count,requests,product=f.begin(task,'a'*40,previous)
                self.assertEqual(count,previous+1)
                for request in list(requests.values())+[product['ui'],product['ux']]:
                    self.assertEqual((request['base_commit'],request['round']),('a'*40,count))
                self.assertEqual(task,before)
        for previous in (-1,8,True):
            with self.assertRaises(f.w1.Invalid):f.begin(task_input(),'a'*40,previous)

    def assessment(self, mutate=None, product=None):
        task=task_input();_,requests,_=f.begin(task,'0'*40,0);candidate=captured()
        reports={lens:report(request,candidate) for lens,request in requests.items()}
        for lens in f.LENSES:reports[lens]['checks'][0]['id']=requests[lens]['checks'][0]['id']
        if mutate:mutate(task,requests,reports,candidate)
        digests={lens:f.w1.digest(f.w1.encoded(request)+b'\n') for lens,request in requests.items()}
        return f.aggregate(task,candidate,copy.deepcopy(candidate),requests,reports,digests,product)

    def test_unavailable_never_becomes_repair_even_with_another_defect(self):
        def change(task,requests,reports,candidate):
            reports['checks']['checks'][0].update(status='unavailable',result='not_run',reason='Missing required tool',evidence=[])
            reports['review']['checks'][0].update(result='failed',reason='Confirmed defect')
        gate=self.assessment(change);self.assertEqual(gate['status'],'blocked');self.assertFalse(gate['blocking'])

    def test_owner_stop_outranks_other_lens_failure(self):
        product={'gate':f.w1.gate('warnings',['Owner resolution'],blocking=True,owner=True)}
        def defect(task,requests,reports,candidate):reports['checks']['checks'][0].update(result='failed',reason='Confirmed defect')
        gate=self.assessment(defect,product);self.assertTrue(gate['blocking_owner_only']);self.assertEqual(gate['suggested_next'],'owner')

    def test_request_candidate_and_round_staleness_block(self):
        for field,val in [('request_digest','sha256:'+'f'*64),('round',2),('candidate',{'wrong':'candidate'})]:
            def change(task,requests,reports,candidate):reports['review'][field]=val
            self.assertEqual(self.assessment(change)['status'],'blocked',field)

    def test_guard_prevents_commit_of_intervening_edit(self):
        basis=captured();gate=f.feature_gate('passed',[])
        self.assertEqual(f.guard(basis,copy.deepcopy(basis),gate),gate)
        current=copy.deepcopy(basis);current['files_digest']='sha256:'+'f'*64
        self.assertEqual(f.guard(basis,current,gate)['status'],'blocked')

    def test_no_hidden_browser_substitution(self):
        task=task_input();task['checks'][0]['method']='browser'
        with self.assertRaises(f.w1.Invalid):f.configuration(task)
        task=task_input(True);task['product']['scenarios']=[]
        with self.assertRaises(f.w1.Invalid):f.configuration(task)

    def test_product_cannot_override_sealed_global_policy(self):
        for lens in ('ui','ux'):
            for field,value in [('optional_policy','stop'),('require_separate_session',True)]:
                task=task_input(True)
                # Both product lenses agree with each other, but contradict the outer owner choice.
                for key in ('ui','ux'):task['product'][key][field]=value
                with self.assertRaises(f.w1.Invalid):f.configuration(task)


if __name__=='__main__':unittest.main()
