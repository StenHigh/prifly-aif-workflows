#!/usr/bin/env python3
"""Measure project settings, profiles and composition before task validation.

Only disposable repositories/authorities and synthetic text are used. Assisted
worker responses are supplied by this script; no AI session or program runs.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify

FIXTURE = verify.ROOT / "tests/fixtures/task-description-limit"


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def check(binary, report):
    with tempfile.TemporaryDirectory(prefix="task-limit-") as temporary:
        root = Path(temporary)
        repository, authority = root / "repository", root / "authority"
        repository.mkdir()
        calls, runs = [], []
        report["calls"] = calls

        def invoke(*args, code=None):
            arguments = [str(binary), "--json", "--project", str(authority), *map(str, args)]
            result = subprocess.run(arguments, capture_output=True, text=True, timeout=120)
            event = {"args": list(map(str, args)), "exit_code": result.returncode}
            calls.append(event)
            if result.returncode:
                event["problem"] = json.loads(result.stderr.strip().splitlines()[-1])
                assert code and event["problem"]["code"] == code, event
                return event["problem"]
            assert code is None, event
            value = json.loads(result.stdout)
            assert not (value.get("receipt") or {}).get("rejection"), value
            return value

        def snapshot():
            paths = [p for p in repository.rglob("*") if p.is_file()]
            return {
                "files": {str(p.relative_to(repository)): digest(p.read_bytes()) for p in paths},
                "runs": invoke("run", "list"),
                "claims": invoke("claim", "list"),
                "packages": invoke("package", "list"),
            }

        def compile_package(package="probe", values=(), **kwargs):
            output = root / f"compiled-{len(calls)}"
            value_arguments = [arg for value in values for arg in ("--value", value)]
            compiled = invoke("project", "compile", "--repository", repository, "--package", package,
                              "--host", "codex-cli", "--output", output, *value_arguments, **kwargs)
            if kwargs.get("code"):
                return compiled
            documents = {
                c["ref"]["id"]: json.loads((output / c["path"]).read_text())
                for c in compiled["components"] if c["kind"] != "context"
            }
            schema = documents["limit-probe:schema/task"]
            effective = schema.get("definition", schema)
            # Compiled schema has its own envelope; preserve it for diagnosis.
            if "properties" not in effective:
                effective = effective["schema"]
            consumers = [document for document in documents.values() if "task" in document.get("inputs", {})]
            refs = [document[ports]["task"]["schema_ref"]
                    for document in consumers for ports in ("inputs", "outputs")]
            assert len(refs) == 6 and all(ref == refs[0] for ref in refs), refs
            return compiled, documents, effective

        def arguments(taskfile, launch="probe"):
            return ("--repository", repository, "--launch", launch, "--host", "codex-cli",
                    "--input", f"task={taskfile}")

        def validate(length, limit, accepted, launch="probe", execute=False):
            # A non-BMP emoji makes a byte/UTF-16 length substitution observable.
            value = {"title": "Issue #3 synthetic task", "description": "я" * (length - 1) + "😀"}
            taskfile = root / f"task-{length}.json"
            write_json(taskfile, value)
            before = snapshot()
            prepared = invoke("project", "questionnaire", *arguments(taskfile, launch), "--prepare",
                              **({} if accepted else {"code": "schema_invalid"}))
            assert snapshot() == before, "prepare changed files, Runs or claims"
            case = {"launch": launch, "length": length, "effective_limit": limit,
                    "prepare_read_only": True, "accepted": accepted}
            if not accepted:
                case["prepare_problem"] = prepared
                started = invoke("project", "start", *arguments(taskfile, launch), code="schema_invalid")
                assert snapshot() == before, "refused start changed files, Runs or claims"
                case["start_problem"] = started
                for problem in (prepared, started):
                    assert problem["violations"][0]["pointer"] == "/description", problem
                    assert str(limit) in problem["message"] and str(length) in problem["message"], problem
            elif execute:
                started = invoke("project", "start", *arguments(taskfile, launch),
                                 "--expected-launch-digest", prepared["review_digest"])
                run_id = started["run"]["run"]["id"]
                runs.append(run_id)
                invoke("run", "drive", run_id)
                tasks = invoke("session", "task", "--run", run_id, "--all")["tasks"]
                assert len(tasks) == 1, tasks
                task = tasks[0]
                incoming = Path(task["workspace"]) / task["context"]["inputs"]["task"]["path"]
                raw = incoming.read_bytes()
                assert json.loads(raw) == value, "task changed before reaching child worker"
                template = invoke("session", "submit", "--template", "--run", run_id,
                                  "--attempt", task["attempt_id"])
                outgoing = Path(task["workspace"]) / task["context"]["outputs"]["task"]["path"]
                outgoing.parent.mkdir(parents=True, exist_ok=True)
                outgoing.write_bytes(raw)
                template["result"]["outputs"]["task"]["digest"] = digest(raw)
                template["result"].update(verdict="pass", summary="Synthetic full task echo; no LLM")
                template["answered_questions"] = []
                submission = root / "submission.json"
                write_json(submission, template)
                invoke("session", "submit", "--file", submission)
                invoke("run", "drive", run_id)
                status = invoke("run", "status", run_id)["run"]
                assert status["status"] == "completed" and status["outcome"] == "succeeded", status
                assert status["output_artifacts"]["task"]["digest"] == digest(raw), status
                case.update(run_id=run_id, outcome=status["outcome"], worker_task_unchanged=True,
                            root_output_unchanged=True, worker_task_digest=digest(raw), run=status)
            report["validation"].append(case)
            return case

        try:
            # --project above points at exactly the disposable state root being initialised.
            invoke("project", "init", "--repository", repository, "--state-root", authority,
                   "--host", "codex-cli")
            folder = repository / ".prifly/workflows/probe"
            shutil.copytree(FIXTURE, folder)
            profile = {"schema_version": "prifly-project-profile/5",
                       "hosts": {"codex-cli": ".codex/skills"},
                       "packages": {"probe": {"source": ".prifly/workflows/probe"}},
                       "launches": {"probe": {"kind": "workflow", "title": "Task limit probe",
                                      "description": "Synthetic schema boundary; no application",
                                      "workflow": ".prifly/workflows/probe/workflow.yaml"}}}
            write_json(repository / ".prifly/project.yaml", profile)
            extension = folder / "extend.yaml"
            report["validation"] = []
            compiled, documents, schema = compile_package()
            assert schema["properties"]["description"]["maxLength"] == 12000, schema
            report["default_build"] = compiled
            report["default_documents"] = documents
            validate(12000, 12000, True, execute=True)
            validate(12001, 12000, False)
            validate(16557, 12000, False)

            write_json(extension, {"authoring": "prifly-extension/5", "settings": {
                "root": {"task_description_limit": 32000}}})
            compiled, documents, schema = compile_package()
            workflow = documents["limit-probe:workflow/root"]
            assert workflow["inputs"]["task_description_limit"]["configuration"]["default"] == 32000, workflow
            assert schema["properties"]["description"]["maxLength"] == 12000, schema
            report["settings_only"] = {"configuration_default": 32000, "task_max_length": 12000,
                                       "compiled": compiled}
            validate(16557, 12000, False)

            write_json(extension, {"authoring": "prifly-extension/5", "settings": {
                "root": {"undeclared_limit": 32000}}})
            report["undeclared_setting"] = compile_package(code="project_option_unknown_input")
            write_json(extension, {"authoring": "prifly-extension/5", "settings": {
                "root": {"task": {"description_limit": 32000}}}})
            report["task_as_setting"] = compile_package(code="project_option_not_project_scoped")

            write_json(extension, {"authoring": "prifly-extension/5", "references": {
                "schema_task": "limit-probe:schema/task@1.0.0"}})
            report["reference_override"] = compile_package(code="project_composition_reference_conflict")

            write_json(extension, {"authoring": "prifly-extension/5", "profile": "expanded"})
            compiled, documents, schema = compile_package()
            assert schema["properties"]["description"]["maxLength"] == 32000, schema
            report["expanded_build"] = compiled
            report["expanded_documents"] = documents
            validate(16557, 32000, True, execute=True)
            validate(32000, 32000, True, execute=True)
            validate(32001, 32000, False)
            write_json(extension, {"authoring": "prifly-extension/5", "profile": "project40000"})
            report["undeclared_profile"] = compile_package(code="project_compile_unknown_profile")

            # Composition inherits the parent's contract; settings do not patch it.
            derived = repository / ".prifly/workflows/derived"
            write_json(derived / "workflow.yaml", {
                "authoring": "prifly-project-workflow/3",
                "package": {"id": "limit-probe:package/derived", "version": "1.0.0",
                            "description": "Project-owned derived consumer", "requires_core_protocol": "1"},
                "id": "limit-probe:workflow/derived", "version": "1.0.0",
                "title": "Derived root", "extends": "probe"})
            write_json(extension, {"authoring": "prifly-extension/5", "profile": "standard"})
            write_json(derived / "extend.yaml", {"authoring": "prifly-extension/5",
                                                 "settings": {"root": {"task_description_limit": 32000}}})
            profile["packages"]["derived"] = {"source": ".prifly/workflows/derived"}
            profile["launches"]["derived"] = {"kind": "workflow", "title": "Derived probe",
                                                "description": "Owner composition control",
                                                "workflow": ".prifly/workflows/derived/workflow.yaml"}
            write_json(repository / ".prifly/project.yaml", profile)
            compiled, documents, schema = compile_package("derived")
            assert schema["properties"]["description"]["maxLength"] == 12000, schema
            report["derived_settings_only"] = {"compiled": compiled, "task_max_length": 12000}
            validate(16557, 12000, False, launch="derived")

            # --value is supported for standalone compile. It cannot override a
            # profile value or reach project prepare/start's own compilation.
            report["profile_value_override"] = compile_package(
                values=("task_description_limit=40000",), code="project_compile_profile_value_conflict")
            free = repository / ".prifly/workflows/free"
            shutil.copytree(FIXTURE, free)
            source = (free / "workflow.yaml").read_text()
            prefix, profiles_and_tail = source.split("  profiles:\n", 1)
            _, tail = profiles_and_tail.split("  references:\n", 1)
            (free / "workflow.yaml").write_text(prefix + "  references:\n" + tail)
            write_json(free / "extend.yaml", {"authoring": "prifly-extension/5"})
            profile["packages"]["free"] = {"source": ".prifly/workflows/free"}
            profile["launches"]["free"] = {"kind": "workflow", "title": "Explicit compile value probe",
                                             "description": "Compile value without an author preset",
                                             "workflow": ".prifly/workflows/free/workflow.yaml"}
            write_json(repository / ".prifly/project.yaml", profile)
            compiled, documents, schema = compile_package("free", values=("task_description_limit=40000",))
            assert schema["properties"]["description"]["maxLength"] == 40000, schema
            report["explicit_compile_value"] = {"compiled": compiled, "task_max_length": 40000,
                                                "documents": documents}
            invoke("package", "import", "--dir", compiled["output"], "--reason", "Audited inert compile value fixture")
            taskfile = root / "task-16557.json"
            before = snapshot()
            report["prepare_value_flag"] = invoke("project", "questionnaire", *arguments(taskfile, "free"),
                                                  "--prepare", "--value", "task_description_limit=40000",
                                                  code="invalid_usage")
            report["start_value_flag"] = invoke("project", "start", *arguments(taskfile, "free"),
                                                "--value", "task_description_limit=40000", code="invalid_usage")
            report["prepare_missing_compile_value"] = invoke(
                "project", "questionnaire", *arguments(taskfile, "free"), "--prepare",
                code="project_compile_unresolved_values")
            report["start_missing_compile_value"] = invoke(
                "project", "start", *arguments(taskfile, "free"), code="project_compile_unresolved_values")
            assert snapshot() == before, "compile value launch refusal changed files, packages, Runs or claims"
            report["compile_value_refusals_read_only"] = True

            report["run_count"] = invoke("run", "list")["total"]
            assert report["run_count"] == 3, report["run_count"]
            for case in report["validation"]:
                if "run_id" in case:
                    assert invoke("run", "status", case["run_id"])["run"] == case["run"], case["run_id"]
            report["previous_runs_unchanged"] = True
        finally:
            if authority.exists():
                for run_id in runs:
                    state = invoke("run", "status", run_id)["run"]
                    if state["status"] not in ("completed", "failed", "cancelled"):
                        invoke("run", "cancel", run_id, "--reason", "Task limit fixture cleanup")
                        invoke("run", "drive", run_id)
                claims = invoke("claim", "list")["claims"]
                assert not any(c["status"] == "active" for c in claims), claims
                report["cleanup"] = {"active_claims": 0,
                                     "registry_entries_removed": verify.forget_authority(authority)}
                assert report["cleanup"]["registry_entries_removed"] == 1, report["cleanup"]
    assert not root.exists(), root
    report["cleanup"]["temporary_root_removed"] = True


def main():
    if not __debug__:
        raise RuntimeError("Run with Python assertions enabled")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    report = {"prifly": verify.run(binary, "version")["version"],
              "binary_sha256": digest(binary.read_bytes()),
              "probe_sha256": digest(Path(__file__).read_bytes()),
              "fixture_sha256": {str(p.relative_to(FIXTURE)): digest(p.read_bytes())
                                 for p in sorted(FIXTURE.rglob("*")) if p.is_file()},
              "complete": False}
    try:
        check(binary, report)
        report["complete"] = True
    finally:
        write_json(args.output, report)
    print(json.dumps({"complete": report["complete"], "prifly": report["prifly"],
                      "runs": report["run_count"], "validation_cases": len(report["validation"]),
                      "output": str(args.output)}))


if __name__ == "__main__":
    main()
