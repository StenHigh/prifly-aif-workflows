#!/usr/bin/env python3
"""Reproduce shared-schema admission after remove/revoke in isolated authorities."""

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
sys.path.insert(0, str(verify.ROOT / "tools"))
import install_composition_contracts as contracts

FLAG = "aif:schema/feature-enabled"
LEGACY = "aif:package/classic"


def check(binary, mode):
    with tempfile.TemporaryDirectory(prefix="schema-revocation-") as temporary:
        root = Path(temporary)
        repository, authority = root / "repository", root / "authority"
        repository.mkdir()
        verify.run(binary, "project", "init", "--repository", repository, "--state-root", authority)
        result, run_ids = {"mode": mode}, []

        def call(*args):
            return verify.run(binary, "--project", authority, *args)

        try:
            baseline = verify.ROOT / "contracts/baselines/admitted-1.0.0/bundle"
            manifest = json.loads((baseline / "prifly.package.json").read_text())
            flag = next(c for c in manifest["components"] if c["ref"]["id"] == FLAG)
            result["schema_ref"] = flag["ref"]
            if mode != "clean":
                # Synthetic inert package: one exact published schema, no historical code.
                legacy = root / "legacy"
                (legacy / "schemas").mkdir(parents=True)
                shutil.copyfile(baseline / flag["path"], legacy / flag["path"])
                manifest.update(id=LEGACY, version="1.15.1", description="Synthetic legacy schema supplier",
                                components=[flag], files=[f for f in manifest["files"] if f["path"] == flag["path"]])
                (legacy / "prifly.package.json").write_text(json.dumps(manifest))
                call("package", "import", "--dir", legacy, "--reason", "Isolated legacy supplier fixture")
                call("package", mode, "--id", LEGACY, "--version", "1.15.1",
                     "--reason", "Isolated lifecycle comparison, no real package decision")
            contracts.install(binary, authority)
            inventory = call("package", "list")["packages"]
            result["suppliers"] = [
                {"ref": p["ref"], "status": p["status"], "resolvable": p["resolvable"]}
                for p in inventory if flag["ref"] in p["component_refs"]]
            assert any(p["status"] == "trusted" and p["resolvable"] for p in result["suppliers"])
            call("package", "inspect", "--component", FLAG,
                 "--package", "aif:package/composition-contracts@1.0.0")
            result["trusted_schema_inspect_passed"] = True
            folder = repository / ".prifly/workflows/probe"
            folder.mkdir()
            workflow = {
                "authoring": "prifly-project-workflow/3",
                "package": {"id": "schema-probe:package/consumer", "version": "1.0.0",
                    "description": "Inert shared schema consumer", "requires_core_protocol": "1",
                    "dependencies": ["aif:package/composition-contracts@1.2.0"],
                    "references": {"flag": FLAG + "@1.0.0", "policy": "core:policy/local@4.0.0"}},
                "id": "schema-probe:workflow/consumer", "version": "1.0.0", "schema_version": "4",
                "title": "Inert shared schema consumer", "inputs": {"enabled": {"schema_ref": "{{flag}}"}},
                "outputs": {}, "policy_ref": "{{policy}}", "entry": "done",
                "limits": {"max_step_instances": 1, "max_control_transitions": 4},
                "stages": {"done": {"kind": "finish", "outcome": "succeeded"}},
            }
            (folder / "workflow.yaml").write_text(json.dumps(workflow))
            profile = {"schema_version": "prifly-project-profile/3",
                       "packages": {"probe": {"source": ".prifly/workflows/probe"}},
                       "launches": {"probe": {"kind": "workflow", "title": "Inert shared schema consumer",
                            "description": "No workers or external effects",
                            "workflow": ".prifly/workflows/probe/workflow.yaml"}}}
            (repository / ".prifly/project.yaml").write_text(json.dumps(profile))
            enabled = root / "enabled.json"
            enabled.write_text("true")
            options = ("--repository", repository, "--launch", "probe", "--input", f"enabled={enabled}")
            prepared = call("project", "questionnaire", *options, "--prepare")
            result["prepare_passed"] = True
            done = subprocess.run([str(binary), "--json", "--project", str(authority), "project", "start",
                                   *map(str, options), "--expected-launch-digest", prepared["review_digest"]],
                                  capture_output=True, text=True, timeout=120)
            if done.returncode:
                result["start_refusal"] = json.loads(done.stderr.strip().splitlines()[-1])
                assert mode == "revoke", result
                assert result["start_refusal"]["code"] == "package_not_resolvable", result
                assert FLAG in result["start_refusal"]["message"], result
            else:
                started = json.loads(done.stdout)
                run_id = started["run"]["run"]["id"]
                run_ids.append(run_id)
                call("run", "drive", run_id)
                state = call("run", "status", run_id)["run"]
                result["start_outcome"] = state.get("outcome")
                assert mode != "revoke" and state.get("outcome") == "succeeded", result
            result["runs_created"] = call("run", "list")["total"]
            assert result["runs_created"] == (0 if mode == "revoke" else 1), result
        finally:
            # No workers, claims or external effects exist in this graph.
            for run_id in run_ids:
                state = call("run", "status", run_id)["run"]
                if state["status"] not in ("completed", "cancelled", "failed"):
                    call("run", "cancel", run_id, "--reason", "Fixture cleanup")
                    call("run", "drive", run_id)
            assert not any(c["status"] == "active" for c in call("claim", "list")["claims"])
            result["registry_entries_removed"] = verify.forget_authority(authority)
            assert result["registry_entries_removed"] == 1
        result["temporary_authority_removed"] = True
        return result


def main():
    if not __debug__:
        raise RuntimeError("Reproduction requires enabled Python assertions")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    report = {"prifly": verify.run(binary, "version")["version"],
              "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
              "boundary": "Synthetic schema-only legacy package; no application or live authority modified.",
              "cases": [], "complete": False}
    for mode in ("clean", "remove", "revoke"):
        report["cases"].append(check(binary, mode))
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(mode, "reproduced", flush=True)
    report["complete"] = True
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
