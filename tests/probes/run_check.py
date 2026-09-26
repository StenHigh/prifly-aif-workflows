#!/usr/bin/env python3
"""Drive a real aif-classic Run past the first handoff and answer the verify gate.

The four gates stop at the first assisted handoff, so nothing they run ever
hands verify its attempt. 0.13.53 compiled and started v1.45.0 cleanly and then
refused to issue that attempt at all. This probe is the host: it answers
warmup, plan and implement with the smallest honest artifacts, answers verify
with the verdict asked for, and reports where the Run ended.

    python3 tests/probes/run_check.py --binary /path/to/prifly [--verdict blocked|pass]

`--check` turns the report into a verdict of its own and exits non-zero when
the Run did not get where the gate's verdict says it must: `pass` has to carry
the Run past verify, `blocked` has to end it `partial`. CI runs `--check
--verdict pass` and `--check --verdict blocked`.

`--continue` then continues the finished Run with `prifly project continue` into
`aif-classic-continuation`: the tail's own resume program checks the tree it
is handed, and the tail is driven until its verify gate has been answered
`pass` and the next gate handed out. It needs Node on PATH (the resume step's
executable, allowed in the fixture's local.yaml the way an owner allows it).

`--tag vX.Y.Z` drives that release instead of the working tree. The Run is
cancelled and its claim, registry entry and directory removed whatever happens;
`--keep` leaves the stand for someone else to read.
"""

import argparse
import shutil as _which
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import compatibility  # noqa: E402
import verify  # noqa: E402

MAX_TURNS = 40
GATE_BLOCKED = {
    "gate": "verify",
    "status": "blocked",
    "blocking": False,
    "blocking_owner_only": False,
    "findings": ["PostgreSQL at localhost:5432 did not answer (`pg_isready`: no response); the suite and acceptance checks did not run."],
    "suggested_next": "continue",
}
GATE_PASSED = {**GATE_BLOCKED, "status": "passed", "findings": []}


def git_out(cwd, *arguments):
    return subprocess.run(["git", *arguments], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def prepare(binary, root, tag):
    repository, authority = verify.prepare_repository(binary, root)
    if tag:
        target = repository / ".prifly" / "workflows" / "aif-classic"
        shutil.rmtree(target)
        archive = subprocess.run(["git", "-C", verify.ROOT, "archive", tag, "aif-classic"], capture_output=True, check=True).stdout
        tarfile.open(fileobj=io.BytesIO(archive)).extractall(target.parent, filter="data")
    # Only the verify gate is under test; improve and security would add turns
    # that answer nothing here.
    (repository / ".prifly" / "workflows" / "aif-classic" / "extend.yaml").write_text("profile: fast\nexclude: [improve, security]\nextensions: []\n")
    verify.git("-C", repository, "add", "-A")
    verify.git("-C", repository, "commit", "-q", "-m", "run probe fixture")
    output = root / "seal"
    verify.run(binary, "--project", authority, "project", "compile", "--repository", repository, "--package", "aif-classic", "--host", "codex-cli", "--output", output)
    verify.run(binary, "--project", authority, "package", "import", "--dir", output, "--reason", "run probe")
    task = root / "task.json"
    task.write_text(json.dumps({"title": "Add greeting", "description": "Add hello.txt with a greeting."}))
    return repository, authority, task


def answer(task, verdict):
    """The artifacts and verdict for one handed-out attempt, by the bridge it pins."""
    bridge = task["skill_refs"][0]["id"].rsplit("/", 1)[-1]
    repository = task.get("repository_workspace")
    if bridge == "aif-warmup-bridge":
        return bridge, "pass", {"handoff": {"summary": "Empty fixture repository.", "entry_points": ["README"], "conventions": ["none"], "sources": ["git ls-files"]}}
    if bridge == "aif-plan-bridge":
        (Path(repository) / ".ai-factory").mkdir(exist_ok=True)
        (Path(repository) / ".ai-factory" / "PLAN.md").write_text("# Plan\n\n- [ ] Add hello.txt with a greeting.\n")
        return bridge, "pass", {}
    if bridge == "aif-implement-bridge":
        base = git_out(repository, "rev-parse", "HEAD")
        (Path(repository) / "hello.txt").write_text("hello\n")
        git_out(repository, "add", "hello.txt")
        git_out(repository, "-c", "user.name=probe", "-c", "user.email=probe@example.invalid", "commit", "-q", "-m", "Add greeting")
        return bridge, "pass", {"implementation": {"base_commit": base, "head_commit": git_out(repository, "rev-parse", "HEAD"), "changed_files": ["hello.txt"]}}
    if bridge == "aif-verify-bridge":
        return bridge, verdict, {"gate": GATE_BLOCKED if verdict == "blocked" else GATE_PASSED}
    return bridge, None, None


def submit(binary, authority, run_id, task, verdict, values, bridge):
    template = verify.run(binary, "--project", authority, "session", "submit", "--template", "--run", run_id, "--attempt", task["attempt_id"])
    workspace = Path(task["workspace"])
    for port, value in values.items():
        data = json.dumps(value).encode()
        path = workspace / task["context"]["outputs"][port]["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        template["result"]["outputs"][port]["digest"] = "sha256:" + hashlib.sha256(data).hexdigest()
    template["result"]["verdict"] = verdict
    template["result"]["summary"] = f"run probe: {bridge} -> {verdict}"
    submission = workspace / "submission.json"
    submission.write_text(json.dumps(template))
    result = subprocess.run([str(binary), "--json", "--project", str(authority), "session", "submit", "--file", str(submission)], capture_output=True, text=True)
    return None if result.returncode == 0 else json.loads(result.stderr or result.stdout)


def drive(binary, authority, run_id, verdict):
    """Answer attempts until verify has been answered; return what was seen."""
    seen = []
    for _ in range(MAX_TURNS):
        refused = subprocess.run([str(binary), "--json", "--project", str(authority), "run", "drive", run_id], capture_output=True, text=True)
        if refused.returncode != 0:
            return seen, json.loads(refused.stderr or refused.stdout)
        tasks = verify.run(binary, "--project", authority, "session", "task", "--run", run_id, "--all")["tasks"]
        if not tasks:
            return seen, None
        for task in tasks:
            if verdict == "cancelled" and task["skill_refs"][0]["id"].endswith("/aif-verify-bridge"):
                # A host that went away while holding the gate: the owner cancels
                # and the Run has no outcome. The gate is read-only, so nothing is
                # left unsettled that `run resolve` would have to answer first.
                verify.run(binary, "--project", authority, "run", "cancel", run_id, "--reason", "run probe: the host went away")
                subprocess.run([str(binary), "--json", "--project", str(authority), "run", "drive", run_id], capture_output=True)
                seen.append({"bridge": "aif-verify-bridge", "routed_verdicts": task["routed_verdicts"], "result_schema": task["result_schema_ref"]["version"]})
                return seen, None
            bridge, step_verdict, values = answer(task, verdict)
            seen.append({"bridge": bridge, "routed_verdicts": task["routed_verdicts"], "result_schema": task["result_schema_ref"]["version"]})
            if step_verdict is None:
                return seen, None  # past verify: the gate has been answered
            refused = submit(binary, authority, run_id, task, step_verdict, values, bridge)
            if refused:
                return seen, {**refused, "at": f"session submit ({bridge})"}
    raise AssertionError(f"no end after {MAX_TURNS} turns: {seen}")


def continue_tail(binary, authority, repository, source_run):
    """Continue a finished classic Run into the tail and drive it past its verify gate."""
    node = subprocess.run([_which.which("node"), "-p", "process.execPath"], capture_output=True, text=True, check=True).stdout.strip()
    verify.run(binary, "--project", authority, "project", "local", "set", "--repository", repository, "--allow-executable", f"node={node}")
    arguments = ["--project", authority, "project", "continue", "--repository", repository, "--launch", "aif-classic-continuation",
                 "--source-run", source_run, "--host", "codex-cli", "--decision-policy", "autonomous", "--workspace", "worktree", "--allow-execution"]
    prepared = verify.run(binary, *arguments, "--prepare")
    started = verify.run(binary, *arguments, "--expected-launch-digest", prepared["review_digest"])
    run_id = started["run"]["run"]["id"]
    seen, refusal = drive(binary, authority, run_id, "pass")
    state = verify.run(binary, "--project", authority, "run", "status", run_id)["run"]
    resume = next((step for step in state["steps"].values() if step["definition_ref"]["id"].endswith(":step/resume")), None)
    accepted = resume and state["attempts"][resume["attempt_ids"][-1]].get("accepted") or {}
    return run_id, started, {
        "answered": [item["bridge"] for item in seen],
        "resume": resume and {"status": resume["status"], "verdict": accepted.get("verdict"), "summary": accepted.get("summary")},
        "run_status": state["status"],
        "run_outcome": state.get("outcome"),
        "refusal": refusal and {"at": refusal.get("at", "run drive"), "code": refusal.get("code"), "message": refusal.get("message")},
    }


def clean(binary, authority, run_ids):
    for run_id in run_ids:
        state = verify.run(binary, "--project", authority, "run", "status", run_id)["run"]
        if state["status"] not in ("completed", "failed", "cancelled"):
            verify.run(binary, "--project", authority, "run", "cancel", run_id, "--reason", "run probe finished")
            subprocess.run([str(binary), "--json", "--project", str(authority), "run", "drive", run_id], capture_output=True)
    # Since 0.13.56 a Run that did not succeed keeps its tree, and a
    # continuation takes it over, so every claim this fixture made is released.
    for claim in verify.run(binary, "--project", authority, "claim", "list")["claims"]:
        if claim["status"] == "active":
            subprocess.run([str(binary), "--json", "--project", str(authority), "claim", "release", "--id", claim["id"], "--generation", str(claim["generation"])], capture_output=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--verdict", choices=("blocked", "pass", "cancelled"), default="blocked")
    parser.add_argument("--tag")
    parser.add_argument("--keep", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--continue", dest="continue_tail", action="store_true")
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    root = Path(tempfile.mkdtemp(prefix="aif-run-probe-"))
    repository, authority, task = prepare(binary, root, args.tag)
    started = compatibility.start_launch(binary, authority, repository, task, "codex-cli", None)
    run_id = started["run"]["run"]["id"]
    run_ids = [run_id]
    try:
        seen, refusal = drive(binary, authority, run_id, args.verdict)
        state = verify.run(binary, "--project", authority, "run", "status", run_id)["run"]
        report = {
            "prifly": verify.run(binary, "version")["version"],
            "package": args.tag or "working tree",
            "verify_verdict": args.verdict,
            "answered": [item["bridge"] for item in seen],
            "verify_task": next(({"routed_verdicts": item["routed_verdicts"], "result_schema": item["result_schema"]} for item in seen if item["bridge"] == "aif-verify-bridge"), None),
            "run_status": state["status"],
            "run_outcome": state.get("outcome"),
            "refusal": refusal and {"at": refusal.get("at", "run drive"), "code": refusal.get("code"), "message": refusal.get("message"), "violations": refusal.get("violations")},
            "stand": str(root) if args.keep else None,
        }
        if args.continue_tail and refusal is None and state["status"] in ("completed", "cancelled"):
            tail_id, _, report["continuation"] = continue_tail(binary, authority, repository, run_id)
            run_ids.append(tail_id)
        print(json.dumps(report, indent=2))
        if args.check:
            assert refusal is None, f"refused: {report['refusal']}"
            assert "aif-verify-bridge" in report["answered"], report["answered"]
            if args.verdict == "cancelled":
                assert state["status"] == "cancelled", state["status"]
            elif args.verdict == "pass":
                # Past verify means the next gate was handed its attempt.
                assert report["answered"][-1] != "aif-verify-bridge", report["answered"]
            else:
                assert (state["status"], state.get("outcome")) == ("completed", "partial"), (state["status"], state.get("outcome"))
                # The developer is handed the gate that says what was down, not
                # an empty partial: the Run's own output is those bytes.
                submitted = "sha256:" + hashlib.sha256(json.dumps(GATE_BLOCKED).encode()).hexdigest()
                assert state["output_artifacts"]["gate"]["digest"] == submitted, state["output_artifacts"]
            if args.continue_tail:
                tail = report.get("continuation")
                assert tail and tail["refusal"] is None, tail
                # The tail's own program accepted the tree, and its verify gate
                # was answered and passed on to the next gate.
                assert (tail["resume"]["status"], tail["resume"]["verdict"]) == ("completed", "pass"), tail["resume"]
                assert "aif-verify-bridge" in tail["answered"] and tail["answered"][-1] != "aif-verify-bridge", tail["answered"]
    finally:
        if args.keep:
            print(f"kept: --project {authority} runs {' '.join(run_ids)}", file=sys.stderr)
        else:
            clean(binary, authority, run_ids)
            verify.forget_authority(authority)
            shutil.rmtree(root)


if __name__ == "__main__":
    main()
