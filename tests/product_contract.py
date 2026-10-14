"""Compile independent W2 components and verify their permission/source boundary."""
from pathlib import Path
from verify import HOSTS, ROOT, STEP_VERDICTS, compile_package, run

SHARED = ('schemas/request.yaml','schemas/report.yaml','schemas/candidate.yaml','schemas/gate.yaml',
          'contexts/aif-review.yaml','contexts/review-severity.yaml','contexts/review-bridge.yaml','files/evidence.py')

def check_product(binary, authority, repository, root):
    for relative in SHARED:
        assert (ROOT/'aif-ui-ux'/relative).read_bytes()==(ROOT/'aif-review-evidence'/relative).read_bytes(),relative
    result,documents=compile_package(binary,authority,repository,'aif-ui-ux',root/'product')
    assert result['package']['id']=='aif-product:package/ui-ux'
    assert len(documents)==10
    for lens in ('ui','ux'):
        step=documents['aif-product:step/'+lens]
        assert step['repository_workspace']=='read_only' and step['effects']['class']=='none'
        assert step['model_profile']['requested']=='independent-review'
        assert step['outputs']['report']['required_for']==['pass','needs_revision','blocked']
    for name,operation in [('environment','ensure'),('release','release')]:
        step=documents['aif-product:step/'+name]
        assert step['effects']=={'class':'external_write','retry_class':'reconcile_required'}
        assert step['external_write']['operations']==[operation]
        assert step['repository_workspace']=='read_only'
    for key,graph in documents.items():
        if key.startswith('aif-product:workflow/'):
            for stage in graph['definition']['stages'].values():
                if stage['kind']=='step':assert set(stage['on'])|set(stage.get('impossible_verdicts',[]))==set(STEP_VERDICTS)
    for host in HOSTS:compile_package(binary,authority,repository,'aif-ui-ux',root/('product-'+host),host=host)
    package=repository/'.prifly/workflows/aif-ui-ux'
    for relative,before,after,expected in (
        ('workflows/quality.yaml','      environment: $stages.environment.environment','      environment: $stages.ui.environment','unknown_port'),
        ('workflows/quality.yaml','      blocked: ux\n','','missing_handler'),
    ):
        p=package/relative;original=p.read_text();assert before in original
        try:
            p.write_text(original.replace(before,after,1))
            error=run(binary,'--project',authority,'project','compile','--repository',repository,'--package','aif-ui-ux','--host','codex-cli','--output',root/('product-negative-'+expected),expect_ok=False)
            assert expected in error,error
        finally:p.write_text(original)
    return len(documents)
