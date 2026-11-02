#!/usr/bin/env python3
"""Explicitly verify and import the pinned inert schema dependency. Python stdlib."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(raw):return 'sha256:'+hashlib.sha256(raw).hexdigest()
def require(condition, message):
 if not condition:raise ValueError(message)

def verify_directory(directory):
 target=directory/'bundle';lock=json.loads((directory/'lock.json').read_text())
 require(lock['schema_version']=='aif-composition-contracts-lock/1','Unknown schema lock version')
 require(not target.is_symlink(),'Schema bundle root cannot be a symlink')
 actual={}
 for p in target.rglob('*'):
  require(not p.is_symlink(),'Schema bundle cannot contain symlinks')
  if p.is_file():actual[str(p.relative_to(target))]=digest(p.read_bytes())
 require(actual==lock['files'],'Schema bundle bytes differ from the pinned lock')
 require(actual['prifly.package.json']==lock['package']['digest'],'Manifest digest differs from its lock')
 for relative,expected in lock.get('dependency_bundles',{}).items():
  path=directory/relative
  require(not Path(relative).is_absolute() and '..' not in Path(relative).parts,'Unsafe dependency bundle path')
  require(digest((path/'lock.json').read_bytes())==expected,'Dependency lock changed')
  require(verify_directory(path)['package'] in json.loads((target/'prifly.package.json').read_text())['dependencies'],'Dependency differs from manifest')
 return lock

def verify_bundle(root=ROOT):return verify_directory(Path(root)/'contracts')

def import_directory(binary,authority,directory):
 lock=verify_directory(directory)
 for relative in lock.get('dependency_bundles',{}):import_directory(binary,authority,directory/relative)
 result=subprocess.run([str(binary),'--json','--project',str(authority),'package','import','--dir',str(directory/'bundle'),'--reason','Explicit installation of owner-approved pinned composition schemas '+lock['package']['digest']],capture_output=True,text=True,timeout=120)
 require(result.returncode==0,result.stderr)
 value=json.loads(result.stdout);require(not (value.get('receipt') or {}).get('rejection'),str(value))
 return {'package':lock['package'],'receipt':value}

def install(binary,authority,root=ROOT):
 return import_directory(binary,authority,Path(root)/'contracts')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',type=Path);p.add_argument('--project',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args()
 if a.check:print(json.dumps({'verified':verify_bundle()['package']}));return
 if not a.binary or not a.project:p.error('Import requires --binary and --project; use --check for read-only validation')
 print(json.dumps(install(a.binary.resolve(strict=True),a.project.resolve(strict=True))))
if __name__=='__main__':main()
