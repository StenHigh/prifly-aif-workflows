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
)


def build(binary, at):
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
    compatibility.stop_at_handoff(binary, authority, run_id, started["workspace"])
    (at / "stand.json").write_text(json.dumps({
        "run": run_id,
        "built_with": verify.run(binary, "version")["version"],
        "authority": str(authority),
    }, indent=2))
    print(json.dumps({"outcome": "built", "at": str(at), "run": run_id}))


def read(binary, authority, run_id, arguments):
    call = [str(binary), "--json", "--project", str(authority), *(part.format(run=run_id) for part in arguments)]
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


def compare(binaries, at):
    stand = json.loads((at / "stand.json").read_text())
    authority, run_id = Path(stand["authority"]), stand["run"]
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
    for label, arguments in READS:
        # Read the old binary twice first: whatever moves between those two
        # reads is a clock or an id, and comparing it across versions would
        # bury the change under noise. Nothing is masked by hand.
        reads = {binary: [read(binary, authority, run_id, arguments) for _ in range(2)]
                 for binary in (old, new)}
        paths = set()
        for pair in reads.values():
            try:
                paths |= volatile_paths(json.loads(pair[0]), json.loads(pair[1]))
            except Exception:
                pass
        paths = frozenset(paths)
        before = rendered(reads[old][1], paths)
        after = rendered(reads[new][1], paths)
        if before == after:
            print(f"  same      {label}   ({len(paths)} field(s) vary between reads)")
            continue
        print(f"  DIFFERS   {label}")
        for line in difflib.unified_diff(before, after, "old", "new", lineterm="", n=0):
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
                print("     ", line[:200])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "compare"))
    parser.add_argument("--binary", required=True, action="append", type=Path)
    parser.add_argument("--at", default=DEFAULT, type=Path)
    arguments = parser.parse_args()
    binaries = [binary.resolve(strict=True) for binary in arguments.binary]
    if arguments.mode == "build":
        build(binaries[0], arguments.at.resolve())
    else:
        assert len(binaries) == 2, "compare needs --binary twice: the old one and the candidate"
        compare(binaries, arguments.at.resolve())


if __name__ == "__main__":
    main()
