"""W6 project native calls on unchanged classic or an explicit consumer; synthetic host."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [
    str(ROOT / "tests"),
    str(ROOT / "tests/probes"),
    str(ROOT / "examples/review-uiux-extensions"),
]
import verify
import install as overlay
from fix_check import Host
from run_check import git_out, clean, GATE_PASSED
from evidence_check import read
from test_review_evidence import report
from product_environment import OwnedEnvironment

BINARY = Path("/home/dev/.local/bin/prifly")
LIVE_SKILLS = None
ARTIFACTS = None

CASES = (
    "pass",
    "defect",
    "unavailable",
    "stale-report",
    "candidate-edit",
    "post-acceptance-edit",
    "cleanup-failure",
    "cancel",
    "resume",
    "commit-resume",
    "owner-stop",
    "missing-check",
    "prepare-drift",
)


def case(
    binary,
    mode="review",
    consumer="classic",
    scenario="pass",
    library=None,
    host="codex-cli",
):
    with tempfile.TemporaryDirectory(prefix="w6-run-") as tmp:
        root = Path(tmp)
        repository, authority = verify.prepare_repository(binary, root)
        runs = []
        environment = None
        live_sessions = []
        if LIVE_SKILLS:
            for host_root in verify.HOSTS.values():
                shutil.copyfile(
                    LIVE_SKILLS / "aif-review.md",
                    repository / host_root / "aif-review/SKILL.md",
                )
                shutil.copyfile(
                    LIVE_SKILLS / "severity.md",
                    repository / host_root / "aif-review/references/SEVERITY.md",
                )
        actor = Host(binary, authority, scenario, "default")
        actor.seen = []
        steps = []
        claims = set()
        reports = []
        captures = []
        commits = []

        def submit(rid, task, values, verdict="pass"):
            actor.seen.append({"step": steps[-1]})
            if not values and task["context"]["outputs"]:
                template = verify.run(
                    binary,
                    "--project",
                    authority,
                    "session",
                    "submit",
                    "--template",
                    "--run",
                    rid,
                    "--attempt",
                    task["attempt_id"],
                )
                template["result"].update(
                    verdict=verdict,
                    outputs={},
                    summary="Synthetic commit declined before any write",
                )
                template["answered_questions"] = []
                if task.get("model_profile"):
                    template["model_profile"] = {
                        "outcome": "unavailable",
                        "reason": "Synthetic fixture host",
                    }
                file = Path(task["workspace"]) / "submission.json"
                file.write_text(json.dumps(template))
                verify.run(
                    binary, "--project", authority, "session", "submit", "--file", file
                )
            else:
                problem = actor.submit(rid, task, verdict, values)
                assert not problem, problem

        try:
            package = "aif-classic" if consumer == "classic" else "w6-consumer"
            folder = repository / ".prifly/workflows" / package
            if consumer != "classic":
                shutil.copytree(
                    ROOT / "examples/review-uiux-extensions/consumer", folder
                )
                profile = overlay.load(
                    (repository / ".prifly/project.yaml").read_text()
                )
                profile["packages"][package] = {
                    "source": ".prifly/workflows/" + package
                }
                profile["launches"][package] = {
                    "title": "W6 explicit consumer",
                    "description": "Scoped native acceptance",
                    "kind": "workflow",
                    "workflow": ".prifly/workflows/" + package + "/workflow.yaml",
                }
                (repository / ".prifly/project.yaml").write_text(json.dumps(profile))
            else:
                (folder / "extend.yaml").write_text(
                    "profile: fast\nexclude: [improve]\nextensions: []\n"
                )
            baseline = {
                str(f.relative_to(folder)): f.read_bytes()
                for f in folder.rglob("*")
                if f.is_file() and f.name != "extend.yaml"
            }
            (repository / "index.html").write_bytes(
                (ROOT / "tests/fixtures/product/index.html").read_bytes()
            )
            (repository / "owner.txt").write_text("Preserve owner work\n")
            config = json.loads(
                (
                    ROOT
                    / "examples/review-uiux-extensions/configurations"
                    / f"{mode}.json"
                ).read_text()
            )

            if LIVE_SKILLS:
                for request in (
                    [config["review"]]
                    if mode == "review"
                    else [config["product"][lens] for lens in ("ui", "ux")]
                    + ([config["review"]] if mode == "combined" else [])
                ):
                    request["require_separate_session"] = True
            if scenario == "owner-stop":
                for request in (
                    [config["review"]]
                    if mode == "review"
                    else [config["product"][lens] for lens in ("ui", "ux")]
                ):
                    request["optional_policy"] = "stop"
            config_file = root / "settings.json"
            config_file.write_text(json.dumps(config))
            summary, changes = overlay.plan(
                repository,
                package,
                config_file,
                mode,
                "review" if consumer == "classic" else "write",
                "commit",
                "abandoned",
                "done",
                "implementation",
            )
            overlay.apply(repository, summary, changes)
            for name, raw in baseline.items():
                assert (folder / name).read_bytes() == raw, name
            verify.git("-C", repository, "add", ".")
            verify.git("-C", repository, "commit", "-qm", "W6 project fixture")
            base = git_out(repository, "rev-parse", "HEAD")
            task = root / "task.json"
            task.write_text(
                json.dumps(
                    {
                        "title": "Greeting feature",
                        "description": "Add greeting(name) returning Hello, <name>! and a unittest.",
                        **({"base_commit": base} if consumer != "classic" else {}),
                    }
                )
            )
            verify.run(
                binary,
                "--project",
                authority,
                "project",
                "local",
                "set",
                "--repository",
                repository,
                "--allow-executable",
                "python=" + str(Path(sys.executable).resolve()),
            )
            args = [
                "--project",
                authority,
                "project",
                "start",
                "--repository",
                repository,
                "--launch",
                package,
                "--host",
                host,
                "--workspace",
                "worktree",
                "--input",
                "task=" + str(task),
                "--allow-execution",
            ]
            if consumer == "classic":
                from compatibility import launch_answers

                answers, digest = launch_answers(binary, authority, repository, None)
                args += answers + ["--expected-decision-catalog-digest", digest]
            prepared = verify.run(
                binary, *args[:3], "questionnaire", *args[4:], "--prepare"
            )
            if scenario == "prepare-drift":
                sealed_settings = folder / "project/files/w6-settings.json"
                sealed_settings.write_bytes(sealed_settings.read_bytes() + b" ")
                refused = verify.run(
                    binary,
                    *args,
                    "--expected-launch-digest",
                    prepared["review_digest"],
                    expect_ok=False,
                )
                problem = json.loads(refused.strip().splitlines()[-1])
                assert problem["code"] == "project_start_stale_launch", problem
                assert not verify.run(binary, "--project", authority, "run", "list")[
                    "runs"
                ]
                return {
                    "scenario": scenario,
                    "mode": mode,
                    "consumer": consumer,
                    "refusal": problem["code"],
                    "runs": 0,
                    "cleaned": True,
                }
            begun = verify.run(
                binary, *args, "--expected-launch-digest", prepared["review_digest"]
            )
            rid = begun["run"]["run"]["id"]
            runs.append(rid)
            original_implementation = None
            tree = None
            cancelled = False
            for iteration in range(2 if scenario in ("resume", "commit-resume") else 1):
                for turn in range(60):
                    verify.run(binary, "--project", authority, "run", "drive", rid)
                    tasks = verify.run(
                        binary,
                        "--project",
                        authority,
                        "session",
                        "task",
                        "--run",
                        rid,
                        "--all",
                    )["tasks"]
                    if not tasks:
                        state = verify.run(
                            binary, "--project", authority, "run", "status", rid
                        )["run"]
                        assert state["status"] in (
                            "completed",
                            "failed",
                            "cancelled",
                        ), state
                        break
                    for delivered in tasks:
                        name = delivered["skill_refs"][0]["id"].rsplit("/", 1)[-1]
                        steps.append(name)

                        if delivered.get("repository_workspace"):
                            tree = Path(delivered["repository_workspace"])
                        if delivered.get("claim_id"):
                            claims.add(delivered["claim_id"])
                        if name in ("aif-warmup-bridge", "aif-plan-bridge"):
                            if name == "aif-warmup-bridge":
                                values = {
                                    "handoff": {
                                        "summary": "Greeting fixture",
                                        "entry_points": ["index.html"],
                                        "conventions": ["Python unittest"],
                                        "sources": ["git ls-files"],
                                    }
                                }
                            else:
                                (tree / ".ai-factory").mkdir(exist_ok=True)
                                (tree / ".ai-factory/PLAN.md").write_text(
                                    "# Plan\n\n- [ ] Add greeting function and unittest.\n"
                                )
                                values = {}
                            submit(rid, delivered, values)
                        elif name in ("aif-implement-bridge", "write"):
                            (tree / "greeting.py").write_text(
                                'def greeting(name):\n    return f"Hello, {name}!"\n'
                            )
                            (tree / "test_greeting.py").write_text(
                                'import unittest\nfrom greeting import greeting\nclass GreetingTest(unittest.TestCase):\n    def test_name(self): self.assertEqual(greeting("Ada"), "Hello, Ada!")\n'
                            )
                            original_implementation = {
                                "base_commit": base,
                                "head_commit": git_out(tree, "rev-parse", "HEAD"),
                                "changed_files": ["greeting.py", "test_greeting.py"],
                            }
                            submit(
                                rid,
                                delivered,
                                {"implementation": original_implementation},
                            )
                        elif name == "aif-review-challenge-bridge":
                            implementation = read(delivered, "implementation")
                            submit(
                                rid,
                                delivered,
                                {
                                    "challenge": {
                                        "base_commit": implementation["base_commit"],
                                        "head_commit": implementation["head_commit"],
                                        "findings": [],
                                        "checked": [
                                            "Synthetic native fixture: greeting function and unittest"
                                        ],
                                    }
                                },
                            )
                        elif name in (
                            "aif-verify-bridge",
                            "aif-security-bridge",
                            "aif-review-bridge",
                        ):
                            submit(
                                rid,
                                delivered,
                                {
                                    "gate": {
                                        **GATE_PASSED,
                                        "gate": (
                                            "security"
                                            if "security" in name
                                            else (
                                                "review"
                                                if "review" in name
                                                else "verify"
                                            )
                                        ),
                                    }
                                },
                            )
                        elif name == "w6-review-review-bridge":

                            if LIVE_SKILLS:
                                live_sessions.append(
                                    live_review(
                                        binary, authority, rid, delivered, ARTIFACTS
                                    )
                                )
                                reports.append(
                                    {
                                        "lens": "review",
                                        "candidate": read(delivered, "candidate")[
                                            "digest"
                                        ],
                                    }
                                )
                                continue
                            rq = read(delivered, "request")
                            basis = read(delivered, "candidate")
                            value = report(rq, basis)
                            value["request_digest"] = delivered["context"]["inputs"][
                                "request"
                            ]["ref"]["digest"]
                            captures.append(basis)
                            run = subprocess.run(
                                [
                                    sys.executable,
                                    "-B",
                                    "-m",
                                    "unittest",
                                    "test_greeting",
                                ],
                                cwd=tree,
                                capture_output=True,
                                text=True,
                            )
                            assert run.returncode == 0, run.stderr
                            value["checks"][0]["evidence"][0].update(
                                locator="python3 -B -m unittest test_greeting",
                                observation=run.stderr.strip(),
                            )
                            if scenario in ("unavailable", "resume") and iteration == 0:
                                value = report(rq, basis, "unavailable", "not_run")
                                value["request_digest"] = delivered["context"][
                                    "inputs"
                                ]["request"]["ref"]["digest"]
                            if scenario == "defect":
                                value["checks"][0].update(
                                    result="failed", reason="Injected review defect"
                                )
                            if scenario == "missing-check":
                                value["checks"] = []
                            if scenario == "stale-report":
                                value["request_digest"] = "sha256:" + "a" * 64
                            if scenario == "cancel":
                                verify.run(
                                    binary,
                                    "--project",
                                    authority,
                                    "run",
                                    "cancel",
                                    rid,
                                    "--reason",
                                    "Read-only W6 cancellation",
                                )
                                verify.run(
                                    binary, "--project", authority, "run", "drive", rid
                                )
                                cancelled = True
                                break
                            submit(rid, delivered, {"report": value})
                            reports.append(
                                {"lens": "review", "candidate": basis["digest"]}
                            )
                            if scenario == "candidate-edit":
                                (tree / "owner.txt").write_text(
                                    "Changed by external owner\n"
                                )
                        elif name.startswith("w6-product-"):
                            kind = name.removeprefix("w6-product-").removesuffix(
                                "-bridge"
                            )
                            cfg = read(delivered, "configuration")
                            basis = (
                                read(delivered, "candidate")
                                if kind != "release"
                                else None
                            )
                            if basis:
                                captures.append(basis)
                            if kind == "environment":
                                if scenario == "unavailable" or (
                                    scenario == "resume" and iteration == 0
                                ):
                                    receipt = {
                                        "status": "unavailable",
                                        "owner": cfg["environment"]["owner"],
                                        "profile": cfg["environment"]["profile"],
                                        "configuration_digest": delivered["context"][
                                            "inputs"
                                        ]["configuration"]["ref"]["digest"],
                                        "candidate_digest": basis["digest"],
                                        "session": None,
                                        "url": None,
                                        "reason": "Required fixture environment unavailable",
                                    }
                                else:
                                    environment = OwnedEnvironment(
                                        root / "environment-state",
                                        tree,
                                        cfg["environment"]["owner"],
                                        profile=cfg["environment"]["profile"],
                                    )
                                    environment.ensure()
                                    receipt = {
                                        "status": "ready",
                                        "owner": environment.owner,
                                        "profile": cfg["environment"]["profile"],
                                        "configuration_digest": delivered["context"][
                                            "inputs"
                                        ]["configuration"]["ref"]["digest"],
                                        "candidate_digest": basis["digest"],
                                        "session": environment.session,
                                        "url": environment.url,
                                        "reason": "",
                                    }
                                submit(rid, delivered, {"environment": receipt})
                            elif kind in ("ui", "ux"):
                                if LIVE_SKILLS and kind in ("ui", "ux"):
                                    import product_check

                                    product_check.AUTO_REVIEW = True
                                    live_sessions.append(
                                        product_check.live_reader(
                                            binary,
                                            authority,
                                            rid,
                                            delivered,
                                            library,
                                            ARTIFACTS,
                                            "w6",
                                            iteration,
                                        )
                                    )
                                    reports.append(
                                        {"lens": kind, "candidate": basis["digest"]}
                                    )
                                    continue
                                if scenario == "cancel" and kind == "ui":
                                    verify.run(
                                        binary,
                                        "--project",
                                        authority,
                                        "run",
                                        "cancel",
                                        rid,
                                        "--reason",
                                        "W6 cancelled after owned setup",
                                    )
                                    verify.run(
                                        binary,
                                        "--project",
                                        authority,
                                        "run",
                                        "drive",
                                        rid,
                                    )
                                    cancelled = True
                                    break
                                rq = read(delivered, "request")
                                env = read(delivered, "environment")
                                value = report(rq, basis)
                                value["request_digest"] = delivered["context"][
                                    "inputs"
                                ]["request"]["ref"]["digest"]
                                check = value["checks"][0]
                                check["id"] = rq["checks"][0]["id"]
                                if env["status"] != "ready":
                                    check.update(
                                        status="unavailable",
                                        result="not_run",
                                        reason=env["reason"],
                                        evidence=[],
                                    )
                                else:
                                    if library:
                                        taskfile = (
                                            Path(delivered["workspace"])
                                            / "browser-task.json"
                                        )
                                        taskfile.write_text(json.dumps(delivered))
                                        out = root / (kind + "-" + str(iteration))
                                        out.mkdir(exist_ok=True)
                                        result = subprocess.run(
                                            [
                                                "node",
                                                str(
                                                    ROOT
                                                    / "tests/probes/product_browser.cjs"
                                                ),
                                                str(library),
                                                str(taskfile),
                                                str(out),
                                            ],
                                            capture_output=True,
                                            text=True,
                                            timeout=90,
                                        )
                                        assert result.returncode == 0, result.stderr
                                        browser = json.loads(result.stdout)
                                        items = browser["observations"]
                                        tool = browser["tool"]
                                    else:
                                        items = [
                                            {
                                                "scenario": s["id"],
                                                "viewport": s["viewport"],
                                                "url": env["url"] + s["path"],
                                                "observations": "Synthetic declared scenario; no browser execution",
                                                "failures": [],
                                            }
                                            for s in cfg["scenarios"]
                                            if s["lens"] == kind
                                        ]
                                        tool = "synthetic browser declarations"
                                    failures = [
                                        f for item in items for f in item["failures"]
                                    ]
                                    check.update(
                                        result=(
                                            "failed"
                                            if failures or scenario == "defect"
                                            else "passed"
                                        ),
                                        reason="; ".join(failures)
                                        or (
                                            "Injected product defect"
                                            if scenario == "defect"
                                            else ""
                                        ),
                                        evidence=[
                                            {
                                                "method": "browser",
                                                "tool": tool,
                                                "locator": i["url"],
                                                "observation": json.dumps(
                                                    {
                                                        k: i[k]
                                                        for k in (
                                                            "scenario",
                                                            "viewport",
                                                            "url",
                                                            "observations",
                                                        )
                                                    }
                                                ),
                                                "exit_code": None,
                                            }
                                            for i in items
                                        ],
                                    )
                                if scenario == "stale-report":
                                    value["request_digest"] = "sha256:" + "a" * 64
                                submit(rid, delivered, {"report": value})
                                reports.append(
                                    {"lens": kind, "candidate": basis["digest"]}
                                )
                                if scenario == "candidate-edit" and kind == "ux":
                                    (tree / "owner.txt").write_text(
                                        "External owner changed candidate\n"
                                    )
                            elif kind == "release":
                                env = read(delivered, "environment")
                                status = "not_needed"
                                if environment:
                                    environment.close()
                                    status = "released"
                                receipt = {
                                    "status": status,
                                    "owner": env["owner"],
                                    "session": env["session"],
                                    "reason": "",
                                }
                                if scenario == "cleanup-failure":
                                    receipt.update(
                                        status="reconcile_required",
                                        reason="Injected cleanup reconciliation required",
                                    )
                                submit(rid, delivered, {"release": receipt})
                            else:
                                raise AssertionError(name)
                        elif name in ("aif-commit-bridge", "commit"):
                            if scenario == "commit-resume" and iteration == 0:
                                submit(rid, delivered, {}, "needs_revision")
                                continue
                            if scenario == "post-acceptance-edit":
                                (tree / "greeting.py").write_text(
                                    'def greeting(name):\n    return "Unreviewed"\n'
                                )
                            implementation = read(delivered, "implementation")
                            git_out(tree, "add", *implementation["changed_files"])
                            git_out(
                                tree,
                                "-c",
                                "user.name=fixture",
                                "-c",
                                "user.email=fixture@example.invalid",
                                "commit",
                                "-qm",
                                "Greeting feature",
                            )
                            implementation["head_commit"] = git_out(
                                tree, "rev-parse", "HEAD"
                            )
                            commits.append(implementation["head_commit"])
                            submit(rid, delivered, {"implementation": implementation})
                        else:
                            raise AssertionError(("Unexpected reader", name))
                    if cancelled:
                        state = verify.run(
                            binary, "--project", authority, "run", "status", rid
                        )["run"]
                        break
                else:
                    raise AssertionError("Too many native turns")
                if scenario in ("resume", "commit-resume") and iteration == 0:
                    assert state["outcome"] == "rejected" and not commits, state
                    if scenario == "resume":
                        (tree / "owner.txt").write_text(
                            "Owner edit before reviewed whole-child replay\n"
                        )
                    argv = [
                        "--project",
                        authority,
                        "project",
                        "continue",
                        "--repository",
                        repository,
                        "--launch",
                        package,
                        "--source-run",
                        rid,
                        "--host",
                        host,
                        "--allow-execution",
                    ]
                    prepared = verify.run(binary, *argv, "--prepare")
                    continued = verify.run(
                        binary,
                        *argv,
                        "--expected-launch-digest",
                        prepared["review_digest"],
                    )
                    rid = continued["run"]["run"]["id"]
                    runs.append(rid)
            evidence = collect_evidence(binary, authority, runs)
            expected = (
                "succeeded"
                if scenario in ("pass", "resume", "commit-resume")
                else None if scenario == "cancel" else "rejected"
            )

            if state.get("outcome") != expected:
                failure = root / "failed-state.json"
                failure.write_text(json.dumps(state))
                assessments = []
                for path in authority.rglob("*"):
                    if path.is_file() and path.stat().st_size < 100000:
                        try:
                            value = json.loads(path.read_bytes())
                            if (
                                isinstance(value, dict)
                                and value.get("protocol") == "w6-assessment/1"
                            ):
                                assessments.append(value)
                        except (ValueError, OSError):
                            pass
                raise AssertionError(
                    {
                        "scenario": scenario,
                        "expected": expected,
                        "actual": state.get("outcome"),
                        "assessments": assessments,
                        "steps": steps,
                        "diagnostics": state.get("diagnostics"),
                    }
                )
            if scenario in (
                "defect",
                "unavailable",
                "stale-report",
                "candidate-edit",
                "cleanup-failure",
                "owner-stop",
                "missing-check",
            ):
                assessments = evidence["assessments"]
                assert assessments, "Rejected without preserved diagnostic assessment"
                expected_gate = (
                    "failed"
                    if scenario == "defect"
                    else "warnings" if scenario == "owner-stop" else "blocked"
                )
                assert assessments[-1]["gate"]["status"] == expected_gate, assessments
            if expected == "succeeded":
                assert evidence["assessments"] and all(
                    a["fresh"] for a in evidence["assessments"]
                )
                assert len(commits) == 1 and reports
            elif scenario != "post-acceptance-edit":
                assert not commits
            if scenario == "resume":
                assert (
                    len({r["candidate"] for r in reports}) == 2
                ), "Continue reused stale candidate"
            assert len(claims) == 1, claims
            for name, raw in baseline.items():
                assert (folder / name).read_bytes() == raw, name
            return {
                "scenario": scenario,
                "mode": mode,
                "consumer": consumer,
                "host": host,
                "outcome": state.get("outcome"),
                "status": state["status"],
                "runs": len(runs),
                "claims": len(claims),
                "reports": reports,
                "evidence": evidence,
                "native_commits": len(commits),
                "actual_browser": bool(library) and mode != "review",
                "actual_llm_sessions": len(live_sessions),
                "live_sessions": live_sessions,
                "upstream_bytes_unchanged": True,
                "cleaned": True,
            }
        finally:
            if environment:
                environment.close()
            clean(binary, authority, runs)
            verify.forget_authority(authority)


def collect_evidence(binary, authority, runs):
    reports = {}
    assessments = []
    receipts = []
    for rid in runs:
        state = verify.run(binary, "--project", authority, "run", "status", rid)["run"]
        for attempt in state["attempts"].values():
            accepted = attempt.get("accepted") or {}
            for port, ref in accepted.get("outputs", {}).items():
                if port not in ("report", "assessment", "receipt"):
                    continue
                slot = attempt["context"]["outputs"][port]
                raw = (Path(attempt["workspace"]) / slot["path"]).read_bytes()
                assert ref["digest"] == "sha256:" + hashlib.sha256(raw).hexdigest()
                value = json.loads(raw)
                if port == "report":
                    reports[ref["artifact_id"]] = ref
                elif port == "assessment":
                    assessments.append(value)
                else:
                    receipts.append(value)
    for assessment in assessments:
        for port, ref in assessment["report_refs"].items():
            assert reports[ref["artifact_id"]] == ref, "Substituted original report ref"
            assert assessment["report_digests"][port] == ref["digest"]
    return {
        "original_report_refs": list(reports.values()),
        "assessments": assessments,
        "receipt_candidate_digests": [r["candidate"]["digest"] for r in receipts],
    }


def live_review(binary, authority, rid, task, artifacts):
    """One actual fresh reader; preserve its original bytes before native submission."""
    workspace = Path(task["workspace"])
    target = artifacts / "review"
    target.mkdir(parents=True, exist_ok=True)
    (workspace / "task.json").write_text(json.dumps(task, indent=2))
    template = verify.run(
        binary,
        "--project",
        authority,
        "session",
        "submit",
        "--template",
        "--run",
        rid,
        "--attempt",
        task["attempt_id"],
    )
    (workspace / "submission-template.json").write_text(json.dumps(template, indent=2))
    prompt = f"""Execute this single delivered read-only Pri-Fly review Attempt. Read {workspace}/task.json, all delivered skill/context references and typed inputs, and submission-template.json. Follow the sealed review bridge and pinned aif-review skill. Use only the delivered repository_workspace. Review the actual uncommitted candidate against every declared criterion; execute the declared command. No repair, Git commit, policy change, later-stage execution or Pri-Fly control calls.
Produce the exact W1 report schema in the allocated output file. Copy candidate unchanged and context.inputs.request.ref.digest. Set session according to this actual fresh session. Model profile is unavailable and model null unless the host supplies real attestation; never invent model independence. Report unavailable checks honestly. Use submission-template.json authority/identity fields unchanged, compute the actual SHA256 of report bytes and fill the report output digest. Put usable report findings in checks; use a native verdict appropriate to report delivery. Native model_profile is {{"outcome":"unavailable","reason":"No independent model attestation"}}, distinct from the typed report model_profile string. answered_questions is [] when none. Write complete submission.json in the task workspace, but do not submit it. Controller submits the exact file unchanged. No expected verdict is supplied.
Shell remains sandboxed. If bwrap prevents shell startup, request automatic approval review for the exact bounded fixture check using require_escalated; do not disable sandbox or access unrelated data. Finish with written file paths."""
    (target / "prompt.txt").write_text(prompt)
    shutil.copyfile(workspace / "task.json", target / "task.json")
    shutil.copytree(workspace / "inputs", target / "inputs", dirs_exist_ok=True)
    before = verify.run(binary, "--project", authority, "run", "status", rid)[
        "run_version"
    ]
    with (target / "events.jsonl").open("w") as out, (target / "stderr.txt").open(
        "w"
    ) as err:
        proc = subprocess.run(
            [
                "codex",
                "exec",
                "--ephemeral",
                "--json",
                "--approve-for-me",
                "-C",
                str(workspace),
                "--skip-git-repo-check",
                "-",
            ],
            input=prompt,
            text=True,
            stdout=out,
            stderr=err,
            timeout=480,
        )
    assert proc.returncode == 0, (target / "stderr.txt").read_text()[-2000:]
    assert (
        verify.run(binary, "--project", authority, "run", "status", rid)["run_version"]
        == before
    ), "Reader mutated native authority"
    file = workspace / "submission.json"
    value = json.loads(file.read_text())
    report_file = workspace / task["context"]["outputs"]["report"]["path"]
    raw = report_file.read_bytes()
    assert (
        value["result"]["outputs"]["report"]["digest"]
        == "sha256:" + hashlib.sha256(raw).hexdigest()
    )
    assert json.loads(raw)["session"] == "separate"
    sessions = [
        json.loads(line)["thread_id"]
        for line in (target / "events.jsonl").read_text().splitlines()
        if json.loads(line).get("type") == "thread.started"
    ]
    assert len(sessions) == 1
    shutil.copyfile(file, target / "submission.json")
    shutil.copyfile(report_file, target / "report.json")
    receipt = verify.run(
        binary, "--project", authority, "session", "submit", "--file", file
    )
    (target / "receipt.json").write_text(json.dumps(receipt, indent=2))
    return {
        "lens": "review",
        "session_id": sessions[0],
        "report_digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "model_attestation": "unavailable",
    }


def case_args(args):
    result = case(*args)
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("evidence", "live_sessions")}
        ),
        flush=True,
    )
    return result


def main():
    if not __debug__:
        raise RuntimeError("Qualification requires enabled assertions")
    global LIVE_SKILLS, ARTIFACTS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live-skills", type=Path)
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument(
        "--mode", choices=["review", "uiux", "combined"], default="combined"
    )
    parser.add_argument("--consumer", choices=["classic", "minimal"], default="classic")
    parser.add_argument("--case", choices=CASES, default="pass")
    parser.add_argument("--browser-library", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    LIVE_SKILLS = args.live_skills
    ARTIFACTS = args.artifacts
    if LIVE_SKILLS and (not ARTIFACTS or not args.browser_library or args.matrix):
        parser.error("Live requires artifacts, browser and a single scoped case")
    if args.matrix:
        from concurrent.futures import ProcessPoolExecutor

        specs = [
            (args.binary, m, c, "pass", args.browser_library, "codex-cli")
            for m in ("review", "uiux", "combined")
            for c in ("minimal", "classic")
        ]
        specs += [
            (args.binary, "review", "minimal", s, None, "codex-cli")
            for s in CASES
            if s not in ("pass", "cleanup-failure")
        ]
        specs += [
            (args.binary, "uiux", "classic", s, args.browser_library, "codex-cli")
            for s in (
                "defect",
                "unavailable",
                "stale-report",
                "candidate-edit",
                "cleanup-failure",
                "cancel",
                "resume",
                "commit-resume",
            )
        ]
        specs += [
            (args.binary, "combined", "minimal", "pass", None, h)
            for h in ("claude-code", "codex-app")
        ]
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            result = list(pool.map(case_args, specs))
    else:
        result = case(
            args.binary, args.mode, args.consumer, args.case, args.browser_library
        )
    if args.report:
        args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {"outcome": "passed", "cases": len(result)}
            if args.matrix
            else {
                k: v
                for k, v in result.items()
                if k not in ("evidence", "live_sessions")
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
