#!/usr/bin/env python3
"""Qualify the shipped task limit on released Core; real Git/CLI, scripted actors."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify
import run_check as host
import fix_check
from readability_compare import input_value, submit

PACKAGES = ("aif-classic", "aif-profiled", "aif-fix")
MAXIMUM = 9007199254740991


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def submit_plan(s, rid, task, location):
    template = s.call("session", "submit", "--template", "--run", rid, "--attempt", task["attempt_id"])
    template["result"].update(outputs={}, verdict="pass", summary="Synthetic plan at the declared chosen location")
    template["answered_questions"] = []
    template["workspace_trees"] = [{"output_port": "plan", "path": location}]
    if task.get("model_profile"):
        template["model_profile"] = {"outcome": "unavailable", "reason": "Scripted fixture; no model used."}
    file = Path(task["workspace"]) / "submission.json"
    write(file, template)
    s.call("session", "submit", "--file", file)


class Stand:
    def __init__(self, binary, package):
        self.binary, self.package = binary, package
        self.temporary = tempfile.TemporaryDirectory(prefix="shipping-task-limit-")
        self.root = Path(self.temporary.name)
        self.repo, self.authority = verify.prepare_repository(binary, self.root)
        self.registry_authority = self.authority
        self.folder = self.repo / ".prifly/workflows" / package
        profile = self.repo / ".prifly/project.yaml"
        profile.write_text(profile.read_text().replace("prifly-project-profile/3", "prifly-project-profile/5"))
        self.runs, self.calls, self.counter = [], [], 0
        self.saved = {}

    def call(self, *args):
        return verify.run(self.binary, "--project", self.authority, *args)

    def refused(self, *args, code=None):
        raw = verify.run(self.binary, "--project", self.authority, *args, expect_ok=False)
        problem = json.loads(raw.strip().splitlines()[-1])
        if code:
            assert problem["code"] == code, problem
        self.calls.append({"args": list(map(str, args)), "problem": problem})
        return problem

    def owner(self, value):
        file = self.folder / "project/compile-values.yaml"
        if value is None:
            file.unlink(missing_ok=True)
        else:
            write(file, {"authoring": "prifly-compile-values/1", "values": {"task_description_limit": value}})

    def taskfile(self, length):
        value = {"title": "Synthetic task limit acceptance", "description": "я" * (length - 1) + "😀"}
        file = self.root / f"task-{length}.json"
        write(file, value)
        return file, value

    def options(self, file, profile="fast"):
        options = ("--repository", self.repo, "--launch", self.package, "--host", "codex-cli",
                   "--input", f"task={file}", "--workspace", "worktree", "--package-profile", profile)
        if self.package == "aif-fix":
            return options + ("--preflight-answer", 'short_checks=""', "--preflight-answer",
                              'gate_warnings="ignore"', "--runtime-answer", "fix_plan_execution=true")
        answers = ("--decision-policy", "attended", "--preflight-answer", "plan_tests=true",
                          "--preflight-answer", 'gate_warnings="ignore"', "--preflight-answer",
                          'gate_checks="python3 -m unittest discover -s tests"', "--preflight-answer",
                          'plan_constraints=""', "--preflight-answer", 'roadmap_linkage="skip"')
        if profile in ("full", "ultra"):
            answers += ("--preflight-answer", 'plan_logging="standard"', "--preflight-answer", "plan_docs=false")
        return options + answers

    def snapshot(self):
        return {
            "files": {str(p.relative_to(self.repo)): digest(p.read_bytes())
                      for p in self.repo.rglob("*") if p.is_file() and ".git" not in p.relative_to(self.repo).parts},
            "runs": self.call("run", "list"), "claims": self.call("claim", "list"),
            "packages": self.call("package", "list"),
        }

    def prepare(self, file, profile="fast"):
        before = self.snapshot()
        result = self.call("project", "questionnaire", *self.options(file, profile), "--prepare")
        assert self.snapshot() == before, "prepare mutated project/state"
        return result

    def start(self, file, profile="fast", prepared=None):
        prepared = prepared or self.prepare(file, profile)
        started = self.call("project", "start", *self.options(file, profile),
                            "--expected-launch-digest", prepared["review_digest"])
        rid = started["run"]["run"]["id"]
        self.runs.append(rid)
        return rid

    def state(self, rid):
        view = self.call("run", "status", rid)
        # The response also contains current authority-wide read metadata.
        # Compare the persisted Run and its version, as the recovery probes do.
        return {key: view[key] for key in ("run_version", "run")}

    def stop(self, rid):
        state = self.state(rid)["run"]
        if state["status"] not in ("completed", "failed", "cancelled"):
            self.call("run", "cancel", rid, "--reason", "Synthetic limit acceptance boundary")
            self.call("run", "drive", rid)
        host.clean(self.binary, self.authority, [rid])

    def compile(self, limit, profile="fast", host_name="codex-cli"):
        self.counter += 1
        output = self.root / f"compiled-{self.counter}"
        compiled = self.call("project", "compile", "--repository", self.repo, "--package", self.package,
                             "--host", host_name, "--package-profile", profile, "--output", output)
        documents = {c["ref"]["id"]: json.loads((output / c["path"]).read_text())
                     for c in compiled["components"] if c["kind"] != "context"}
        schema = documents["aif:schema/task"]
        assert schema["properties"]["description"]["maxLength"] == limit, schema
        task_refs = [d["inputs"]["task"]["schema_ref"] for d in documents.values() if "task" in d.get("inputs", {})]
        assert len(task_refs) >= 3 and all(r == task_refs[0] for r in task_refs), task_refs
        assert task_refs[0]["id"] == "aif:schema/task", task_refs
        return {"build_key": compiled["build_key"], "package": compiled["package"],
                "profile": profile, "host": host_name, "limit": limit,
                "task_ref": task_refs[0], "consumer_count": len(task_refs)}

    def commit(self):
        verify.git("-C", self.repo, "add", "-A")
        verify.git("-C", self.repo, "commit", "--allow-empty", "-qm", "Configure task limit acceptance")

    def close(self):
        host.clean(self.binary, self.authority, self.runs)
        # Every worker here is this synchronous script, with only fixture-local
        # writes. A refused report can leave its completed writes uncertain.
        for rid in self.runs:
            for attempt_id, attempt in self.state(rid)["run"]["attempts"].items():
                if attempt["status"] == "uncertain":
                    self.call("run", "resolve", rid, "--attempt", attempt_id, "--outcome", "applied",
                              "--reason", "Synchronous synthetic actor returned; owned local writes inspected, no external effects.")
        host.clean(self.binary, self.authority, self.runs)
        assert not any(c["status"] == "active" for c in self.call("claim", "list")["claims"])
        removed = verify.forget_authority(self.registry_authority)
        assert removed == 1, removed
        self.temporary.cleanup()
        assert not self.root.exists()
        return {"active_claims": 0, "registry_entries_removed": removed, "root_removed": True}


def boundaries(binary, package):
    s = Stand(binary, package)
    result = {"package": package, "case": "boundaries", "builds": [], "refusals": s.calls}
    profile = "default" if package == "aif-fix" else "fast"
    try:
        s.commit()
        result["builds"].append(s.compile(12000, profile))
        for limit, accepted, refused in ((12000, (12000,), (12001, 16557)), (32000, (16557, 32000), (32001,))):
            s.owner(None if limit == 12000 else limit)
            s.commit()
            for length in accepted:
                file, _ = s.taskfile(length)
                rid = s.start(file, profile)
                assert s.state(rid)["run"]["status"] == "running"
                s.stop(rid)
                s.saved[rid] = s.state(rid)
            for length in refused:
                file, _ = s.taskfile(length)
                before = s.snapshot()
                for command, extra in (("questionnaire", ("--prepare",)), ("start", ())):
                    problem = s.refused("project", command, *s.options(file, profile), *extra, code="schema_invalid")
                    assert problem["violations"][0]["pointer"] == "/description", problem
                    assert str(length) in problem["message"] and str(limit) in problem["message"], problem
                assert s.snapshot() == before
        profiles = ("default", "custom") if package == "aif-fix" else ("fast", "full", "ultra")
        for selected in profiles:
            for host_name in verify.HOSTS:
                result["builds"].append(s.compile(32000, selected, host_name))
        file, _ = s.taskfile(16557)
        prepared = s.prepare(file, profile)
        s.owner(40000)
        current = s.prepare(file, profile)
        assert prepared["review_digest"] != current["review_digest"]
        before = s.snapshot()
        s.refused("project", "start", *s.options(file, profile), "--expected-launch-digest",
                  prepared["review_digest"], code="project_start_stale_launch")
        assert s.snapshot() == before
        for invalid in (0, -1, 1.5, "32000", True, None, MAXIMUM + 1, {}, []):
            # None here must be explicit null, rather than omission/default.
            write(s.folder / "project/compile-values.yaml", {
                "authoring": "prifly-compile-values/1", "values": {"task_description_limit": invalid}})
            before = s.snapshot()
            for command, extra in (("questionnaire", ("--prepare",)), ("start", ())):
                s.refused("project", command, *s.options(file, profile), *extra,
                          code="project_compile_parameter_invalid")
            assert s.snapshot() == before
        s.owner(32000)
        if package != "aif-fix":
            project_readers(s)
            step = s.folder / "project/steps/task-reader.yaml"
            step.write_text(step.read_text().replace("{{schema_task}}", "{{frozen_task}}"))
            extension = s.folder / "extend.yaml"
            data = json.loads(extension.read_text())
            data["references"] = {"frozen_task": "aif:schema/task@1.1.0"}
            write(extension, data)
            before = s.snapshot()
            problem = s.refused("project", "compile", "--repository", s.repo, "--package", package,
                                "--host", "codex-cli", "--package-profile", profile,
                                "--output", s.root / "incompatible-consumer")
            assert "binding" in problem["message"] or "schema" in problem["message"], problem
            assert s.snapshot() == before
            result["incompatible_consumer"] = problem
        for rid, original in s.saved.items():
            assert s.state(rid) == original, "new limit changed previous Run"
        result.update(accepted_starts=3, unicode_diagnostics=True, previous_runs_unchanged=True,
                      prepare_and_refusals_read_only=True, stale_review_refused=True)
        return result
    finally:
        result["cleanup"] = s.close()


def project_readers(s):
    point_file = json.loads((s.folder / "extension-points.yaml").read_text())
    write(s.folder / "project/contexts/task-reader.yaml", {
        "id": "task-limit:context/task-reader", "version": "1.0.0", "media_type": "text/plain",
        "text": "Read the full synthetic task; return the current implementation unchanged."})
    task_schema = {"schema_ref": "{{schema_task}}"}
    implementation = {"schema_ref": "{{contract_schema_implementation}}"}
    write(s.folder / "project/steps/task-reader.yaml", {
        "authoring": "prifly-step/2", "id": "task-limit:step/task-reader", "version": "1.0.0",
        "title": "Project-owned task consumer", "kind": "worker",
        "inputs": {"task": task_schema, "implementation": implementation},
        "outputs": {"implementation": {**implementation, "required_for": ["pass"]}},
        "executor": {"adapter_ref": "{{assisted_adapter}}", "operation": "session"},
        "instructions_ref": "{{context_task-reader}}", "effects": {"class": "none", "retry_class": "pure"},
        "result_schema_ref": "{{step_result_schema_v2}}"})
    extensions = [{"id": "task-" + point, "point": point, "step": "task-reader",
                   "output_bindings": {name: "implementation" for name in point_file["points"][point]["consumers"]}}
                  for point in ("before-verify", "before-review")]
    write(s.folder / "extend.yaml", {"authoring": "prifly-extension/5", "exclude": ["improve"], "extensions": extensions})


def route(binary, package, profile):
    s = Stand(binary, package)
    result = {"package": package, "case": "route", "profile": profile, "seen": [], "task_reads": 0}
    try:
        s.owner(32000)
        project_readers(s)
        s.commit()
        result["build"] = s.compile(32000, profile)
        file, expected = s.taskfile(16557)
        rid = s.start(file, profile)
        counts = {"verify": 0, "review": 0, "fix": 0}
        original = None
        resumed = False
        for _ in range(70):
            s.call("run", "drive", rid)
            tasks = s.call("session", "task", "--run", rid, "--all")["tasks"]
            if not tasks:
                state = s.state(rid)["run"]
                if not resumed:
                    assert state["outcome"] == "partial", state
                    original = s.state(rid)
                    s.owner(12000)
                    arguments = ("project", "continue", "--repository", s.repo, "--launch", package,
                                 "--source-run", rid, "--host", "codex-cli")
                    before = s.snapshot()
                    problem = s.refused(*arguments, "--prepare")
                    assert s.snapshot() == before
                    result["changed_limit_continue_refusal"] = problem
                    s.owner(32000)
                    before = s.snapshot()
                    prep = s.call(*arguments, "--prepare")
                    assert s.snapshot() == before
                    rid = s.call(*arguments, "--expected-launch-digest", prep["review_digest"])["run"]["run"]["id"]
                    s.runs.append(rid)
                    resumed = True
                    continue
                assert state["outcome"] == "succeeded", state
                assert s.state(s.runs[0]) == original
                assert counts == {"verify": 3, "review": 2, "fix": 2}, counts
                result.update(outcome=state["outcome"], runs=s.runs, counts=counts,
                              continued_with_original_limit=True, source_unchanged=True)
                return result
            for task in tasks:
                role = task["skill_refs"][0]["id"].rsplit("/", 1)[-1]
                result["seen"].append(role)
                if "task" in task["context"]["inputs"]:
                    assert input_value(task, "task") == expected, role
                    result["task_reads"] += 1
                if role == "task-reader":
                    verdict, values = "pass", {"implementation": input_value(task, "implementation")}
                elif role == "aif-plan-bridge":
                    tree = Path(task["repository_workspace"])
                    manifest = json.loads((Path(task["workspace"]) / "workspace-trees.json").read_text())
                    capture = manifest["ports"][0]["capture"]
                    path = tree / capture["path"]
                    if capture["kind"] == "direct_child_file":
                        path /= "task-limit.md"
                    elif capture["kind"] == "direct_child_tree":
                        path = path / "task-limit"
                    location = str(path.relative_to(tree))
                    if capture["kind"] == "direct_child_tree":
                        path /= capture["entrypoint"]
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("# Plan\n\n- [ ] Add hello.txt.\n")
                    submit_plan(s, rid, task, location)
                    continue
                elif role in ("aif-verify-bridge", "aif-review-bridge"):
                    gate = "verify" if role == "aif-verify-bridge" else "review"
                    counts[gate] += 1
                    blocked = gate == "verify" and counts[gate] == 1
                    repair = counts[gate] == (2 if gate == "verify" else 1)
                    value = {**host.GATE_PASSED, "gate": gate}
                    if blocked:
                        value = {**host.GATE_BLOCKED, "gate": gate}
                    elif repair:
                        value.update(status="failed", blocking=True, findings=["Synthetic repair"], suggested_next="/aif-fix")
                    verdict, values = "blocked" if blocked else "needs_revision" if repair else "pass", {"gate": value}
                elif role == "aif-fix-bridge":
                    tree = Path(task["repository_workspace"])
                    incoming = input_value(task, "implementation")
                    counts["fix"] += 1
                    (tree / "hello.txt").write_text(f"hello repair {counts['fix']}\n")
                    host.git_out(tree, "add", "hello.txt")
                    host.git_out(tree, "-c", "user.name=probe", "-c", "user.email=probe@example.invalid", "commit", "-qm", "Synthetic repair")
                    verdict, values = "pass", {"implementation": {**incoming, "head_commit": host.git_out(tree, "rev-parse", "HEAD")}}
                elif role == "aif-review-challenge-bridge":
                    incoming = input_value(task, "implementation")
                    verdict, values = "pass", {"challenge": {"base_commit": incoming["base_commit"],
                        "head_commit": incoming["head_commit"], "findings": [], "checked": ["Synthetic route"]}}
                elif role == "aif-commit-bridge":
                    verdict, values = "pass", {"implementation": input_value(task, "implementation")}
                else:
                    _, verdict, values = host.answer(task, "pass")
                    assert verdict is not None, role
                submit(binary, s.authority, rid, task, verdict, values)
        raise AssertionError("route turn limit")
    finally:
        result["cleanup"] = s.close()


def fix_route(binary):
    s = Stand(binary, "aif-fix")
    result = {"package": "aif-fix", "case": "repair-route", "task_reads": 0, "seen": []}
    actor = fix_check.Host(binary, s.authority, "repair-check", "default")
    try:
        s.owner(32000)
        (s.repo / "calc.py").write_text(fix_check.BAD)
        (s.repo / "tracked.txt").write_text("original\n")
        s.commit()
        file, expected = s.taskfile(16557)
        rid = s.start(file, "default")
        for _ in range(70):
            s.call("run", "drive", rid)
            tasks = s.call("session", "task", "--run", rid, "--all")["tasks"]
            if not tasks:
                state = s.state(rid)["run"]
                assert state["outcome"] == "succeeded", state
                assert result["seen"].count("check-change") == 2 and "repair" in result["seen"]
                result.update(outcome="succeeded", runs=s.runs)
                return result
            for task in tasks:
                role = task["skill_refs"][0]["id"].rsplit("/", 1)[-1].removesuffix("-bridge")
                result["seen"].append(role)
                actor.seen.append({"step": role, "run": rid})
                if "task" in task["context"]["inputs"]:
                    assert input_value(task, "task") == expected, role
                    result["task_reads"] += 1
                verdict, values = actor.answer(task, role)
                assert not actor.submit(rid, task, verdict, values)
        raise AssertionError("fix route turn limit")
    finally:
        result["cleanup"] = s.close()


def shared_authority(binary, package):
    first, second = Stand(binary, package), Stand(binary, package)
    result = {"case": "shared-authority", "package": package}
    profile = "default" if package == "aif-fix" else "fast"
    second.authority = first.authority
    try:
        first.call("capacity", "set", "--capacity", "2", "--reason", "Two owned synthetic projects")
        first.owner(32000)
        second.owner(40000)
        first.commit()
        second.commit()
        a, b = first.compile(32000, profile), second.compile(40000, profile)
        assert a["task_ref"] != b["task_ref"] and a["build_key"] != b["build_key"], (a, b)
        file, _ = first.taskfile(16557)
        rid = first.start(file, profile)
        original = first.state(rid)
        other, _ = second.taskfile(16557)
        other_rid = second.start(other, profile)
        first.owner(12000)
        first.compile(12000, profile)
        assert first.state(rid) == original, "other project/limit changed pinned Run"
        result.update(builds=[a, b], runs=[rid, other_rid], same_authority=True,
                      different_task_refs=True, previous_run_unchanged=True)
        return result
    finally:
        # Both stands own every Run in this shared disposable authority.
        for stand in (first, second):
            for rid in stand.runs:
                stand.stop(rid)
        result["cleanup"] = [second.close(), first.close()]


def update(binary, package):
    s = Stand(binary, package)
    result = {"case": "update", "package": package}
    selected = "default" if package == "aif-fix" else "fast"
    try:
        publisher = s.root / "publisher"
        publisher.mkdir()
        raw = subprocess.run(["git", "-C", str(verify.ROOT), "archive", "v1.57.0", package],
                             capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            archive.extractall(publisher, filter="data")
        verify.git("-C", publisher, "init", "-q", "-b", "main")

        def publish():
            verify.git("-C", publisher, "add", "-A")
            verify.git("-C", publisher, "commit", "-qm", "Publish fixture workflow")
            return host.git_out(publisher, "rev-parse", "HEAD")

        old = publish()
        s.call("project", "workflows", "remove", package, "--repository", s.repo)
        s.call("project", "workflows", "add", publisher.as_uri(), "--path", package, "--name", package,
               "--ref", old, "--repository", s.repo)
        extend = s.folder / "extend.yaml"
        owner_extend = extend.read_text() + "\n# Owner extension settings remain intact.\n"
        extend.write_text(owner_extend)
        sentinel = s.folder / "project/owner.txt"
        sentinel.parent.mkdir(parents=True)
        sentinel.write_text("Owner data must survive update.\n")
        shutil.rmtree(publisher / package)
        shutil.copytree(verify.ROOT / package, publisher / package)
        candidate = publish()
        s.call("project", "workflows", "update", package, "--ref", candidate, "--repository", s.repo)
        assert extend.read_text() == owner_extend and sentinel.read_text() == "Owner data must survive update.\n"
        s.owner(32000)
        original = (s.folder / "project/compile-values.yaml").read_bytes()
        s.compile(32000, selected)
        # A new source commit really changes package bytes; update must preserve
        # the already supported owner parameter as well as the migration files.
        readme = publisher / package / "README.md"
        readme.write_text(readme.read_text() + "\nSynthetic update acceptance marker.\n")
        workflow = publisher / package / "workflow.yaml"
        workflow.write_text(workflow.read_text().replace("version: 3.0.0", "version: 3.0.1"))
        refreshed = publish()
        s.call("project", "workflows", "update", package, "--ref", refreshed, "--repository", s.repo)
        assert (s.folder / "project/compile-values.yaml").read_bytes() == original
        assert extend.read_text() == owner_extend and sentinel.read_text() == "Owner data must survive update.\n"
        build = s.compile(32000, selected)
        file, _ = s.taskfile(16557)
        s.commit()
        rid = s.start(file, selected)
        s.stop(rid)
        result.update(source_commits=[old, candidate, refreshed], old_release="v1.57.0",
                      owner_values_preserved=True, extend_preserved=True, project_files_preserved=True,
                      long_task_start_accepted=True, build=build)
        return result
    finally:
        result["cleanup"] = s.close()


def main():
    if not __debug__:
        raise RuntimeError("Assertions must be enabled")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", choices=("boundaries", "route", "fix-route", "shared-authority", "update"))
    parser.add_argument("--package", choices=PACKAGES)
    parser.add_argument("--profile", choices=("fast", "full", "ultra"))
    parser.add_argument("--jobs", type=int, default=1)
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    report = {"prifly": verify.run(binary, "version")["version"], "binary_sha256": digest(binary.read_bytes()),
              "probe_sha256": digest(Path(__file__).read_bytes()),
              "package_sources": {package: {str(p.relative_to(verify.ROOT / package)): digest(p.read_bytes())
                                  for p in sorted((verify.ROOT / package).rglob("*")) if p.is_file()}
                                  for package in PACKAGES}, "cases": [], "complete": False}
    work = []
    try:
        if args.case in (None, "boundaries"):
            for package in (args.package,) if args.package else PACKAGES:
                work.append((boundaries, (binary, package)))
        if args.case in (None, "route"):
            for package in (args.package,) if args.package else PACKAGES[:2]:
                if package == "aif-fix":
                    continue
                for profile in (args.profile,) if args.profile else ("fast", "full", "ultra"):
                    work.append((route, (binary, package, profile)))
        if args.case in (None, "fix-route"):
            work.append((fix_route, (binary,)))
        for name, implementation in (("shared-authority", shared_authority), ("update", update)):
            if args.case in (None, name):
                for package in (args.package,) if args.package else PACKAGES:
                    work.append((implementation, (binary, package)))
        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            futures = [pool.submit(function, *arguments) for function, arguments in work]
            for future in as_completed(futures):
                result = future.result()
                report["cases"].append(result)
                write(args.output, report)
                print(json.dumps({key: result[key] for key in ("case", "package", "profile") if key in result}), flush=True)
        report["complete"] = True
    finally:
        write(args.output, report)
    print(json.dumps({"complete": report["complete"], "cases": len(report["cases"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
