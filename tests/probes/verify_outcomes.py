#!/usr/bin/env python3
"""Real classic/profiled stops and continuation on released Pri-Fly; no model calls."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify
import run_check as probe
from readability_compare import input_value, submit


PACKAGES = ("aif-classic", "aif-profiled")
CASES = ("fail", "no_work", "fail-after-fix", "no_work-after-fix", "fix-fail", "fix-no_work")
PREFIX = {"warmup", "plan", "improve", "implement"}


def snapshot(tree):
    """Candidate bytes and index, excluding the engine's materialised read-only plan."""
    return {
        "head": probe.git_out(tree, "rev-parse", "HEAD"),
        "index": probe.git_out(tree, "diff", "--cached", "--binary"),
        "work": probe.git_out(tree, "diff", "--binary"),
        "files": {name: (tree / name).read_text() for name in
                  ("hello.txt", "owner.txt", "owner-staged.txt") if (tree / name).exists()},
    }


def start(binary, authority, repository, package, taskfile):
    # The ready task and reviewed questionnaire/start command match examples/classic.
    arguments = ("--project", authority, "project")
    options = ("--repository", repository, "--launch", package, "--host", "codex-cli",
               "--input", f"task={taskfile}", "--workspace", "worktree", "--package-profile", "fast",
               "--decision-policy", "attended", "--preflight-answer", "plan_tests=true",
               "--preflight-answer", 'gate_warnings="ignore"', "--preflight-answer",
               'gate_checks="python3 -m unittest discover -s tests"', "--preflight-answer",
               'plan_constraints=""', "--preflight-answer", 'roadmap_linkage="skip"')
    prepared = verify.run(binary, *arguments, "questionnaire", *options, "--prepare")
    return verify.run(binary, *arguments, "start", *options,
                      "--expected-launch-digest", prepared["review_digest"])["run"]["run"]["id"]


def stopped(state):
    assert (state["status"], state.get("outcome")) == ("completed", "rejected"), {
        key: state.get(key) for key in ("status", "outcome", "diagnostics")}
    assert state["output_artifacts"] == {}, state["output_artifacts"]
    assert not state["has_unresolved_effects"]
    assert not any(d["code"] == "unhandled_child_outcome" for d in state["diagnostics"])


def run_case(binary, source, package, case):
    with tempfile.TemporaryDirectory(prefix="verify-outcome-") as temporary:
        root = Path(temporary)
        repository, authority = verify.prepare_repository(binary, root)
        runs, claims, seen = [], set(), []
        result = {"package": package, "case": case}
        tree, current, plan = None, None, None
        verify_count, fix_count = 0, 0

        def call(*args):
            return verify.run(binary, "--project", authority, *args)

        def status(run_id):
            view = call("run", "status", run_id)
            return {key: view[key] for key in ("run_version", "run")}

        def drive(run_id, resume=False, fail_again=False, candidate=None):
            nonlocal tree, current, plan, verify_count, fix_count
            observed = []
            for _ in range(40):
                call("run", "drive", run_id)
                tasks = call("session", "task", "--run", run_id, "--all")["tasks"]
                if not tasks:
                    return status(run_id)["run"], observed
                for task in tasks:
                    bridge = task["skill_refs"][0]["id"].rsplit("/", 1)[-1]
                    observed.append(bridge)
                    seen.append(bridge)
                    claims.update(claim["id"] for claim in call("claim", "list")["claims"]
                                  if claim["status"] == "active")
                    if task.get("repository_workspace"):
                        task_tree = Path(task["repository_workspace"])
                        assert tree is None or task_tree == tree
                        tree = task_tree
                    if resume:
                        assert observed[0] == "aif-verify-bridge", observed
                        assert snapshot(tree) == candidate, "continue changed the candidate"
                        assert bridge in ("aif-verify-bridge", "aif-security-bridge"), observed
                        if bridge == "aif-security-bridge":
                            assert not fail_again
                            return status(run_id)["run"], observed
                    if bridge == "aif-verify-bridge":
                        if plan is None:
                            plan = input_value(task, "plan")
                        assert input_value(task, "plan") == plan, "continue changed the sealed plan"
                        if not resume:
                            assert input_value(task, "implementation") == current
                    _, verdict, values = probe.answer(task, "pass")
                    if bridge == "aif-implement-bridge":
                        current = values["implementation"]
                    if bridge == "aif-verify-bridge":
                        verify_count += 1
                        if resume:
                            verdict, values = (case, {}) if fail_again else ("pass", {"gate": probe.GATE_PASSED})
                        elif case in ("fail", "no_work") or (case.endswith("-after-fix") and verify_count == 2):
                            verdict, values = case.removesuffix("-after-fix"), {}
                        else:
                            verdict = "needs_revision"
                            values = {"gate": {**probe.GATE_PASSED, "status": "failed", "blocking": True,
                                               "findings": ["Synthetic repairable blocker"], "suggested_next": "/aif-fix"}}
                    if bridge == "aif-fix-bridge":
                        fix_count += 1
                        assert input_value(task, "implementation") == current
                        if case.startswith("fix-"):
                            verdict, values = case.removeprefix("fix-"), {}
                        else:
                            (tree / "hello.txt").write_text("hello repaired\n")
                            probe.git_out(tree, "add", "hello.txt")
                            probe.git_out(tree, "-c", "user.name=probe", "-c", "user.email=probe@example.invalid",
                                          "commit", "-q", "-m", "Repair greeting")
                            current = {**current, "head_commit": probe.git_out(tree, "rev-parse", "HEAD")}
                            verdict, values = "pass", {"implementation": current}
                    assert verdict is not None, (case, bridge)
                    submit(binary, authority, run_id, task, verdict, values)
            raise AssertionError((package, case, "too many turns", observed))

        def continuation(source_run, candidate):
            arguments = ("project", "continue", "--repository", repository, "--launch", package,
                         "--source-run", source_run, "--host", "codex-cli")
            before = {"source": status(source_run), "claims": call("claim", "list")["claims"],
                      "runs": call("run", "list")["runs"], "candidate": snapshot(tree)}
            prepared = call(*arguments, "--prepare")
            after = {"source": status(source_run), "claims": call("claim", "list")["claims"],
                     "runs": call("run", "list")["runs"], "candidate": snapshot(tree)}
            assert before == after, "continue --prepare mutated source/work/claims/inventory"
            assert prepared["recovery"]["frontier_stage_id"] == "verify", prepared["recovery"]
            assert prepared["recovery"]["frontier_action"] == "execute", prepared["recovery"]
            reused = {item["stage_id"] for item in prepared["recovery"]["reused"]}
            assert PREFIX <= reused and "verify" not in reused, reused
            next_run = call(*arguments, "--expected-launch-digest", prepared["review_digest"])["run"]["run"]["id"]
            runs.append(next_run)
            assert snapshot(tree) == candidate
            assert status(source_run) == before["source"], "continue rewrote its source"
            return next_run

        try:
            # Each launch works without any other package installed, including classic for profiled.
            for folder in (repository / ".prifly/workflows").iterdir():
                shutil.rmtree(folder)
            folder = repository / ".prifly/workflows" / package
            shutil.copytree(source / package, folder)
            profile = repository / ".prifly/project.yaml"
            text = re.sub(r"(?ms)^packages:\n.*?(?=^\S|\Z)",
                          f"packages:\n  {package}:\n    source: .prifly/workflows/{package}\n", profile.read_text())
            text = re.sub(r"(?ms)^launches:\n.*?(?=^\S|\Z)",
                          f"launches:\n  {package}:\n    title: Verify outcome probe\n"
                          "    description: Released runtime outcome and continuation probe.\n"
                          f"    kind: workflow\n    workflow: .prifly/workflows/{package}/workflow.yaml\n", text)
            profile.write_text(text)
            extend = folder / "extend.yaml"
            extend.write_text(extend.read_text().replace("exclude: []", "exclude: [improve]"))
            taskfile = root / "task.json"
            shutil.copyfile(verify.ROOT / "examples/classic/task.json", taskfile)
            verify.git("-C", repository, "add", "-A")
            verify.git("-C", repository, "commit", "-q", "-m", "Configure isolated outcome probe")
            run_id = start(binary, authority, repository, package, taskfile)
            runs.append(run_id)
            state, first = drive(run_id)
            stopped(state)
            assert not any(name in first for name in ("aif-security-bridge", "aif-review-bridge",
                                                     "aif-review-challenge-bridge", "aif-commit-bridge")), first
            assert fix_count == (0 if case in ("fail", "no_work") else 1)
            assert verify_count == (2 if case.endswith("-after-fix") else 1)
            assert (tree / "hello.txt").read_text() == ("hello repaired\n" if case.endswith("-after-fix") else "hello\n")
            # Both untracked work and the staged index belong to the owner across continuation.
            (tree / "owner.txt").write_text("Preserve untracked owner work\n")
            (tree / "owner-staged.txt").write_text("Preserve staged owner work\n")
            probe.git_out(tree, "add", "owner-staged.txt")
            candidate = snapshot(tree)
            if case in ("fail", "no_work"):
                run_id = continuation(run_id, candidate)
                repeated, observed = drive(run_id, resume=True, fail_again=True, candidate=candidate)
                stopped(repeated)
                assert observed == ["aif-verify-bridge"]
            run_id = continuation(run_id, candidate)
            continued, observed = drive(run_id, resume=True, candidate=candidate)
            assert observed == ["aif-verify-bridge", "aif-security-bridge"], observed
            assert continued["status"] == "running"
            assert len(claims) == 1, claims
            assert snapshot(tree) == candidate
            result.update(status=state["status"], outcome=state["outcome"], root_outputs=state["output_artifacts"],
                          runs=len(runs), first_bridges=first, continue_bridges=observed,
                          same_claim=True, candidate_preserved=True, plan_preserved=True,
                          prepare_read_only=True, prefix_reused=sorted(PREFIX),
                          repeated_rejection_checked=case in ("fail", "no_work"))
            return result
        finally:
            try:
                probe.clean(binary, authority, runs)
                assert not any(c["status"] == "active" for c in call("claim", "list")["claims"])
                result["cleanup"] = {"active_claims": 0}
            finally:
                removed = verify.forget_authority(authority)
                assert removed == 1, removed
                result.setdefault("cleanup", {})["registry_entries_removed"] = removed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--source", type=Path, default=verify.ROOT)
    parser.add_argument("--package", choices=PACKAGES)
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--jobs", type=int, default=1, choices=range(1, 4))
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    binary = args.binary.resolve()
    matrix = [(package, case) for package in ([args.package] if args.package else PACKAGES)
              for case in ([args.case] if args.case else CASES)]
    report = {"prifly": verify.run(binary, "version")["version"],
              "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
              "boundary": "real CLI/Runs/Git, synthetic replies, no model acceptance",
              "expected_cases": len(matrix), "complete": False, "cases": [], "errors": []}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(run_case, binary, args.source.resolve(), package, case): (package, case)
                   for package, case in matrix}
        for future in as_completed(futures):
            package, case = futures[future]
            try:
                result = future.result()
                report["cases"].append(result)
                print(json.dumps(result), flush=True)
            except Exception as error:
                traceback.print_exc()
                report["errors"].append({"package": package, "case": case, "error": str(error)})
                print(f"FAIL {package} {case}: {error}", file=sys.stderr, flush=True)
            report["cases"].sort(key=lambda item: (item["package"], item["case"]))
            args.report.write_text(json.dumps(report, indent=2) + "\n")
    report["complete"] = not report["errors"] and len(report["cases"]) == len(matrix)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
