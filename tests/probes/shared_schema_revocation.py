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


def exercise_migration(call, binary, authority, root, options, prepared, flag_refs, run_ids):
    """Approve only synthetic, audited schemas in this disposable authority."""
    # Failed project start rolls back its temporary consumer import to removed.
    # Restore only this newly compiled consumer, never the revoked legacy package.
    compiled = root / "compiled"
    compiled_info = call("project", "compile", "--repository", root / "repository", "--package", "probe", "--output", compiled)
    inventory = call("package", "list")["packages"]
    consumer = next(p["ref"] for p in inventory if p["ref"]["id"] == "schema-probe:package/consumer")
    assert consumer == compiled_info["package"], "review must select the exact compiled consumer"
    consumer_entry = next(p for p in inventory if p["ref"] == consumer)
    assert consumer_entry["status"] == "removed", consumer_entry
    call("package", "restore", "--id", consumer["id"], "--version", consumer["version"],
         "--reason", "Audited inert consumer removed only by failed launch cleanup")
    supplier = next(p["ref"] for p in inventory
                    if p["ref"]["id"] == "aif:package/composition-contracts" and p["ref"]["version"] == "1.0.0")
    request_file, plan_file = root / "request.json", root / "plan.json"
    request = {"schema_version": "schema-migration-request/1", "consumer_ref": consumer, "selections": []}

    def prepare():
        request_file.write_text(json.dumps(request))
        return call("package", "schema-migration", "prepare", "--request", request_file)

    def refusal(*args):
        failed = subprocess.run([str(binary), "--json", "--project", str(authority), *map(str, args)],
                                capture_output=True, text=True, timeout=120)
        assert failed.returncode, failed.stdout
        return json.loads(failed.stderr.strip().splitlines()[-1])["code"]

    before = [call(*args) for args in (("package", "list"), ("run", "list"), ("claim", "list"))]
    diagnostic = prepare()
    after = [call(*args) for args in (("package", "list"), ("run", "list"), ("claim", "list"))]
    assert before == after, "diagnostic prepare changed packages, Runs or claims"
    assert diagnostic["complete"] and not diagnostic["applicable"], diagnostic
    assert sorted(s["schema_ref"]["id"] for s in diagnostic["schemas"]) == sorted(r["id"] for r in flag_refs)
    assert all(s["revocations"][0]["status"] == "revoked" and
               s["revocations"][0]["status_reason"] for s in diagnostic["schemas"])
    plan_file.write_text(json.dumps(diagnostic))
    incomplete = refusal("package", "schema-migration", "apply", "--plan", plan_file,
                         "--expected-review-digest", diagnostic["review_digest"], "--reason", "Fixture incomplete selection")
    assert incomplete == "schema_migration_incomplete", incomplete
    request["selections"] = [{"schema_ref": s["schema_ref"], "supplier_ref": supplier} for s in diagnostic["schemas"]]
    plan = prepare()
    assert plan["complete"] and plan["applicable"], plan
    plan_file.write_text(json.dumps(plan))
    call("package", "revoke", "--id", LEGACY, "--version", "1.15.1", "--reason", "Fixture lifecycle changed after review")
    stale = refusal("package", "schema-migration", "apply", "--plan", plan_file,
                    "--expected-review-digest", plan["review_digest"], "--reason", "Fixture stale review")
    assert stale == "schema_migration_plan_stale", stale
    plan = prepare()
    assert plan["complete"] and plan["applicable"], plan
    plan_file.write_text(json.dumps(plan))
    apply_args = ("package", "schema-migration", "apply", "--plan", plan_file,
                  "--expected-review-digest", plan["review_digest"], "--reason", "Audited inert fixture schemas; mistaken retirement",
                  "--command-id", "command:fixture-schema-migration")
    applied = call(*apply_args)
    decision_id = applied["decision"]["id"]
    assert call("package", "schema-migration", "inspect", "--id", decision_id)["valid"]
    selected = call("project", "questionnaire", *options, "--prepare", "--schema-migration", decision_id)
    assert selected["review_digest"] != prepared["review_digest"], "migration selection must change launch review"
    outdated = refusal("project", "start", *options, "--schema-migration", decision_id,
                       "--expected-launch-digest", prepared["review_digest"])
    assert outdated == "project_start_stale_launch", outdated
    started = call("project", "start", *options, "--schema-migration", decision_id,
                   "--expected-launch-digest", selected["review_digest"])
    run_id = started["run"]["run"]["id"]
    run_ids.append(run_id)
    call("run", "drive", run_id)
    state = call("run", "status", run_id)["run"]
    assert state["outcome"] == "succeeded", state
    binding = state["schema_migration"]
    assert binding["decision_id"] == decision_id and binding["consumer_ref"] == consumer
    assert sorted(s["schema_ref"]["id"] for s in binding["selections"]) == sorted(r["id"] for r in flag_refs)
    unselected = call("project", "questionnaire", *options, "--prepare")
    without_selection = refusal("project", "start", *options, "--expected-launch-digest", unselected["review_digest"])
    assert without_selection == "package_not_resolvable", without_selection
    replay = call(*apply_args)
    assert replay["duplicate"] and replay["receipt"] == applied["receipt"], replay
    call("package", "revoke", "--id", LEGACY, "--version", "1.15.1", "--reason", "Fixture subsequent security decision")
    invalid = call("package", "schema-migration", "inspect", "--id", decision_id)
    assert not invalid["valid"] and invalid["reasons"], invalid
    invalid_start = refusal("project", "start", *options, "--schema-migration", decision_id)
    assert invalid_start == "schema_migration_decision_invalid", invalid_start
    legacy = next(p for p in call("package", "list")["packages"] if p["ref"]["id"] == LEGACY)
    assert legacy["status"] == "revoked" and not legacy["resolvable"], legacy
    assert call("run", "list")["total"] == 1
    return {"consumer_ref": consumer, "supplier_ref": supplier, "consumer_cleanup_restored": True,
            "diagnostic_prepare_read_only": True,
            "diagnostic_schemas": diagnostic["schemas"], "incomplete_apply": incomplete, "stale_apply": stale,
            "review_selection_changed_digest": True, "outdated_launch_review": outdated,
            "explicit_start_outcome": state["outcome"], "run_binding": binding,
            "unselected_start_refusal": without_selection, "apply_replay_duplicate": True,
            "subsequent_revoke_invalidates_decision": True, "invalid_decision_start_refusal": invalid_start,
            "legacy_status": legacy["status"]}


def check(binary, mode, migrate=False):
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
            selected_flags = [flag]
            if migrate:
                selected_flags.append(next(c for c in manifest["components"] if c["ref"]["id"] == "aif:schema/round-limit"))
            result["schema_ref"] = flag["ref"]
            if mode != "clean":
                # Synthetic inert package: exact published schemas, no historical code.
                legacy = root / "legacy"
                (legacy / "schemas").mkdir(parents=True)
                for component in selected_flags:
                    shutil.copyfile(baseline / component["path"], legacy / component["path"])
                manifest.update(id=LEGACY, version="1.15.1", description="Synthetic legacy schema supplier",
                                components=selected_flags,
                                files=[f for f in manifest["files"] if f["path"] in {c["path"] for c in selected_flags}])
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
            if migrate:
                workflow["package"]["references"]["rounds"] = "aif:schema/round-limit@1.1.0"
                workflow["inputs"]["rounds"] = {"schema_ref": "{{rounds}}"}
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
            if migrate:
                rounds = root / "rounds.json"
                rounds.write_text("2")
                options += ("--input", f"rounds={rounds}")
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
            if migrate:
                result["migration"] = exercise_migration(call, binary, authority, root, options, prepared,
                                                         [c["ref"] for c in selected_flags], run_ids)
                result["runs_created"] = call("run", "list")["total"]
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
    parser.add_argument("--exercise-migration", action="store_true",
                        help="Also exercise explicit two-schema migration; requires released Core 0.13.89 or newer")
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
    if args.exercise_migration:
        report["cases"].append(check(binary, "revoke", migrate=True))
        print("explicit migration verified", flush=True)
    report["complete"] = True
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
