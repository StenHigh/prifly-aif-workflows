#!/usr/bin/env python3
"""Compile a branch merge with a real native plan only on the planned route.

No package is imported and no Run is started. Negative variants must fail for
the intended binding violation, not for an unrelated schema or syntax error.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify import forget_authority, run

FIXTURE = Path(__file__).resolve().parent / "route-probe"


def replace_once(path, before, after):
    text = path.read_text()
    assert text.count(before) == 1, (path, before)
    path.write_text(text.replace(before, after))


def main():
    if not __debug__:
        raise RuntimeError("Verification requires enabled Python assertions")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    refusals = {}
    with tempfile.TemporaryDirectory(prefix="prifly-route-") as temporary:
        root = Path(temporary)
        repository, authority = root / "repository", root / "authority"
        repository.mkdir()
        run(binary, "project", "init", "--repository", repository,
            "--state-root", authority, "--host", "codex-cli")
        try:
            project = repository / ".prifly/project.yaml"
            replace_once(project, "packages: {}\n",
                         "packages:\n  route-probe:\n    source: .prifly/workflows/route-probe\n")
            package = repository / ".prifly/workflows/route-probe"
            before = run(binary, "--project", authority, "package", "list")
            cases = ("valid", "required-child-plan", "required-tail-plan",
                     "missing-implementation", "direct-merge", "required-root-plan")
            for case in cases:
                if package.exists():
                    shutil.rmtree(package)
                shutil.copytree(FIXTURE, package)
                child = package / "workflows/build.yaml"
                expected = "unavailable_output"
                if case == "required-child-plan":
                    replace_once(child, "plan: {schema_ref: schema_plan, required_for: []}",
                                 "plan: {schema_ref: schema_plan, required_for: [succeeded]}")
                    expected = "missing_binding"
                elif case == "required-tail-plan":
                    replace_once(package / "steps/tail.yaml", "required: false", "required: true")
                elif case == "missing-implementation":
                    replace_once(child, "output_bindings: {implementation: $stages.fix.implementation}",
                                 "output_bindings: {}")
                    expected = "missing_binding"
                elif case == "direct-merge":
                    # Both successful edges now reach one finish, whose source
                    # exists only on the planned route.
                    replace_once(child, "pass: fix-done", "pass: planned-done")
                    replace_once(child, "  fix-done:\n    kind: finish\n    outcome: succeeded\n"
                                 "    output_bindings: {implementation: $stages.fix.implementation}\n", "")
                elif case == "required-root-plan":
                    replace_once(package / "workflow.yaml",
                                 "plan: {schema_ref: schema_plan, required_for: []}",
                                 "plan: {schema_ref: schema_plan, required_for: [succeeded]}")
                arguments = ("--project", authority, "project", "compile", "--repository",
                             repository, "--package", "route-probe", "--host", "codex-cli",
                             "--output", root / case)
                if case == "valid":
                    result = run(binary, *arguments)
                    documents = {
                        component["ref"]["id"]: json.loads((root / case / component["path"]).read_text())
                        for component in result["components"] if component["kind"] in ("workflow", "step")
                    }
                    build = documents["probe:workflow/build"]
                    assert build["outputs"]["implementation"]["required_for"] == ["succeeded"]
                    assert build["outputs"]["plan"]["required_for"] == []
                    assert "plan" not in build["definition"]["stages"]["fix-done"]["output_bindings"]
                    assert not documents["probe:step/tail"]["inputs"]["plan"]["required"]
                    assert documents["probe:step/planned"]["workspace_trees"][0]["output_port"] == "plan"
                else:
                    refused = run(binary, *arguments, expect_ok=False)
                    problem = json.loads(refused.strip().splitlines()[-1])
                    assert problem["code"] == "project_compile_invalid_workflow", (case, problem)
                    assert problem["message"].startswith(expected + " at "), (case, problem)
                    refusals[case] = {"code": problem["code"], "message": problem["message"]}
            assert before == run(binary, "--project", authority, "package", "list")
        finally:
            forgotten = forget_authority(authority)
            assert forgotten == 1, forgotten
    print(json.dumps({
        "outcome": "passed", "prifly": run(binary, "version")["version"],
        "binary_sha256": "sha256:" + hashlib.sha256(binary.read_bytes()).hexdigest(),
        "valid": "wrapper merge; required implementation, optional native plan",
        "refusals": refusals, "registry_entries_removed": forgotten,
        "boundary": "compile only; no runtime, capture execution or resume",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
