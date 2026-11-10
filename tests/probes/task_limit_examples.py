#!/usr/bin/env python3
"""Admit the exact ready example files on released Core; no live AI actor."""
import argparse
import json
from pathlib import Path

from shipping_task_limit import Stand, PACKAGES, digest, write, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    examples = verify.ROOT / "examples/task-description-limit"
    report = {"prifly": verify.run(binary, "version")["version"],
              "binary_sha256": digest(binary.read_bytes()), "cases": [], "complete": False}
    try:
        for package in PACKAGES:
            s = Stand(binary, package)
            result = {"package": package}
            try:
                owner = s.folder / "project/compile-values.yaml"
                owner.parent.mkdir(parents=True, exist_ok=True)
                owner.write_bytes((examples / "compile-values.yaml").read_bytes())
                s.commit()
                file = examples / ("fix-task.json" if package == "aif-fix" else "task.json")
                expected = json.loads(file.read_text())
                assert len(expected["description"]) == 16557
                profile = "default" if package == "aif-fix" else "fast"
                prepared = s.prepare(file, profile)
                rid = s.start(file, profile, prepared)
                reference = s.state(rid)["run"]["input_artifacts"]["task"]
                write(s.root / "reference.json", reference)
                s.call("artifact", "export", "--ref", s.root / "reference.json", "--output", s.root / "task-export.json")
                assert json.loads((s.root / "task-export.json").read_text()) == expected
                result.update(input=str(file.relative_to(verify.ROOT)), input_sha256=digest(file.read_bytes()),
                              owner_sha256=digest(owner.read_bytes()), length=16557, run_id=rid,
                              prepare_passed=True, start_passed=True, full_saved_input=True,
                              boundary="Accepted root input and dispatched read-only warmup; no live skills or application acceptance.")
            finally:
                result["cleanup"] = s.close()
            report["cases"].append(result)
        report["complete"] = True
    finally:
        write(args.output, report)
    print(json.dumps({"complete": report["complete"], "cases": len(report["cases"])}))


if __name__ == "__main__":
    main()
