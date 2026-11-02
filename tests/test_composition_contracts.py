"""The explicit schema dependency refuses altered, undeclared and linked bytes."""
import importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('install_contracts',ROOT/'tools/install_composition_contracts.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PinnedContractsTest(unittest.TestCase):
 def test_every_manifest_component_and_payload_is_pinned(self):
  lock=m.verify_bundle();manifest=json.loads((ROOT/'contracts/bundle/prifly.package.json').read_text())
  self.assertEqual(len(manifest['components']),1)
  self.assertEqual(manifest['requested_capabilities'],[])
  for c in manifest['components']:
   self.assertEqual(c['kind'],'schema');self.assertEqual(c['ref']['digest'],lock['files'][c['path']])
 def mutated(self,change):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);shutil.copytree(ROOT/'contracts',root/'contracts');change(root/'contracts/bundle')
   with self.assertRaises(ValueError):m.verify_bundle(root)
 def test_dependency_lock_and_payload_are_pinned(self):
  for mutate_lock in (True,False):
   with self.subTest(mutate_lock=mutate_lock),tempfile.TemporaryDirectory() as directory:
    root=Path(directory);shutil.copytree(ROOT/'contracts',root/'contracts')
    base=root/'contracts/baselines/admitted-1.0.0'
    path=base/'lock.json' if mutate_lock else next((base/'bundle/schemas').glob('*.json'))
    path.write_bytes(path.read_bytes()+b' ')
    with self.assertRaises(ValueError):m.verify_bundle(root)
 def test_previously_exported_schema_copy_is_not_an_additive_export(self):
  def change(root):
   source=next((root.parent/'baselines/admitted-1.0.0/bundle/schemas').glob('*.json'))
   shutil.copyfile(source,root/'schemas'/source.name)
  self.mutated(change)
 def test_changed_schema_is_rejected(self):
  def change(root):
   p=next((root/'schemas').glob('*.json'));p.write_bytes(p.read_bytes()+b' ')
  self.mutated(change)
 def test_undeclared_file_is_rejected(self):self.mutated(lambda root:(root/'extra').write_text('unexpected'))
 def test_symlink_is_rejected(self):self.mutated(lambda root:(root/'linked').symlink_to('prifly.package.json'))
if __name__=='__main__':unittest.main()
