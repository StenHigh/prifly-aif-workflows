"""Compilation contracts for the independently installed bug workflow."""
import json

from verify import HOSTS, STEP_VERDICTS, compile_package, run


def check_fix(binary, authority, repository, root):
    result, documents = compile_package(binary, authority, repository, "aif-fix", root / "fix")
    workflow = documents["aif-fix:workflow/fix"]
    assert result["package"]["id"] == "aif-fix:package/fix"
    assert "plan" not in workflow["outputs"]
    assert workflow["outputs"]["implementation"]["required_for"] == ["succeeded", "partial"]
    assert workflow["resumable"] == {"from_outcomes": ["partial", "rejected"], "from_cancelled": True}
    assert not any("aif:step/implement" == component["ref"]["id"] for component in result["components"])
    assert documents["aif-fix:step/review-task"]["model_profile"]["requested"] == "independent-review"
    for name in ("check-change", "review-task"):
        step = documents[f"aif-fix:step/{name}"]
        assert step["repository_workspace"] == "read_only"
        assert step["effects"]["class"] == "none"
        assert "plan" not in step["inputs"] and "challenge" not in step["inputs"]
    for graph in (item for key, item in documents.items() if key.startswith("aif-fix:workflow/")):
        for stage in graph["definition"]["stages"].values():
            if stage["kind"] == "step":
                assert set(stage["on"]) | set(stage.get("impossible_verdicts", [])) == set(STEP_VERDICTS)
    for name in ("fix-plan", "fix-from-plan"):
        binding = documents[f"aif-fix:step/{name}"]["workspace_trees"][0]
        assert binding["capture"] == {"kind": "exact_file", "path": ".ai-factory/FIX_PLAN.md"}
        assert binding["output_port"] == "fix_plan"
    questionnaire = run(binary, "--project", authority, "project", "questionnaire", "--repository", repository, "--package", "aif-fix")
    assert {entry["id"] for entry in questionnaire["decision_states"]} == {"short_checks", "gate_warnings", "fix_plan_execution"}
    catalog = {entry["id"]: entry for entry in json.loads((root / "fix/decisions.json").read_text())["decisions"]}
    assert not catalog["fix_plan_execution"]["automatic"]
    assert catalog["fix_plan_execution"]["destination"] == {"kind": "session_context", "name": "fix_plan_execution"}
    for name in ('check', 'security', 'review'):
        branches = documents['aif-fix:workflow/quality-round']['definition']['stages'][f'decide-{name}']['branches']
        predicate = branches[0]['predicate']
        assert predicate['op'] == 'eq' and predicate['right'] == {'kind': 'literal', 'value': 'blocked'}
        assert predicate['left']['ref'] == {'from': 'stage_output', 'stage_id': name, 'port': 'gate', 'pointer': '/status'}
        assert branches[0]['next'] == f'blocked-{name}'
    for name in ('warmup', 'fix-task', 'fix-plan', 'fix-from-plan', 'check-change', 'security', 'review-task', 'repair', 'commit'):
        refs = documents[f'aif-fix:step/{name}']['context_refs']
        assert any(ref['id'] == 'aif-fix:context/session-report' for ref in refs), name
    for host in HOSTS:
        compile_package(binary, authority, repository, "aif-fix", root / f"fix-{host}", host=host)
    _, custom = compile_package(binary, authority, repository, "aif-fix", root / "fix-custom", profile="custom")
    assert custom["aif-fix:step/fix-plan"]["workspace_trees"][0]["capture"]["path"] == ".ai-factory/fix-plans/FIX_PLAN.md"
    package = repository / ".prifly/workflows/aif-fix"
    for case, relative, before, after, expected in (
        ("missing-implementation", "workflows/build.yaml",
         "      implementation: $stages.fix-task.implementation\n",
         "", "missing_binding"),
        ("missing-handler", "workflow.yaml", "      blocked: abandoned\n", "", "missing_handler"),
        ("external-effect", "steps/fix-task.yaml", "class: workspace_write", "class: external_write", "external_write"),
    ):
        path = package / relative
        original = path.read_text()
        assert before in original
        try:
            path.write_text(original.replace(before, after, 1))
            refused = run(binary, "--project", authority, "project", "compile", "--repository", repository,
                          "--package", "aif-fix", "--host", "codex-cli", "--output", root / f"fix-invalid-{case}", expect_ok=False)
            assert expected in refused, (case, refused)
        finally:
            path.write_text(original)
    return len(documents)
