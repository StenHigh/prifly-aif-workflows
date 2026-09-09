#!/usr/bin/env python3
"""A stand that outlives the session, so two binaries can read the same Run.

A change to what a command *prints* is cheapest to check by reading finished
data twice — once with the old binary, once with the candidate. A fresh Run
would differ in its data as well as in its reading, and the difference would
have to be explained; frozen data makes every difference the change itself.

    frozen_stand.py build   --binary /path/to/prifly [--at DIR]
    frozen_stand.py compare --binary /path/old --binary /path/new [--at DIR]
"""
import argparse, difflib, json, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compatibility, verify

DEFAULT = Path.home() / ".prifly-stands" / "aif-classic"
# Read-only commands whose output a candidate may change. `run status` carries
# the timing tree, which is where the engine's reading changes land.
READS = (
    # First on purpose: two different binaries must differ here, so a report
    # whose every other line says "same" still shows the comparison can see a
    # difference at all. A run where even this says "same" is not evidence.
    ("version", ("version",)),
    ("run status", ("run", "status", "{run}")),
    ("run explain", ("run", "explain", "{run}")),
    ("run timing", ("run", "timing", "{run}")),
    ("run events", ("run", "events", "{run}")),
    ("package list", ("package", "list")),
    # Refusals are what the last several releases actually changed, and nothing
    # here compared them: every read above succeeds. These three refuse for a
    # different reason each, and all three only read — a command that could
    # succeed would mutate the stand it is meant to keep frozen.
    ("refusal: unknown run", ("run", "status", "run:0000000000000000000000000000000000000000000000000000000000000000")),
    ("refusal: unknown component", ("package", "inspect", "--component", "aif:step/nothing-here")),
    ("refusal: unknown package version", ("package", "inspect", "--component", "aif:step/warmup", "--package", "aif:package/classic@9.9.9")),
)
# Only a live stand can hold the admission slot, and only an assisted step
# leaves an attempt open without a driver holding the lock — which is why this
# probe lives here and not in the engine's own stands. It could succeed if the
# slot were free, so the fingerprint below is what makes it admissible.
# There is no capacity probe here, and the reason is worth keeping. A second
# `project start` on a full authority does reach `capacity_conflict` — but the
# refusal is not a no-op: the Run is created and queued, and `capacity show`
# lists one more entry under `waiting` every time. Measured: 10 waiting before,
# 11 after, the new id named. So the probe grows the stand it is supposed to
# freeze, and the fingerprint below is what caught it. `capacity_conflict` and
# `active_stop` stay outside what a frozen stand can compare until the engine
# offers a read-only way to ask whether a start would be admitted.
LIVE_READS = ()
# What each refusal probe is aimed at. A probe that reaches a different refusal
# compares that one instead, under the name of the one it claims — and says
# "same" for as long as the wrong refusal stays put. Building the capacity probe
# cost three attempts for exactly this reason: it reached the questionnaire, then
# the missing input, and only then the admission boundary. Checked against the
# old binary, so a code that moves in the candidate still shows up as a
# difference rather than an error.
EXPECTED_REFUSALS = {
    "refusal: unknown run": "not_found",
    "refusal: unknown component": "package_component_not_found",
    "refusal: unknown package version": "package_not_installed",
}


def build(binary, at, live=False):
    shutil.rmtree(at, ignore_errors=True)
    at.mkdir(parents=True)
    repository, authority = verify.prepare_repository(binary, at)
    compatibility.git("-C", repository, "add", "-A")
    compatibility.git("-C", repository, "commit", "-q", "-m", "frozen stand")
    task = at / "task.json"
    task.write_text(json.dumps({"title": "Frozen stand", "description": "A settled Run kept for re-reading."}))
    output = at / "sealed"
    verify.compile_package(binary, authority, repository, "aif-classic", output)
    verify.run(binary, "--project", authority, "package", "import", "--dir", output, "--reason", "frozen stand")
    started = compatibility.start_launch(binary, authority, repository, task, "codex-cli", None)
    run_id = started["run"]["run"]["id"]
    if not live:
        compatibility.stop_at_handoff(binary, authority, run_id, started["workspace"])
    answers, digest = compatibility.launch_answers(binary, authority, repository, None)
    start_again = ["project", "start", "--repository", str(repository), "--launch", "aif-classic",
                   "--host", "codex-cli", "--workspace", "worktree", "--input", f"task={task}",
                   "--expected-decision-catalog-digest", digest, *[str(part) for part in answers]]
    (at / "stand.json").write_text(json.dumps({
        "start_again": start_again,
        "run": run_id,
        "mode": "live" if live else "settled",
        "repository": str(repository),
        "built_with": verify.run(binary, "version")["version"],
        "authority": str(authority),
    }, indent=2))
    print(json.dumps({"outcome": "built", "at": str(at), "run": run_id}))


def read(binary, authority, run_id, arguments, repository=""):
    call = [str(binary), "--json", "--project", str(authority),
            *(part.format(run=run_id, repository=repository) for part in arguments)]
    done = subprocess.run(call, capture_output=True, text=True, timeout=120)
    return (done.stdout or done.stderr).strip()


def volatile_paths(document, other, prefix=()):
    """Where two reads of the same binary disagree — clocks, ids, nothing else."""
    if isinstance(document, dict) and isinstance(other, dict) and set(document) == set(other):
        found = set()
        for key in document:
            found |= volatile_paths(document[key], other[key], prefix + (key,))
        return found
    if isinstance(document, list) and isinstance(other, list) and len(document) == len(other):
        found = set()
        for index, (left, right) in enumerate(zip(document, other)):
            found |= volatile_paths(left, right, prefix + (index,))
        return found
    return set() if document == other else {prefix}


def mask(document, paths, prefix=()):
    if prefix in paths:
        return "<varies between reads>"
    if isinstance(document, dict):
        return {key: mask(value, paths, prefix + (key,)) for key, value in document.items()}
    if isinstance(document, list):
        return [mask(value, paths, prefix + (index,)) for index, value in enumerate(document)]
    return document


def rendered(text, paths=frozenset()):
    try:
        return json.dumps(mask(json.loads(text), paths), indent=1, sort_keys=True).splitlines()
    except Exception:
        return text.splitlines()


def fingerprint(binary, authority, run_id, live=False):
    """What must not move: the Run, not the authority.

    The authority records a receipt even for a refusal, so its cut advances by
    design; a guard on the store would cry every run and be switched off within
    a week. The subject of "nothing changed" is the Run.
    """
    state = json.loads(read(binary, authority, run_id, ("run", "status", "{run}")))
    run = state["run"]
    return {
        "run_version": state["run_version"],
        "status": run["status"],
        "outcome": run.get("outcome"),
        "attempts": len(run.get("attempts") or {}),
        "stops": len(run.get("stops") or []),
        "control_epoch": run["control_epoch"],
        # A probe that could start a second Run would show up here before it
        # showed up anywhere else: the slot is held by whoever was admitted.
        "capacity": json.loads(read(binary, authority, run_id, ("capacity", "show"))) if live else None,
    }


def compare(binaries, at):
    stand = json.loads((at / "stand.json").read_text())
    authority, run_id = Path(stand["authority"]), stand["run"]
    live = stand.get("mode") == "live"
    repository = stand.get("repository", "")
    old, new = binaries
    versions = [json.loads(read(binary, authority, run_id, ("version",)))["version"] for binary in (old, new)]
    # A stand written by a newer binary can carry state neither of these two
    # knows how to read, and the difference would then be about the stand
    # rather than about the release. Rebuild it instead of reasoning about it.
    def ordered(text):
        return tuple(int(part) for part in text.split("-")[0].split(".") if part.isdigit())
    built = ordered(stand["built_with"])
    assert all(built <= ordered(version) for version in versions), (
        f"the stand was built with {stand['built_with']}, newer than {min(versions, key=ordered)}: "
        "rebuild it with the oldest binary you mean to compare")
    print(f"stand built with {stand['built_with']}, run {run_id}")
    print(f"  reading it with {versions[0]} and {versions[1]}")
    # The comparison cannot show a difference between two copies of one binary,
    # and a run that reports "same" everywhere would look identical either way.
    # Say so before the results rather than after.
    assert versions[0] != versions[1], (
        f"both binaries report {versions[0]}: this compares a binary with itself and can only say 'same'")
    # The fingerprint proves the reads did not damage the stand. It does not
    # prove the stand is still the stand: the engine session lost the Run of
    # theirs between sessions, every probe answered `not_found` under both
    # binaries, and eleven lines read as "same". Ask first whether the Run is
    # still there, and refuse rather than compare an empty authority.
    state = json.loads(read(old, authority, run_id, ("run", "status", "{run}")))
    assert not state.get("code"), (
        f"the stand no longer holds {run_id} ({state.get('code')}): rebuild it before comparing")
    before_run = fingerprint(old, authority, run_id, live)
    compared = differed = 0
    for label, arguments in READS + (LIVE_READS if live else ()):
        arguments = arguments or tuple(stand["start_again"])
        # Read the old binary twice first: whatever moves between those two
        # reads is a clock or an id, and comparing it across versions would
        # bury the change under noise. Nothing is masked by hand.
        reads = {binary: [read(binary, authority, run_id, arguments, repository) for _ in range(2)]
                 for binary in (old, new)}
        paths = set()
        for pair in reads.values():
            try:
                paths |= volatile_paths(json.loads(pair[0]), json.loads(pair[1]))
            except Exception:
                pass
        paths = frozenset(paths)
        expected = EXPECTED_REFUSALS.get(label)
        if expected:
            try:
                seen = json.loads(reads[old][1]).get("code")
            except Exception:
                seen = None
            assert seen == expected, f"{label} reaches {seen}, not {expected}: it is comparing the wrong refusal"
        before = rendered(reads[old][1], paths)
        after = rendered(reads[new][1], paths)
        compared += 1
        if before == after:
            print(f"  same      {label}   ({len(paths)} field(s) vary between reads)")
            continue
        # A field that varies only sometimes escapes a mask sampled twice, and
        # the escape looks exactly like a real difference. Ask again before
        # reporting: noise rarely repeats, a change always does. Measured on the
        # live stand, where the varying-field count itself moves between runs
        # (44, 56, 44) and one comparison reported a difference three others
        # did not.
        again = {binary: [read(binary, authority, run_id, arguments, repository) for _ in range(2)]
                 for binary in (old, new)}
        for pair in again.values():
            try:
                paths |= volatile_paths(json.loads(pair[0]), json.loads(pair[1]))
            except Exception:
                pass
        before, after = rendered(again[old][1], paths), rendered(again[new][1], paths)
        if before == after:
            print(f"  same      {label}   (a first reading differed and did not repeat; {len(paths)} field(s) vary)")
            continue
        differed += 1
        print(f"  DIFFERS   {label}")
        for line in difflib.unified_diff(before, after, "old", "new", lineterm="", n=0):
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
                print("     ", line[:200])


    # Read-only is a claim until it is measured: the engine session found four
    # of their eight probes could have written to the stand had a release moved
    # a check. Ours refuse on paths that cannot succeed — this says so after the
    # fact instead of trusting the choice.
    # The denominator beside the result: "nothing differed" and "nothing was
    # read" look the same in a report that only prints differences.
    print(f"  {differed} of {compared} reads differed")
    after_run = fingerprint(old, authority, run_id, live)
    assert after_run == before_run, f"the stand moved while being read: {before_run} → {after_run}"
    print(f"  stand unchanged: {json.dumps(after_run)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "compare"))
    parser.add_argument("--binary", required=True, action="append", type=Path)
    parser.add_argument("--at", default=DEFAULT, type=Path)
    parser.add_argument("--live", action="store_true", help="leave the Run open, holding its admission slot")
    arguments = parser.parse_args()
    binaries = [binary.resolve(strict=True) for binary in arguments.binary]
    if arguments.mode == "build":
        build(binaries[0], arguments.at.resolve(), arguments.live)
    else:
        assert len(binaries) == 2, "compare needs --binary twice: the old one and the candidate"
        compare(binaries, arguments.at.resolve())


if __name__ == "__main__":
    main()
