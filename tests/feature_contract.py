"""Three-host compilation of independent W3 and unchanged W1/W2 worker bytes."""
import hashlib
from verify import HOSTS, ROOT, STEP_VERDICTS, compile_package, run


def check_feature(binary, authority, repository, root):
    result, documents=compile_package(binary,authority,repository,'aif-feature',root/'feature')
    assert result['package']['id']=='aif-feature:package/feature'
    assert len(documents)==25
    graph=documents['aif-feature:workflow/feature']
    assert graph['resumable']=={'from_outcomes':['partial','rejected'],'from_cancelled':True}
    assert set(graph['outputs'])=={'implementation','result','plan','gate','evidence'}
    assert not any('/fix' in key or '/improve' in key or '/challenge' in key for key in documents)
    assert graph['limits']['max_step_instances']>=118
    assert graph['limits']['max_child_depth']==4
    acceptance=documents['aif-feature:workflow/quality']
    assert acceptance['limits']['max_step_instances']==114
    assert 'commit' in acceptance['definition']['stages'] and 'commit' not in graph['definition']['stages']
    assert acceptance['definition']['stages']['round']['on_complete']['succeeded']=='guard'
    snapshot=next(x['ref'] for x in result['components'] if x['ref']['id']=='aif-feature:context/candidate-snapshot')
    assert snapshot['digest']=='sha256:'+hashlib.sha256((ROOT/'aif-feature/files/evidence.py').read_bytes()).hexdigest()
    for key,d in documents.items():
        if 'workflow/' in key:
            for stage in d['definition']['stages'].values():
                if stage['kind']=='step':assert set(stage['on'])|set(stage.get('impossible_verdicts',[]))==set(STEP_VERDICTS),(key,stage)
    for name in ('checks','security','review'):
        d=documents['aif-feature:step/'+name]
        assert d['repository_workspace']=='read_only' and d['effects']['class']=='none'
        assert d['model_profile']['requested']=='independent-review'
    for name in ('plan','implement','repair','commit'):
        assert documents['aif-feature:step/'+name]['effects']=={'class':'workspace_write','retry_class':'never'}
    for name in ('plan','implement'):
        capture=documents['aif-feature:step/'+name]['workspace_trees'][0]
        assert capture['capture']=={'kind':'exact_file','path':'.ai-factory/PLAN.md'}
    assert documents['aif-feature:step/implement']['workspace_trees'][0]['input_port']=='plan'
    assert 'plan' not in documents['aif-feature:step/repair']['inputs']
    for path in (ROOT/'aif-ui-ux/files').glob('*.py'):
        if path.name!='preview.py':assert (ROOT/'aif-feature/files'/path.name).read_bytes()==path.read_bytes(),path
    for path in (ROOT/'aif-ui-ux/contexts').glob('*.yaml'):
        assert (ROOT/'aif-feature/contexts'/path.name).read_bytes()==path.read_bytes(),path
    for host in HOSTS:
        for profile in ('backend','frontend'):
            _,compiled=compile_package(binary,authority,repository,'aif-feature',root/('feature-'+host+'-'+profile),host=host,profile=profile)
            assert compiled['aif-feature:workflow/feature']['inputs']['surface']['configuration']['default']==profile
    q=run(binary,'--project',authority,'project','questionnaire','--repository',repository,'--package','aif-feature')
    assert {x['id'] for x in q['decision_states']}=={'plan_tests','plan_constraints','plan_retention'}
    package=repository/'.prifly/workflows/aif-feature'
    for name,relative,before,after,expected in (
        ('missing-handler','workflows/quality-round.yaml','      blocked: security\n','', 'missing_handler'),
        ('unknown-port','workflows/quality-round.yaml','candidate: $stages.capture.candidate','candidate: $stages.capture.unknown','unknown_port'),
    ):
        path=package/relative;original=path.read_text();assert before in original
        try:
            path.write_text(original.replace(before,after,1))
            error=run(binary,'--project',authority,'project','compile','--repository',repository,'--package','aif-feature','--host','codex-cli','--output',root/('feature-negative-'+name),expect_ok=False)
            assert expected in error,error
        finally:path.write_text(original)
    return len(documents)
