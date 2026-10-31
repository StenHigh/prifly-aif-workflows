#!/usr/bin/env python3
"""Bounded native transport/anchor reproducer, not AIF receipt acceptance."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify
import run_check as probe
from readability_compare import input_value

FIXTURE = verify.ROOT / "tests/fixtures/report-transport"


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def run_case(binary, case):
    result = {"case": case}
    with tempfile.TemporaryDirectory(prefix="report-transport-") as directory:
        root = Path(directory)
        repository, authority = root / "repository", root / "authority"
        repository.mkdir()
        verify.git("-C", repository, "init", "-q", "-b", "main")
        verify.run(binary, "project", "init", "--repository", repository,
                   "--state-root", authority, "--host", "codex-cli")
        folder = repository / ".prifly/workflows/transport"
        shutil.copytree(FIXTURE, folder)
        profile_path = repository / ".prifly/project.yaml"
        profile = profile_path.read_text()
        assert "packages: {}\n" in profile and "launches: {}\n" in profile
        profile = profile.replace("packages: {}\n", "packages:\n  transport:\n    source: .prifly/workflows/transport\n")
        profile = profile.replace("launches: {}\n", "launches:\n  transport:\n"
                                  "    title: Report transport probe\n"
                                  "    description: Synthetic handoffs without application checks or LLM.\n"
                                  "    kind: workflow\n"
                                  "    workflow: .prifly/workflows/transport/workflow.yaml\n")
        profile_path.write_text(profile)
        (repository / "metadata.txt").write_text("initial\n")
        verify.git("-C", repository, "add", "-A")
        verify.git("-C", repository, "commit", "-q", "-m", "Generic fixture")
        runs, seen, original, produced_workspace = [], [], {}, None

        def call(*args, **kwargs):
            return verify.run(binary, "--project", authority, *args, **kwargs)

        def status(run_id):
            view = call("run", "status", run_id)
            return {key: view[key] for key in ("run_version", "run")}

        def export(ref):
            reference, output = root / "ref.json", root / "export"
            reference.write_text(json.dumps(ref))
            output.unlink(missing_ok=True)
            call("artifact", "export", "--ref", reference, "--output", output)
            raw = output.read_bytes()
            assert digest(raw) == ref["digest"]
            return raw

        def submit(task, verdict, values):
            template = call("session", "submit", "--template", "--run", runs[-1],
                            "--attempt", task["attempt_id"])
            template["result"]["outputs"] = {
                port: template["result"]["outputs"][port] for port in values}
            for port, raw in values.items():
                path = Path(task["workspace"]) / task["context"]["outputs"][port]["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                template["result"]["outputs"][port]["digest"] = digest(raw)
            template["result"].update(verdict=verdict, summary="Synthetic transport probe")
            template["answered_questions"] = []
            path = Path(task["workspace"]) / "submission.json"
            path.write_text(json.dumps(template))
            call("session", "submit", "--file", path)

        try:
            call("project", "compile", "--repository", repository,
                 "--package", "transport", "--host", "codex-cli", "--output", root / "compiled")
            result["root_extension_compiled"] = True
            prepared = call("project", "questionnaire", "--repository", repository,
                            "--launch", "transport", "--host", "codex-cli",
                            "--workspace", "worktree", "--prepare")
            started = call("project", "start", "--repository", repository,
                           "--launch", "transport", "--host", "codex-cli",
                           "--workspace", "worktree", "--expected-launch-digest", prepared["review_digest"])
            runs.append(started["run"]["run"]["id"])
            for _ in range(16):
                call("run", "drive", runs[-1])
                tasks = call("session", "task", "--run", runs[-1], "--all")["tasks"]
                if not tasks:
                    if case == "continue" and len(runs) == 1:
                        source = status(runs[0])
                        assert source["run"]["outcome"] == "partial", source
                        arguments = ("project", "continue", "--repository", repository,
                                     "--launch", "transport", "--host", "codex-cli",
                                     "--source-run", runs[0])
                        prepared = call(*arguments, "--prepare")
                        assert prepared["recovery"]["frontier_stage_id"] == "cycle", prepared
                        assert status(runs[0]) == source
                        reused = {item["stage_id"] for item in prepared["recovery"]["reused"]}
                        assert {"produce", "measure"} <= reused, reused
                        resumed = call(*arguments, "--expected-launch-digest", prepared["review_digest"])
                        runs.append(resumed["run"]["run"]["id"])
                        assert status(runs[0]) == source
                        result["continue"] = {"frontier": prepared["recovery"]["frontier_stage_id"],
                                              "reused": sorted(reused), "source_unchanged": True}
                        continue
                    break
                for task in tasks:
                    role = task["skill_refs"][0]["id"].rsplit("/", 1)[-1]
                    seen.append(role)
                    if role != "produce" and produced_workspace and produced_workspace.exists():
                        # Only remove this fixture's completed producer Attempt directory.
                        assert produced_workspace.is_relative_to(authority)
                        shutil.rmtree(produced_workspace)
                    verdict, values = "pass", {}
                    if role == "produce":
                        produced_workspace = Path(task["workspace"])
                        slots = call("session", "submit", "--template", "--run", runs[-1],
                                     "--attempt", task["attempt_id"])["result"]["outputs"]
                        log = b"original synthetic check: exit=1\n" if case == "failed" else b"original synthetic check: exit=0\n"
                        log_ref = {**slots["log"], "digest": digest(log)}
                        report = {"subject": "dataset:original", "basis": "fixture-contract:1",
                                  "method": "synthetic check", "exit": 1 if case == "failed" else 0,
                                  "status": "failed" if case == "failed" else "passed", "logs": [log_ref]}
                        raw = json.dumps(report).encode()
                        ref = {**slots["report"], "digest": digest(raw)}
                        carrier = {"candidate": "original", "reports": [ref]}
                        original.update(report=raw, ref=ref, log=log, log_ref=log_ref)
                        values = {"log": log, "report": raw, "carrier": json.dumps(carrier).encode()}
                    elif role in ("read", "repair", "measure"):
                        carrier = input_value(task, "carrier")
                        assert carrier["reports"] == [original["ref"]]
                        assert export(carrier["reports"][0]) == original["report"]
                        assert export(original["log_ref"]) == original["log"]
                        if role == "read":
                            if case == "repair" and seen.count("read") == 1:
                                verdict = "needs_revision"
                            elif case == "continue" and len(runs) == 1:
                                verdict = "blocked"
                            elif case == "failed":
                                verdict = "blocked"
                        if role == "repair":
                            tree = Path(task["repository_workspace"])
                            (tree / "metadata.txt").write_text("unrelated metadata changed\n")
                            verify.git("-C", tree, "add", "metadata.txt")
                            verify.git("-C", tree, "commit", "-q", "-m", "Unrelated metadata")
                            carrier["candidate"] = "metadata-repaired"
                            values = {"carrier": json.dumps(carrier).encode()}
                    elif role == "consume":
                        carrier = input_value(task, "carrier")
                        assert carrier["reports"] == [original["ref"]], carrier
                        assert export(carrier["reports"][0]) == original["report"]
                        assert export(original["log_ref"]) == original["log"]
                    else:
                        raise AssertionError(role)
                    submit(task, verdict, values)
            else:
                raise AssertionError("Probe did not stop")
            state = call("run", "status", runs[-1])["run"]
            assert state["status"] == "completed", state
            expected = "partial" if case == "failed" else "succeeded"
            assert state["outcome"] == expected, state
            final = json.loads(export(state["output_artifacts"]["carrier"]))
            assert final["reports"] == [original["ref"]], final
            assert final["candidate"] == ("metadata-repaired" if case == "repair" else "original"), final
            assert seen.count("produce") == 1 and seen.count("measure") == 1, seen
            assert seen.count("read") == (2 if case in ("repair", "continue") else 1), seen
            assert not produced_workspace.exists()
            result.update(status=state["status"], outcome=state["outcome"], handoffs=seen,
                          producer_count=1, project_measurement_handoffs=1,
                          report_ref=original["ref"], report_sha256=digest(original["report"]),
                          original_report=json.loads(original["report"]), producer_directory_removed=True,
                          nested_log_exported=True, runs=len(runs))
            result["invalid_refs"] = {}
            for name, ref in {
                "unknown": {**original["ref"], "artifact_id": "artifact:" + "0" * 64},
                "missing_revision": {**original["ref"], "revision": 2},
                "substituted_digest": {**original["ref"], "digest": "sha256:" + "0" * 64},
            }.items():
                reference = root / "ref.json"
                reference.write_text(json.dumps(ref))
                output = root / "export"
                output.unlink(missing_ok=True)
                refused = call("artifact", "export", "--ref", reference, "--output", output, expect_ok=False)
                code = json.loads(refused.strip().splitlines()[-1])["code"]
                assert code == ("not_found" if name == "unknown" else "integrity_failure"), (name, code)
                result["invalid_refs"][name] = code
            # A supported root insertion is the positive control for this refusal.
            (folder / "extend.yaml").write_bytes((folder / "nested-extension.yaml").read_bytes())
            refused = call("project", "compile", "--repository", repository,
                           "--package", "transport", "--host", "codex-cli",
                           "--output", root / "nested-compiled", expect_ok=False)
            assert "project_extension_unknown_workflow" in refused, refused
            result["nested_extension_refusal"] = json.loads(refused.strip().splitlines()[-1])
        finally:
            try:
                probe.clean(binary, authority, runs)
                claims = call("claim", "list")["claims"]
                assert not any(c["status"] == "active" for c in claims), claims
                result["cleanup"] = {"active_claims": 0}
            finally:
                result.setdefault("cleanup", {})["registry_entries_removed"] = verify.forget_authority(authority)
                assert result["cleanup"]["registry_entries_removed"] == 1
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cases", nargs="+", choices=("success", "repair", "failed", "continue"),
                        default=("success", "repair", "failed", "continue"))
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    report = {"prifly": verify.run(binary, "version")["version"],
              "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
              "boundary": "Generic wiring with synthetic assisted replies; no AIF or LLM acceptance.",
              "cases": [], "complete": False}
    for case in args.cases:
        report["cases"].append(run_case(binary, case))
        print(case, "PASS", flush=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    report["complete"] = True
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
