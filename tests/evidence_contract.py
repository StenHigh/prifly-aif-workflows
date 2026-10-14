"""Compile the standalone W1 package; legacy workflow graphs are unchanged."""
from verify import HOSTS, STEP_VERDICTS, compile_package, run


def check_evidence(binary, authority, repository, root):
    result, documents = compile_package(binary, authority, repository, 'aif-review-evidence', root / 'evidence')
    assert result['package']['id'] == 'aif-evidence:package/review-evidence'
    assert len(documents) == 6
    workflow = documents['aif-evidence:workflow/review-evidence']
    assert workflow['resumable'] == {'from_outcomes':['partial','rejected'],'from_cancelled':True}
    assert set(workflow['outputs']) == {'gate','report'}
    assert workflow['definition']['stages']['quality']['kind'] == 'call'
    assert not any(x['effects']['class'] != 'none' for key,x in documents.items() if key.startswith('aif-evidence:step/'))
    for key, graph in documents.items():
        if key.startswith('aif-evidence:workflow/'):
            for stage in graph['definition']['stages'].values():
                if stage['kind']=='step':
                    assert set(stage['on']) | set(stage.get('impossible_verdicts',[])) == set(STEP_VERDICTS)
    reader=documents['aif-evidence:step/review']
    assert reader['repository_workspace']=='read_only'
    assert reader['outputs']['report']['required_for']==['pass','needs_revision','blocked']
    assert reader['model_profile']['requested']=='independent-review'
    for host in HOSTS:
        compile_package(binary,authority,repository,'aif-review-evidence',root/('evidence-'+host),host=host)
    package=repository/'.prifly/workflows/aif-review-evidence'
    for relative,before,after,expected in (
        ('workflows/quality.yaml','    report: $stages.review.report','    report: $stages.capture.report','unknown_port'),
        ('workflows/quality.yaml','      blocked: evaluate\n','', 'missing_handler'),
        ('steps/review.yaml','repository_workspace: read_only','repository_workspace: writable','repository_workspace'),
    ):
        path=package/relative;original=path.read_text();assert before in original
        try:
            path.write_text(original.replace(before,after,1))
            refused=run(binary,'--project',authority,'project','compile','--repository',repository,
                        '--package','aif-review-evidence','--host','codex-cli','--output',root/('evidence-negative-'+expected),expect_ok=False)
            assert expected in refused,refused
        finally:path.write_text(original)
    return len(documents)
