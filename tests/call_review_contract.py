#!/usr/bin/env python3
"""W6 exact local closure and typed extension compilation on all supported hosts."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

import verify

sys.path.insert(0, str(verify.ROOT / "examples/review-uiux-extensions"))
import install


def check(binary):
    results = []
    refusals = []
    for consumer in ("classic", "minimal"):
        for mode in ("review", "uiux", "combined"):
            with tempfile.TemporaryDirectory(prefix="w6-contract-") as temporary:
                root = Path(temporary)
                repo, authority = verify.prepare_repository(binary, root)
                try:
                    package = "aif-classic" if consumer == "classic" else "w6-consumer"
                    folder = repo / ".prifly/workflows" / package
                    if consumer == "minimal":
                        shutil.copytree(install.HERE / "consumer", folder)
                        profile_path = repo / ".prifly/project.yaml"
                        profile = install.load(profile_path.read_text())
                        profile["packages"][package] = {
                            "source": ".prifly/workflows/" + package
                        }
                        profile_path.write_text(json.dumps(profile))
                    originals = {
                        p.relative_to(folder): p.read_bytes()
                        for p in folder.rglob("*")
                        if p.is_file() and p.name != "extend.yaml"
                    }
                    summary, changes = install.plan(
                        repo,
                        package,
                        install.HERE / "configurations" / (mode + ".json"),
                        mode,
                        "review" if consumer == "classic" else "write",
                        "commit",
                        "abandoned",
                        "done",
                        "implementation",
                    )
                    install.apply(repo, summary, changes)
                    for host in verify.HOSTS:
                        compiled, docs = verify.compile_package(
                            binary, authority, repo, package, root / host, host
                        )
                        assert "w6:workflow/w6-" + mode in docs
                        quality = docs["w6:workflow/w6-" + mode]
                        assert quality["limits"]["max_parallelism"] == 1
                        readers = [
                            v
                            for k, v in docs.items()
                            if k.startswith("w6:step/")
                            and any(k.endswith(s) for s in ("-review", "-ui", "-ux"))
                        ]
                        assert readers and all(
                            v["repository_workspace"] == "read_only" for v in readers
                        )
                        results.append(
                            {
                                "mode": mode,
                                "consumer": consumer,
                                "host": host,
                                "definitions": len(docs),
                                "build_key": compiled["build_key"],
                            }
                        )
                    assert all(
                        (folder / p).read_bytes() == raw for p, raw in originals.items()
                    )
                    if consumer == "minimal" and mode == "combined":
                        overlay_path = folder / "extend.yaml"
                        original_overlay = overlay_path.read_bytes()
                        mutations = {
                            "missing-callee": lambda x: x["extensions"][0].update(
                                call="missing"
                            ),
                            "wrong-kind": lambda x: x["extensions"][0].update(
                                call="w6-review-review"
                            ),
                            "missing-input": lambda x: x["extensions"][0][
                                "input_bindings"
                            ].clear(),
                            "late-producer": lambda x: x["extensions"][0][
                                "input_bindings"
                            ].update(implementation="$stages.commit.implementation"),
                            "unsupported-input-source": lambda x: x["extensions"][0][
                                "input_bindings"
                            ].update(implementation="$inputs.task"),
                            "missing-outcome": lambda x: x["extensions"][0]["on"].pop(
                                "partial"
                            ),
                            "missing-export": lambda x: x["extensions"][1][
                                "input_bindings"
                            ].update(receipt="$stages.w6-quality.missing"),
                        }
                        for name, mutate in mutations.items():
                            value = json.loads(original_overlay)
                            mutate(value)
                            overlay_path.write_text(json.dumps(value))
                            refused = verify.run(
                                binary,
                                "--project",
                                authority,
                                "project",
                                "compile",
                                "--repository",
                                repo,
                                "--package",
                                package,
                                "--host",
                                "codex-cli",
                                "--output",
                                root / ("refused-" + name),
                                expect_ok=False,
                            )
                            problem = json.loads(refused.strip().splitlines()[-1])
                            assert (
                                problem.get("code")
                                and problem["code"] != "internal_error"
                            ), problem
                            refusals.append({"case": name, "code": problem["code"]})
                        overlay_path.write_bytes(original_overlay)
                        callee = folder / "project/workflows/w6-combined.yaml"
                        original_callee = callee.read_bytes()
                        altered = json.loads(original_callee)
                        altered["refs"]["implementation"] = "{{schema_task}}"
                        callee.write_text(json.dumps(altered))
                        refused = verify.run(
                            binary,
                            "--project",
                            authority,
                            "project",
                            "compile",
                            "--repository",
                            repo,
                            "--package",
                            package,
                            "--host",
                            "codex-cli",
                            "--output",
                            root / "refused-schema",
                            expect_ok=False,
                        )
                        problem = json.loads(refused.strip().splitlines()[-1])
                        assert problem["code"] == "port_type_mismatch", problem
                        refusals.append(
                            {"case": "wrong-schema", "code": problem["code"]}
                        )
                        callee.write_bytes(original_callee)

                finally:
                    verify.forget_authority(authority)
    return {
        "prifly": verify.run(binary, "version")["version"],
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "compiles": results,
        "refusals": refusals,
        "scope": "compile only; no host execution",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = check(args.binary)
    if args.report:
        args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
