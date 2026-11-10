#!/usr/bin/env python3
"""Build the inert native schema package; authoring only needs PyYAML 6.0.1.

Install/check use stdlib through install_composition_contracts.py. Native
package import, not the generator, validates these definitions in an authority.
"""
import argparse,hashlib,json,re,shutil
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
PACKAGES=('aif-classic','aif-fix','aif-ui-ux')

def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def digest(raw):return 'sha256:'+hashlib.sha256(raw).hexdigest()
def build():
 sources={};bindings={}
 for package in PACKAGES:
  bindings[package]={}
  # A schema with a compile parameter belongs to each compiled source owner.
  # It cannot be exported as an inert exact schema with an unresolved scalar.
  declaration=ROOT/package/'compile-parameters.yaml'
  owned=set()
  if declaration.is_file():
   parameters=yaml.safe_load(declaration.read_text())['parameters']
   owned={b['schema'] for p in parameters.values() for b in p['bindings']}
  for path in sorted((ROOT/package/'schemas').glob('*.yaml')):
   if 'schema_'+path.stem in owned:continue
   value=yaml.safe_load(path.read_text());ref=value['id']+'@'+value['version'];raw=canonical(value)
   if ref in sources and sources[ref]!=raw:raise ValueError('Conflicting schema identity: '+ref)
   sources[ref]=raw;bindings[package]['contract_schema_'+path.stem]=ref
 for baseline in sorted((ROOT/'contracts/baselines').glob('*/bundle/prifly.package.json')):
  previous=json.loads(baseline.read_text())
  for component in previous['components']:
   logical=component['ref']['id']+'@'+component['ref']['version']
   if logical in sources and digest(sources[logical])!=component['ref']['digest']:
    raise ValueError('Previously admitted schema bytes changed: '+logical)
 baseline_root=ROOT/'contracts/baselines/admitted-1.0.0'
 baseline_lock=json.loads((baseline_root/'lock.json').read_text())
 admitted={c['ref']['id']+'@'+c['ref']['version'] for c in json.loads((baseline_root/'bundle/prifly.package.json').read_text())['components']}
 sources={k:v for k,v in sources.items() if k not in admitted}
 files={};components=[];payload=[]
 for logical,raw in sorted(sources.items()):
  value=json.loads(raw);name='schemas/'+re.sub('[^a-zA-Z0-9_.-]','_',logical)+'.json';sha=digest(raw)
  files[name]=raw;components.append({'kind':'schema','ref':{'id':value['id'],'version':value['version'],'digest':sha},'path':name})
  payload.append({'path':name,'digest':sha,'size_bytes':len(raw),'media_type':'application/json','role':'data'})
 manifest={'schema_version':'1','id':'aif:package/composition-contracts','version':'1.2.0','description':'Shared exact JSON schemas for explicit cross-owner workflow composition; inert, no programs or effects.','requires_core_protocol':'1','dependencies':[baseline_lock['package']],'requested_capabilities':[],'license':'MIT','components':components,'files':payload}
 files['prifly.package.json']=canonical(manifest)
 lock={'schema_version':'aif-composition-contracts-lock/1','package':{'id':manifest['id'],'version':manifest['version'],'digest':digest(files['prifly.package.json'])},'bindings':bindings,'dependency_bundles':{'baselines/admitted-1.0.0':digest((baseline_root/'lock.json').read_bytes())},'files':{path:digest(raw) for path,raw in sorted(files.items())}}
 return files,canonical(lock)+b'\n'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();files,lock=build();target=ROOT/'contracts/bundle'
 actual={str(p.relative_to(target)):p.read_bytes() for p in target.rglob('*') if p.is_file()} if target.exists() else {}
 if a.check:
  assert actual==files,'Regenerate composition contract bundle';assert (ROOT/'contracts/lock.json').read_bytes()==lock,'Regenerate composition contracts lock'
 else:
  if target.exists():shutil.rmtree(target)
  for name,raw in files.items():p=target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
  (ROOT/'contracts/lock.json').write_bytes(lock)
 print(json.dumps({'schemas':len(files)-1,'manifest_sha256':digest(files['prifly.package.json']),'checked':a.check}))
if __name__=='__main__':main()
