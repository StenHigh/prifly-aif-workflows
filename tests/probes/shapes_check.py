#!/usr/bin/env python3
"""Capture shapes no product package carries: two captures on one step, a
captured port that is the only output, and the same step handed out twice."""
import argparse, json, shutil, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compatibility, verify

PACKAGE = Path(__file__).resolve().parent / "capture-probe"

def call(binary, authority, *arguments, ok=True):
    done = subprocess.run([str(binary), "--json", "--project", str(authority), *map(str, arguments)],
                          capture_output=True, text=True, timeout=180)
    body = (done.stdout or done.stderr).strip().splitlines()
    try:
        document = json.loads(body[-1])
    except Exception:
        document = {}
    if ok:
        assert done.returncode == 0, f"{arguments}: {done.stderr[:400]}"
    return done.returncode, document

def envelope(authority):
    session = next(p for p in (authority / ".prifly/work").iterdir() if p.is_dir() and p.name != "claims")
    context = json.loads((session / "context.json").read_text())
    memo = session / "workspace-trees.json"
    return context, (json.loads(memo.read_text()) if memo.exists() else None)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--work", default="shapes", type=Path)
    parser.add_argument("--entry", default="only")
    arguments = parser.parse_args()
    binary = arguments.binary.resolve(strict=True)
    root = arguments.work.resolve()
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    repository, authority = verify.prepare_repository(binary, root)
    shutil.copytree(PACKAGE, repository / ".prifly" / "workflows" / "capture-probe")
    manifest = repository / ".prifly" / "workflows" / "capture-probe" / "workflow.yaml"
    if arguments.entry != "only":
        text = manifest.read_text().replace("entry: only", f"entry: {arguments.entry}")
        text = text.replace("""  only:
    kind: step
    step_ref: step_only
    on: {pass: two, needs_revision: stopped, fail: stopped, no_work: stopped}
""", "").replace('  step_only: "{{step_only-capture}}"\n', "")
        manifest.write_text(text)
    project = repository / ".prifly" / "project.yaml"
    text = project.read_text()
    text = text.replace("packages:\n", "packages:\n  capture-probe:\n    source: .prifly/workflows/capture-probe\n", 1)
    text = text.replace("launches:\n", "launches:\n  capture-probe:\n    title: Capture shape probe\n    description: Shapes no product package carries.\n    kind: workflow\n    workflow: .prifly/workflows/capture-probe/workflow.yaml\n", 1)
    project.write_text(text)
    compatibility.git("-C", repository, "add", "-A")
    compatibility.git("-C", repository, "commit", "-q", "-m", "capture shapes")

    output = root / "sealed"
    call(binary, authority, "project", "compile", "--repository", repository, "--package", "capture-probe",
         "--host", "codex-cli", "--output", output)
    call(binary, authority, "package", "import", "--dir", output, "--reason", "capture shapes")
    started = verify.run(binary, "--project", authority, "project", "start", "--repository", repository,
                         "--launch", "capture-probe", "--host", "codex-cli", "--workspace", "worktree")
    run_id = started["run"]["run"]["id"]
    print(f"prifly {verify.run(binary, 'version')['version']}   entry stage: {arguments.entry}")
    context, memo = envelope(authority)
    print("  context.json outputs :", json.dumps(context["outputs"]))
    print("  memo ports           :", [p["output_port"] for p in memo["ports"]] if memo else "<absent>")

    rc, document = call(binary, authority, "run", "pause", run_id, "--reason", "shapes: park it", ok=False)
    print("\nre-issue after park:")
    print(f"  pause  rc={rc} {document.get('code') or 'ok'}")
    if rc:
        return
    after = verify.run(binary, "--project", authority, "run", "status", run_id)
    for stop in after["run"].get("stops") or []:
        call(binary, authority, "run", "release", run_id, "--expected-epoch", after["run"]["control_epoch"],
             "--stop", f'{stop["id"]}:{stop["generation"]}', "--reason", "shapes: release the park", ok=False)
    after = verify.run(binary, "--project", authority, "run", "status", run_id)
    rc, document = call(binary, authority, "run", "resume", run_id, "--expected-version", after["run_version"],
                        "--reason", "shapes: resume", ok=False)
    print(f"  resume rc={rc} {document.get('code') or 'ok'}")
    if rc:
        return
    call(binary, authority, "run", "drive", run_id, ok=False)
    again, memo_again = envelope(authority)
    print("  outputs after re-issue :", json.dumps(again["outputs"]))
    print("  memo after re-issue    :", [p["output_port"] for p in memo_again["ports"]] if memo_again else "<absent>")
    print("  envelope unchanged     :", again == context and memo_again == memo)

if __name__ == "__main__":
    main()
