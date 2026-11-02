#!/usr/bin/env python3
"""Add explicit /5 UI/UX imports to an initialized project; no import/start side effects.

The repository must already contain aif-ui-ux from this candidate/release.
Install the pinned contracts through tools/install_composition_contracts.py first.
Only this new package and project profile entries are written.
"""
import argparse,json,re
from pathlib import Path

def setup(repository, applicability=False):
 repository=Path(repository).resolve(strict=True);folder=repository/'.prifly/workflows/ui-ux-composed'
 if folder.exists():raise ValueError('Refuse to overwrite existing ui-ux-composed package')
 refs={'policy':'core:policy/local@4.0.0','configuration':'aif-product:schema/configuration@1.0.0','gate':'aif-evidence:schema/gate@1.0.0','report':'aif-evidence:schema/report@1.0.0','environment':'aif-product:schema/environment@1.0.0','release':'aif-product:schema/release@1.0.0'}
 outputs={name:{'schema_ref':'{{'+kind+'}}','required_for':['succeeded','partial']} for name,kind in [('gate','gate'),('ui_report','report'),('ux_report','report'),('environment','environment'),('release','release')]}
 finishes={outcome:{'kind':'finish','outcome':outcome,'output_bindings':{k:'$stages.quality.'+k for k in outputs}} for outcome in ('succeeded','partial')}
 workflow={'authoring':'prifly-project-workflow/3','package':{'id':'aif-composed:package/ui-ux','version':'1.0.0','description':'Public provider components with pinned shared schemas.','requires_core_protocol':'1','dependencies':['aif:package/composition-contracts@1.2.0'],'references':refs},'id':'aif-composed:workflow/ui-ux','schema_version':'8','version':'1.0.0','title':'Composed UI/UX review','policy_ref':'{{policy}}','refs':{'configure':'product.configure','quality':'product.quality'},'inputs':{'configuration':{'schema_ref':'{{configuration}}'}},'outputs':outputs,'resumable':{'from_outcomes':['partial','rejected'],'from_cancelled':True},'entry':'configure','limits':{'max_step_instances':8,'max_control_transitions':48,'max_child_depth':2,'max_parallelism':1},'stages':{'configure':{'kind':'step','step_ref':'configure','input_bindings':{'configuration':'$inputs.configuration'},'on':{'pass':'quality','needs_revision':'rejected','fail':'rejected','no_work':'rejected'},'impossible_verdicts':['blocked']},'quality':{'kind':'call','workflow_ref':'quality','input_bindings':{p:'$stages.configure.'+p for p in ('configuration','ui','ux')},'on':{'succeeded':'succeeded','partial':'partial','rejected':'rejected'}},**finishes,'rejected':{'kind':'finish','outcome':'rejected'}}}
 if applicability:
  # A root with only this Call has no accepted prefix to resume.
  # Real development consumers supply their own meaningful accepted stages.
  workflow.pop('resumable',None)
  refs.update(task='aif:schema/task@1.1.0',implementation='aif:schema/implementation@1.2.0',applicability='aif-product:schema/applicability@1.0.0')
  for name,kind in [('implementation','implementation'),('applicability','applicability')]:
   outputs[name]={'schema_ref':'{{'+kind+'}}','required_for':['succeeded','partial']}
  for name in ('ui_report','ux_report','environment','release'):outputs[name]['required_for']=[]
  workflow.update(refs={'quality':'product.review-for-change'},inputs={'task':{'schema_ref':'{{task}}'},'implementation':{'schema_ref':'{{implementation}}'},'configuration':{'schema_ref':'{{configuration}}','required':False}},entry='quality',limits={'max_step_instances':13,'max_control_transitions':80,'max_child_depth':4,'max_parallelism':1})
  workflow['stages']={'quality':{'kind':'call','workflow_ref':'quality','input_bindings':{p:'$inputs.'+p for p in ('task','implementation','configuration')},'on':{'succeeded':'succeeded','partial':'partial','rejected':'rejected'}},**{outcome:{'kind':'finish','outcome':outcome,'output_bindings':{k:'$stages.quality.'+k for k in outputs}} for outcome in ('succeeded','partial')},'rejected':{'kind':'finish','outcome':'rejected'}}
 profile=repository/'.prifly/project.yaml';text=profile.read_text()
 if not re.search(r'^packages:\s*$',text,re.M) or not re.search(r'^launches:\s*$',text,re.M):raise ValueError('Profile needs nonempty packages and launches mappings')
 if re.search(r'^  ui-ux-composed:',text,re.M):raise ValueError('Profile already declares ui-ux-composed')
 text=text.replace('packages:\n','packages:\n  ui-ux-composed:\n    source: .prifly/workflows/ui-ux-composed\n',1)
 text=text.replace('launches:\n','launches:\n  ui-ux-composed:\n    title: Composed UI/UX review\n    description: Public configure and quality imports with shared exact schemas.\n    kind: workflow\n    workflow: .prifly/workflows/ui-ux-composed/workflow.yaml\n',1)
 folder.mkdir(parents=True);(folder/'workflow.yaml').write_text(json.dumps(workflow,indent=2)+'\n');(folder/'extend.yaml').write_text(json.dumps({'authoring':'prifly-extension/5','imports':{'product':'aif-ui-ux'},'extensions':[]},indent=2)+'\n');profile.write_text(text)
 return folder

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repository',type=Path,required=True);p.add_argument('--applicability',action='store_true');a=p.parse_args();print(setup(a.repository,applicability=a.applicability))
if __name__=='__main__':main()
