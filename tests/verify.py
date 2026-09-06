#!/usr/bin/env python3
"""Compile both AI Factory packages with a real Pri-Fly binary and check the sealed contracts.

No network, AI Factory runtime or LLM is involved: host skills are stubs, and
nothing is imported into an authority or started as a Run.
"""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {"codex-cli": ".codex/skills", "codex-app": ".agents/skills", "claude-code": ".claude/skills"}
CLASSIC_SKILLS = ("aif-warmup", "aif-plan", "aif-improve", "aif-implement", "aif-verify", "aif-security", "aif-review", "aif-commit", "aif-fix",)
IMPROVE_REFERENCES = ("LIST-MODE.md", "CHECK-MODE.md", "EXAMPLES.md", "VALIDATOR.md")
PROFILE_CAPTURES = {
    "fast": {"kind": "exact_file", "path": ".ai-factory/PLAN.md"},
    "full": {"kind": "direct_child_file", "path": ".ai-factory/plans"},
    "ultra": {"kind": "direct_child_tree", "path": ".ai-factory/plans", "entrypoint": "index.md"},
}
PLAN_STEPS = ("aif:step/plan", "aif:step/improve", "aif:step/implement")
CLASSIC_DECISIONS = {
    "plan_profile": "preflight",
    "plan_tests": "preflight",
    "plan_logging": "preflight",
    "plan_docs": "preflight",
    "roadmap_linkage": "preflight",
    "roadmap_milestone": "preflight",
    "plan_constraints": "preflight",
    "improve_apply": "runtime",
    "gate_warnings": "preflight",
}
# `fast` keeps the whole plan in one file, so how logging and documentation are
# split across plan files is not a question anybody has to answer under it.
FAST_APPLICABILITY = {"plan_logging": "inactive", "plan_docs": "inactive", "roadmap_milestone": "conditional"}


def by_id(entries, key="id"):
    return {entry[key]: entry for entry in entries}


def run(binary, *arguments, expect_ok=True):
    result = subprocess.run([str(binary), "--json", *map(str, arguments)], capture_output=True, text=True, timeout=120)
    if expect_ok:
        assert result.returncode == 0, f"{arguments}: {result.stderr}"
        return json.loads(result.stdout)
    assert result.returncode != 0, f"{arguments} unexpectedly succeeded: {result.stdout}"
    return result.stderr


def git(*arguments):
    subprocess.run(
        ["git", "-c", "user.name=prifly-aif-workflows", "-c", "user.email=ci@example.invalid", "-c", "commit.gpgsign=false", *map(str, arguments)],
        check=True,
        capture_output=True,
        timeout=60,
    )


def prepare_repository(binary, root):
    repository = root / "repository"
    authority = root / "authority"
    repository.mkdir()
    git("-C", repository, "init", "-q", "-b", "main")
    # `prifly-project-profile/3` initialises host-neutral: a host the package
    # compiles for has to be attached on purpose.
    hosts = [argument for host in HOSTS for argument in ("--host", host)]
    run(binary, "project", "init", "--repository", repository, "--state-root", authority, *hosts)
    for name in ("aif-classic", "aif-fanout"):
        shutil.copytree(ROOT / name, repository / ".prifly" / "workflows" / name)
    for skills_root in HOSTS.values():
        for skill in CLASSIC_SKILLS:
            path = repository / skills_root / skill / "SKILL.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {skill}\n")
        # A skill's own reference files are not carried by pinning the skill,
        # so the package pins each one and the host root must hold them.
        for reference in IMPROVE_REFERENCES:
            path = repository / skills_root / "aif-improve" / "references" / reference
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {reference}\n")
    profile = (repository / ".prifly" / "project.yaml").read_text()
    profile = profile.replace("packages: {}\n", "packages:\n  aif-classic:\n    source: .prifly/workflows/aif-classic\n  aif-fanout:\n    source: .prifly/workflows/aif-fanout\n")
    profile = profile.replace(
        "launches: {}\n",
        "launches:\n"
        "  aif-classic:\n    title: AI Factory classic development workflow\n    description: Canonical AI Factory development workflow with bounded plan improvement.\n    kind: workflow\n    workflow: .prifly/workflows/aif-classic/workflow.yaml\n"
        "  aif-fanout:\n    title: AI Factory fan-out plan refinement\n    description: Optional AI Factory plan refinement with independent review perspectives.\n    kind: workflow\n    workflow: .prifly/workflows/aif-fanout/workflow.yaml\n",
    )
    (repository / ".prifly" / "project.yaml").write_text(profile)
    return repository, authority


def compile_package(binary, authority, repository, package, output, host="codex-cli", profile=None):
    arguments = ["--project", authority, "project", "compile", "--repository", repository, "--package", package, "--host", host, "--output", output]
    if profile:
        arguments += ["--package-profile", profile]
    result = run(binary, *arguments)
    documents = {}
    for component in result["components"]:
        if component["kind"] in ("workflow", "step"):
            documents[component["ref"]["id"]] = json.loads((output / component["path"]).read_text())
    return result, documents


def applicability_under(binary, authority, repository, package_profile=None):
    arguments = ["--project", authority, "project", "questionnaire", "--repository", repository, "--package", "aif-classic"]
    if package_profile:
        arguments += ["--package-profile", package_profile]
    questionnaire = run(binary, *arguments)
    states = by_id(questionnaire["decision_states"], "decision_id")
    assert {name: state["phase"] for name, state in states.items()} == CLASSIC_DECISIONS, questionnaire["decision_states"]
    applicability = {name: state["applicability"] for name, state in states.items()}
    # A decision the profile switched off is left out of the phase lists, so the
    # two lists together must still account for every declared decision.
    for phase in ("preflight", "runtime"):
        expected = {name for name, state in applicability.items() if state != "inactive" and CLASSIC_DECISIONS[name] == phase}
        assert set(by_id(questionnaire[phase])) == expected, (phase, questionnaire[phase])
    return questionnaire, applicability


def expected_applicability(**overrides):
    return {name: overrides.get(name, FAST_APPLICABILITY.get(name, "applicable")) for name in CLASSIC_DECISIONS}


def check_questionnaire(binary, authority, repository):
    questionnaire, applicability = applicability_under(binary, authority, repository)
    assert questionnaire["schema_version"] == "project-questionnaire/3", questionnaire["schema_version"]
    assert questionnaire["project_profile_version"] == "prifly-project-profile/3", questionnaire["project_profile_version"]
    # The form reports what it read from the sealed catalog; a question a skill
    # invents mid-Run is not covered by it and must not look answered here.
    assert questionnaire["known_questions_only"] is True, questionnaire
    assert [(entry["id"], entry["default"]) for entry in questionnaire["profiles"]] == [("fast", True), ("full", False), ("ultra", False)], questionnaire["profiles"]
    assert applicability == expected_applicability(), applicability
    milestone = by_id(questionnaire["preflight"])["roadmap_milestone"]
    assert milestone["when"]["answers"] == {"roadmap_linkage": "link"}, milestone
    # The two questions `fast` switches off are not gone, they belong to the
    # deeper plan layouts; asking under `full` is what tells the two apart.
    _, deeper = applicability_under(binary, authority, repository, "full")
    assert deeper == expected_applicability(plan_logging="applicable", plan_docs="applicable"), deeper


def check_classic(binary, authority, repository, root):
    listed = run(binary, "--project", authority, "project", "workflows", "--repository", repository)
    assert [launch["id"] for launch in listed["launches"]] == ["aif-classic", "aif-fanout"], listed
    check_questionnaire(binary, authority, repository)

    extend_path = repository / ".prifly" / "workflows" / "aif-classic" / "extend.yaml"
    reviewed_extend = extend_path.read_text()
    extend_path.write_text("profile: fast\nsettings:\n  improve-batch: {improve_round_limit: 2}\n  improve-series: {improve_batch_limit: 2}\nexclude: [improve, verify, security, review]\nextensions: []\n")

    output = root / "classic"
    result, documents = compile_package(binary, authority, repository, "aif-classic", output)
    assert result["package"]["id"] == "aif:package/classic" and len(result["components"]) == 49, result["package"]
    catalog = by_id(json.loads((output / "decisions.json").read_text())["decisions"])
    assert {name: entry["phase"] for name, entry in catalog.items()} == CLASSIC_DECISIONS, sorted(catalog)
    assert catalog["plan_profile"]["destination"]["kind"] == "package_profile", catalog["plan_profile"]
    assert catalog["roadmap_milestone"]["when"]["answers"] == {"roadmap_linkage": "link"}, catalog["roadmap_milestone"]
    # What warmup distilled has to reach the steps that plan and build, or the
    # step that produced it is a session spent on nothing.
    for step_id in ("aif:step/plan", "aif:step/improve", "aif:step/implement"):
        assert "handoff" in documents[step_id]["inputs"], step_id
    # Taking a refinement changes what the Run was planned to build, so no policy
    # answers this one: an unattended Run is covered by the owner sealing an
    # answer at start. Relabelling it ordinary and automatic would buy the night
    # by dropping the same guard on every attended Run.
    improve = catalog["improve_apply"]
    assert not improve["automatic"] and improve["sensitivity"] == "scope-changing" and "recommendation" not in improve, improve

    for step_id in PLAN_STEPS:
        step = documents[step_id]
        capture = step["workspace_trees"][0]["capture"]
        assert capture["kind"] == "exact_file" and capture["path"] == ".ai-factory/PLAN.md" and step["schema_version"] == "5", step_id
    assert "plan" not in documents["aif:step/plan"]["inputs"], "aif-plan must create, not consume, the first native plan"
    for step_id in ("aif:step/improve", "aif:step/implement"):
        binding = documents[step_id]["workspace_trees"][0]
        assert binding["input_port"] == "plan" and binding["output_port"] == "plan", step_id
    for step_id, primary, upstream in (
        ("aif:step/plan", "aif:context/aif-plan-bridge", "aif:context/aif-plan"),
        ("aif:step/implement", "aif:context/aif-implement-bridge", "aif:context/aif-implement"),
        ("aif:step/commit", "aif:context/aif-commit-bridge", "aif:context/aif-commit"),
    ):
        step = documents[step_id]
        assert step["instructions_ref"]["id"] == primary and [ref["id"] for ref in step["context_refs"]] == [upstream], step_id

    stages = lambda workflow_id: documents[workflow_id]["definition"]["stages"]
    for workflow_id in ("aif:workflow/improve-batch", "aif:workflow/improve-series"):
        assert stages(workflow_id)["improve"]["next_bindings"]["plan"]["from"] == "iteration_output", workflow_id
    root_stages = stages("aif:workflow/classic")
    assert root_stages["warmup"]["on"]["pass"] == "plan"
    assert root_stages["improve"]["workflow_ref"]["id"] == "aif:workflow/improve-or-pass"
    for stage, step_id in (("security", "aif:step/security"), ("commit", "aif:step/commit")):
        assert root_stages[stage]["step_ref"]["id"] == step_id, stage
    # Review is a bounded loop, not a single step: it reviews, fixes what blocks
    # and reviews again, and an exhausted limit is still reported honestly.
    assert root_stages["review"]["workflow_ref"]["id"] == "aif:workflow/review-batch"
    assert root_stages["review"]["on"] == {"succeeded": "commit", "partial": "fix-after-review"}
    assert root_stages["verify"]["workflow_ref"]["id"] == "aif:workflow/verify-batch"
    assert root_stages["verify"]["on"] == {"succeeded": "choose-security", "partial": "fix-after-verify"}
    for terminal in ("fix-after-review", "fix-after-verify"):
        assert root_stages[terminal]["outcome"] == "partial", terminal
    for decision, terminal in (("security-decision", "fix-after-security"),):
        assert root_stages[decision]["branches"][0]["next"] == terminal and root_stages[terminal]["outcome"] == "partial", decision
    for workflow_id, input_name in (
        ("aif:workflow/improve-or-pass", "improve_enabled"),
        ("aif:workflow/classic", "verify_enabled"),
        ("aif:workflow/classic", "security_enabled"),
        ("aif:workflow/classic", "review_enabled"),
    ):
        assert documents[workflow_id]["inputs"][input_name]["configuration"]["default"] is False, (workflow_id, input_name)
    assert documents["aif:workflow/improve-batch"]["inputs"]["improve_round_limit"]["configuration"]["default"] == 2
    assert documents["aif:workflow/improve-series"]["inputs"]["improve_batch_limit"]["configuration"]["default"] == 2
    for workflow_id, workflow in documents.items():
        if workflow_id.startswith("aif:workflow/"):
            assert '"kind":"parallel"' not in json.dumps(workflow, separators=(",", ":")), workflow_id
    for step_id in ("aif:step/verify", "aif:step/security", "aif:step/review"):
        assert documents[step_id]["effects"]["class"] == "none", step_id
    # The package now runs /aif-fix, but only inside the bounded review loop and
    # never as a gate's own doing: a gate that could fix what it found would be
    # marking its own work.
    assert documents["aif:step/fix"]["effects"]["class"] == "workspace_write"
    for gate in ("verify", "review"):
        assert set(stages(f"aif:workflow/{gate}-once")) >= {gate, "fix", "clean", "fixed", "unresolved"}, gate
        assert stages(f"aif:workflow/{gate}-batch")["round"]["continue_on"] == ["partial"], gate
        assert stages(f"aif:workflow/{gate}-batch")["exhausted"]["outcome"] == "partial", "an exhausted limit stays honest"

    for profile, expected in PROFILE_CAPTURES.items():
        _, profiled = compile_package(binary, authority, repository, "aif-classic", root / f"classic-{profile}", profile=profile)
        for step_id in PLAN_STEPS:
            capture = profiled[step_id]["workspace_trees"][0]["capture"]
            for key, value in expected.items():
                assert capture.get(key) == value, (profile, step_id, capture)
    refused = run(binary, "--project", authority, "project", "compile", "--repository", repository, "--package", "aif-classic", "--host", "codex-cli", "--package-profile", "nondefault", "--output", root / "classic-invalid", expect_ok=False)
    assert "project_compile_unknown_profile" in refused, refused
    assert not (root / "classic-invalid").exists()
    assert "profile: fast" in extend_path.read_text(), "per-Run profile compilation must not rewrite extend.yaml"
    extend_path.write_text(reviewed_extend)
    for host in HOSTS:
        compile_package(binary, authority, repository, "aif-classic", root / f"classic-{host}", host=host)


def check_fanout(binary, authority, repository, root):
    result, documents = compile_package(binary, authority, repository, "aif-fanout", root / "fanout")
    assert result["package"]["id"] == "aif:package/fanout", result["package"]
    improve_pass = json.dumps(documents["aif:workflow/improve-pass"], separators=(",", ":"))
    assert '"kind":"parallel"' in improve_pass and "opus" not in improve_pass and "sonnet" not in improve_pass


def main():
    if not __debug__:
        raise RuntimeError("Verification requires enabled Python assertions")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="prifly-aif-") as temporary:
        root = Path(temporary)
        repository, authority = prepare_repository(binary, root)
        before = run(binary, "--project", authority, "package", "list")
        check_classic(binary, authority, repository, root)
        check_fanout(binary, authority, repository, root)
        after = run(binary, "--project", authority, "package", "list")
        assert before == after, "compile must not import or trust a package"
    version = run(binary, "version")
    print(json.dumps({"outcome": "passed", "prifly": version["version"], "packages": ["aif-classic", "aif-fanout"]}))


if __name__ == "__main__":
    main()
