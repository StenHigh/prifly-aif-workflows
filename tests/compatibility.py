#!/usr/bin/env python3
"""One authority carries Classic through every plan profile without losing what it already holds.

Unlike verify.py this fixture does import and start: each variant is sealed
into the same authority, trusted, and launched. It watches what a returning
owner would notice — an earlier Run rewritten, a tracked default silently
edited, or a variant quietly served under another variant's bytes.

No AI host answers here, so every Run is driven to the point where the first
assisted step is dispatched and waits, then cancelled. Everything past that
handoff needs a real host and is not claimed by this check.
"""

import argparse
import json
from pathlib import Path
import tempfile

from verify import HOSTS, git, prepare_repository, run

# A project owner's own extend.yaml: a setting the package did not default to,
# a declared feature switched off, and a step inserted into one exact route.
# Against a WorkflowRevision v4 package the insertion answers for every verdict
# too, exactly as the package's own stages do. Its
# profile is not the package's own default, so a launch that names none proves
# the owner's tracked choice is what applies.
TRACKED_PROFILE = "full"
EXTEND = "profile: " + TRACKED_PROFILE + """
settings:
  improve-batch: {improve_round_limit: 2}
exclude: [security]
extensions:
  - id: hold-after-commit
    workflow: classic
    step: continue-improve
    between: {from: commit, to: done}
    on: {pass: done, needs_revision: abandoned, fail: abandoned, no_work: abandoned}
"""
# An inserted stage is named by the step it inserts, not by the extension id.
EXTENSION_STAGE = "continue-improve"
# (package profile for this launch, host, host skill marker). The last launch
# restores the first one's host and skill bytes: the same inputs must be served
# as the same build, not as a fresh one that happens to look alike.
SEQUENCE = (
    ("fast", "codex-cli", "1"),
    ("full", "codex-app", "2"),
    ("ultra", "claude-code", "3"),
    (None, "codex-cli", "4"),
    ("fast", "codex-cli", "1"),
)
CLASSIC_SKILL = "aif-plan"


def write_host_skill(repository, host, marker):
    path = repository / HOSTS[host] / CLASSIC_SKILL / "SKILL.md"
    path.write_text(f"# {CLASSIC_SKILL}\nhost {host}, revision {marker}\n")


def launch_answers(binary, authority, repository, package_profile):
    """Answer exactly what the questionnaire says start will wait for."""
    arguments = ["--project", authority, "project", "questionnaire", "--repository", repository, "--package", "aif-classic"]
    if package_profile:
        arguments += ["--package-profile", package_profile]
    questionnaire = run(binary, *arguments)
    waiting = {state["id"] for state in questionnaire["decision_states"] if state.get("wait_reason") == "required_before_start"}
    answers = []
    for decision in questionnaire["preflight"]:
        if decision["id"] not in waiting:
            continue
        value = decision["choices"][0]["value"] if "choices" in decision else ""
        answers += ["--preflight-answer", f"{decision['id']}={json.dumps(value)}"]
    return answers, questionnaire["catalog_digest"]


def stop_at_handoff(binary, authority, run_id, workspace):
    """Nothing here answers an assisted step, so give the repository claim back."""
    state = run(binary, "--project", authority, "run", "status", run_id)["run"]
    assert state["status"] == "running" and state["active_attempt_ids"], state["status"]
    run(binary, "--project", authority, "run", "cancel", run_id, "--reason", "no AI host in this fixture")
    run(binary, "--project", authority, "run", "drive", run_id)
    stopped = run(binary, "--project", authority, "run", "status", run_id)["run"]
    assert stopped["status"] == "cancelled", stopped["status"]
    run(binary, "--project", authority, "claim", "release", "--id", workspace["id"], "--generation", workspace["generation"])


def check_customisation(documents):
    classic = documents["aif:workflow/classic"]["definition"]["stages"]
    assert classic["commit"]["on"]["pass"] == EXTENSION_STAGE, classic["commit"]
    assert classic[EXTENSION_STAGE]["on"]["pass"] == "done", classic[EXTENSION_STAGE]
    assert documents["aif:workflow/improve-batch"]["inputs"]["improve_round_limit"]["configuration"]["default"] == 2
    assert documents["aif:workflow/classic"]["inputs"]["security_enabled"]["configuration"]["default"] is False


def compile_and_import(binary, authority, repository, output, host, package_profile):
    arguments = ["--project", authority, "project", "compile", "--repository", repository, "--package", "aif-classic", "--host", host, "--output", output]
    if package_profile:
        arguments += ["--package-profile", package_profile]
    result = run(binary, *arguments)
    documents = {}
    for component in result["components"]:
        if component["kind"] == "workflow":
            documents[component["ref"]["id"]] = json.loads((output / component["path"]).read_text())
    check_customisation(documents)
    run(binary, "--project", authority, "package", "import", "--dir", output, "--reason", f"compatibility sequence {host}")
    return result


def start_launch(binary, authority, repository, task, host, package_profile):
    answers, catalog_digest = launch_answers(binary, authority, repository, package_profile)
    arguments = [
        "--project", authority, "project", "start", "--repository", repository, "--launch", "aif-classic",
        "--host", host, "--input", f"task={task}", "--workspace", "worktree",
        "--expected-decision-catalog-digest", catalog_digest, *answers,
    ]
    if package_profile:
        arguments += ["--package-profile", package_profile]
    return run(binary, *arguments)


def trusted_packages(binary, authority):
    listed = run(binary, "--project", authority, "package", "list")["packages"]
    return {entry["ref"]["version"]: (entry["ref"]["digest"], entry["status"]) for entry in listed}


def sealed_run(binary, authority, run_id):
    """What the authority still says this Run is bound to and how it ended."""
    state = run(binary, "--project", authority, "run", "status", run_id)["run"]
    return state["status"], state["workflow_ref"], state["package_lock_ref"], state["input_artifacts"]


def check_sequence(binary, authority, repository, root, task):
    tracked = {path: (repository / ".prifly" / path).read_bytes() for path in ("workflows/aif-classic/extend.yaml", "project.yaml")}
    builds, runs, imported = {}, {}, {}
    for index, (package_profile, host, marker) in enumerate(SEQUENCE):
        write_host_skill(repository, host, marker)
        compiled = compile_and_import(binary, authority, repository, root / f"seal-{index}", host, package_profile)
        started = start_launch(binary, authority, repository, task, host, package_profile)
        # An owner reads the author version; the exact build is what the
        # authority holds. Compile and start of one input must agree on both.
        assert started["author_package"] == compiled["author_package"], (started["author_package"], compiled["author_package"])
        assert started["package"] == compiled["package"] and started["build_key"] == compiled["build_key"], started["package"]
        assert started["package_profile"] == (package_profile or TRACKED_PROFILE), started["package_profile"]
        builds[index] = compiled["build_key"]
        run_id = started["run"]["run"]["id"]
        stop_at_handoff(binary, authority, run_id, started["workspace"])
        runs[run_id] = sealed_run(binary, authority, run_id)

        listed = trusted_packages(binary, authority)
        for version, entry in imported.items():
            assert listed.get(version) == entry, (version, listed.get(version), entry)
        imported = listed
        assert listed[compiled["package"]["version"]] == (compiled["package"]["digest"], "trusted"), listed[compiled["package"]["version"]]
        # A stopped Run is evidence; a later launch of another variant must
        # leave every byte of it where the earlier launch put it.
        for earlier, sealed in runs.items():
            assert sealed_run(binary, authority, earlier) == sealed, earlier
        for path, bytes_ in tracked.items():
            assert (repository / ".prifly" / path).read_bytes() == bytes_, f"a launch rewrote the tracked {path}"
    # Fast → Full → Ultra → default → Fast: the return is the same build again,
    # and the three variants in between stayed distinct.
    assert builds[4] == builds[0], (builds[4], builds[0])
    assert len(set(builds.values())) == len(SEQUENCE) - 1, builds
    return builds, imported


def main():
    if not __debug__:
        raise RuntimeError("Verification requires enabled Python assertions")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="prifly-aif-compat-") as temporary:
        root = Path(temporary)
        repository, authority = prepare_repository(binary, root)
        (repository / ".prifly" / "workflows" / "aif-classic" / "extend.yaml").write_text(EXTEND)
        git("-C", repository, "add", "-A")
        git("-C", repository, "commit", "-q", "-m", "compatibility fixture")
        task = root / "task.json"
        task.write_text(json.dumps({"title": "Compatibility sequence", "description": "Carry one authority across every declared plan profile."}))
        builds, imported = check_sequence(binary, authority, repository, root, task)
    version = run(binary, "version")
    print(json.dumps({
        "outcome": "passed",
        "prifly": version["version"],
        "launches": len(SEQUENCE),
        "distinct_builds": len(set(builds.values())),
        "trusted_packages": len(imported),
        "boundary": "assisted handoff dispatched; no AI host answers it here",
    }))


if __name__ == "__main__":
    main()
