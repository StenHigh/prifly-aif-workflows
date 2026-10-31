"""Actual local catalog add/update: preserved project overlays and source boundaries."""
import argparse
from pathlib import Path
import shutil
import sys
import tempfile
import verify


def check_install(binary):
    with tempfile.TemporaryDirectory(prefix='w3-install-') as tmp:
        root=Path(tmp);repository,authority=verify.prepare_repository(binary,root)
        try:
            source=root/'source';source.mkdir();shutil.copytree(verify.ROOT/'aif-feature',source/'aif-feature')
            draft=verify.ROOT/'docs/changes/add-bounded-feature-workflow/catalog.draft.yaml'
            (source/'catalog.yaml').write_text(draft.read_text().replace('https://github.com/StenHigh/prifly-aif-workflows.git',source.as_uri()))
            verify.git('-C',source,'init','-q','-b','main');verify.git('-C',source,'add','.');verify.git('-C',source,'commit','-qm','W3 catalog fixture')
            def call(*args):return verify.run(binary,'--project',authority,'project','workflows',*args)
            call('remove','aif-feature','--repository',repository)
            found=call('search','--catalog',source.as_uri());assert 'aif-feature' in str(found)
            call('add','aif-feature','--catalog',source.as_uri(),'--repository',repository)
            installed=repository/'.prifly/workflows/aif-feature'
            for path in (source/'aif-feature').rglob('*'):
                if path.is_file():assert (installed/path.relative_to(source/'aif-feature')).read_bytes()==path.read_bytes(),path
            extend=installed/'extend.yaml';extend.write_text('profile: backend\nsettings:\n  quality: {limit: 2}\nexclude: []\nextensions: []\n')
            overlay=installed/'project/owner.txt';overlay.parent.mkdir();overlay.write_text('Preserve project-owned adapter\n')
            p=source/'aif-feature/README.md';p.write_text(p.read_text()+'\nFixture update only.\n')
            # A real released update would bump version; this unpublished source fixture tests transfer only.
            verify.git('-C',source,'add','.');verify.git('-C',source,'commit','-qm','Fixture update')
            call('update','aif-feature','--repository',repository)
            assert 'limit: 2' in extend.read_text() and overlay.read_text()=='Preserve project-owned adapter\n'
            assert (installed/'README.md').read_bytes()==p.read_bytes()
            verify.compile_package(binary,authority,repository,'aif-feature',root/'compiled')
            changed=installed/'instructions/feature-review.md';changed.write_text(changed.read_text()+'\n# Unreviewed local upstream edit\n')
            refusal=verify.run(binary,'--project',authority,'project','workflows','update','aif-feature','--repository',repository,expect_ok=False)
            assert 'project_workflow_modified' in refusal and 'instructions/feature-review.md' in refusal,refusal
            return {'outcome':'passed','catalog':'local unpublished fixture','installed_bytes':'matched','project_overlay':'preserved','extend':'preserved','local_edit':'refused'}
        finally:verify.forget_authority(authority)


if __name__=='__main__':
    import json
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--binary',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(check_install(args.binary)))
