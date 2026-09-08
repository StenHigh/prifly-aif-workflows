#!/usr/bin/env python3
"""Does the executor's envelope agree with itself about a captured port?

One Run per capture kind plus one with no capture. Reports what `context.json`
and the memo each say about the captured port, and whether ordinary ports moved
— only the second can lose a Run's result rather than raise a refusal.
"""
import argparse, json, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compatibility, verify

CAPTURE = """outputs:
  plan: {schema_ref: "{{workspace_tree_manifest}}", required_for: [pass]}
  handoff:"""

def stand(binary, base, name, with_capture, profile):
    root = (base / name).resolve()
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    repository, authority = verify.prepare_repository(binary, root)
    warmup = repository / ".prifly" / "workflows" / "aif-classic" / "steps" / "warmup.yaml"
    if with_capture:
        text = warmup.read_text()
        text = text.replace("effects: {class: none, retry_class: never}", "effects: {class: workspace_write, retry_class: never}")
        text = text.replace("outputs:\n  handoff:", CAPTURE)
        text = text.replace('result_schema_ref: "{{step_result_schema}}"\n',
                            'result_schema_ref: "{{step_result_schema}}"\nworkspace_trees:\n  - output_port: plan\n    capture: "{{plan_capture}}"\n')
        warmup.write_text(text)
    compatibility.git("-C", repository, "add", "-A")
    compatibility.git("-C", repository, "commit", "-q", "-m", "capture check")
    task = root / "task.json"
    task.write_text(json.dumps({"title": "Capture check", "description": "What the envelope says about a captured port."}))
    output = root / "sealed"
    _, documents = verify.compile_package(binary, authority, repository, "aif-classic", output, profile=profile)
    verify.run(binary, "--project", authority, "package", "import", "--dir", output, "--reason", "capture check")
    compatibility.start_launch(binary, authority, repository, task, "codex-cli", profile)
    session = next(p for p in (authority / ".prifly/work").iterdir() if p.is_dir() and p.name != "claims")
    context = json.loads((session / "context.json").read_text())
    memo = session / "workspace-trees.json"
    return documents, context, (json.loads(memo.read_text()) if memo.exists() else None)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--work", default="capture-check", type=Path)
    arguments = parser.parse_args()
    binary = arguments.binary.resolve(strict=True)
    base = arguments.work.resolve()
    shutil.rmtree(base, ignore_errors=True)
    print(f"prifly {verify.run(binary, 'version')['version']}")
    ordinary = {}
    for name, with_capture, profile in (("nocapture", False, None), ("fast", True, "fast"), ("full", True, "full"), ("ultra", True, "ultra")):
        documents, context, memo = stand(binary, base, name, with_capture, profile)
        outputs = context["outputs"]
        declared = documents["aif:step/warmup"].get("workspace_trees")
        ordinary[name] = {port: value["path"] for port, value in outputs.items() if port != "plan"}
        print(f"\n{name}:")
        print(f"  context.json outputs      : {sorted(outputs)}")
        print(f"  captured port in outputs  : {'plan' in outputs}")
        print(f"  memo                      : {'absent' if memo is None else memo['ports'][0]['capture']}")
        print(f"  declared in compiled step : {declared[0]['capture'] if declared else '<none>'}")
        if memo and declared:
            print(f"  memo matches the step     : {memo['ports'][0]['capture'] == declared[0]['capture']}")
        print(f"  memo keys                 : {sorted(memo['ports'][0]) if memo else '-'}")
        print(f"  ordinary ports            : {ordinary[name]}")
    print(f"\nordinary ports identical across all four stands: {all(v == ordinary['nocapture'] for v in ordinary.values())}")

if __name__ == "__main__":
    main()
