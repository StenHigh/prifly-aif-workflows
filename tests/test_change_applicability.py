"""Correlation, immutability and mandatory browser configuration boundaries."""
import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'aif-ui-ux/files'))
import review_change as change
from test_product_review import captured,configuration

class ApplicabilityTest(unittest.TestCase):
    def source(self,status='required'):
        return dict(status=status,reason='Actual task/candidate inspection',task_digest='sha256:'+'a'*64,candidate=captured())
    def test_source_report_is_immutable(self):
        for status in ('required','not-required','unknown'):
            source=self.source(status);before=copy.deepcopy(source)
            value,gate=change.assess(source,source['task_digest'],captured(),captured())
            self.assertEqual(source,before)
            self.assertEqual(value['status'],status)
            self.assertEqual(gate['status'],'blocked' if status=='unknown' else 'passed')
    def test_mismatch_blocks_without_relabeling_source(self):
        for mismatch in ('task','capture','current','derivation'):
            source=self.source('not-required');before=copy.deepcopy(source)
            task=source['task_digest'];basis=captured();current=captured()
            if mismatch=='task':task='sha256:'+'b'*64
            elif mismatch=='capture':basis['head_commit']='f'*40
            elif mismatch=='current':current['head_commit']='f'*40
            else:source['source_report']={'artifact_id':'forged','revision':1,'digest':'sha256:'+'f'*64};before=copy.deepcopy(source)
            value,gate=change.assess(source,task,basis,current)
            self.assertEqual(source,before);self.assertEqual(value['status'],'unknown');self.assertTrue(gate['blocking'])
    def test_required_configuration_cannot_hide_browser_work(self):
        for case in ('missing','backend','disabled','base'):
            value=configuration()
            if case=='missing':value=None
            elif case=='backend':value=configuration(surface='backend')
            elif case=='disabled':value['ui']['checks'][0]['enabled']=False
            else:value['ui']['base_commit']='f'*40
            with self.assertRaises(change.w1.Invalid):change.configuration(value,captured())
        self.assertEqual(change.configuration(configuration(),captured()),configuration())
if __name__=='__main__':unittest.main()
