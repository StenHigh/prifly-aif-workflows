"""Derive explicit project-owned W1/W2 copies; Python+PyYAML, no engine mutation."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "examples/review-uiux-extensions/bundle"
CORE = {
    "process": "core:adapter/local-process@2.0.0",
    "session": "core:adapter/assisted-session@1.0.0",
    "policy": "core:policy/local@4.0.0",
    "result": "core:schema/step-result@1.0.0",
    "result_v2": "core:schema/step-result@2.0.0",
}
MODES = ("review", "uiux", "combined")


def build(target):
    sources = {}
    groups = {}
    bindings = {}

    def put(path, value):
        file = target / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        return path

    for group, package in [("review", "aif-review-evidence"), ("product", "aif-ui-ux")]:
        aliases = {}
        docs = []
        for kind in ("contexts", "schemas", "steps", "workflows"):
            for path in sorted((ROOT / package / kind).glob("*.yaml")):
                if kind == "steps" and path.stem == "configure":
                    continue
                name = "w6-" + group + "-" + path.stem
                alias = kind.rstrip("s") + "_" + path.stem
                aliases[alias] = kind.rstrip("s") + "_" + name
                docs.append((kind, path, name))
        paths = []
        for kind, source, name in docs:
            data = yaml.safe_load(source.read_text())
            sources[str(source.relative_to(ROOT))] = (
                "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
            )
            data["id"] = "w6:" + kind.rstrip("s") + "/" + name
            data["version"] = "1.0.0"
            text = json.dumps(data)
            for old, new in {**aliases, **{k: "w6-" + k for k in CORE}}.items():
                text = text.replace("{{" + old + "}}", "{{" + new + "}}")
            paths.append(
                put("project/" + kind + "/" + name + ".yaml", json.loads(text))
            )
        groups[group] = paths
        root_path = ROOT / package / "workflow.yaml"
        sources[str(root_path.relative_to(ROOT))] = (
            "sha256:" + hashlib.sha256(root_path.read_bytes()).hexdigest()
        )
        root = yaml.safe_load(root_path.read_text())
        for step, binding in root["execution_bindings"]["steps"].items():
            name = step.rsplit("/", 1)[-1]
            if name == "configure":
                continue
            binding["files"] = {n: "project/files/w6-" + n for n in binding["files"]}
            bindings["w6-" + group + "-" + name] = binding
    for filename, source in [
        ("evidence.py", ROOT / "aif-review-evidence/files/evidence.py"),
        ("product.py", ROOT / "aif-ui-ux/files/product.py"),
        ("acceptance.py", ROOT / "examples/review-uiux-extensions/acceptance.py"),
    ]:
        file = target / "project/files" / ("w6-" + filename)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(source.read_bytes())
        sources[str(source.relative_to(ROOT))] = (
            "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
        )
    candidate = yaml.safe_load(
        (ROOT / "aif-review-evidence/schemas/candidate.yaml").read_text()
    )
    candidate.update(id="w6:schema/w6-candidate", version="1.0.0")
    common = [put("project/schemas/w6-candidate.yaml", candidate)]
    receipt = {
        "id": "w6:schema/w6-receipt",
        "version": "1.0.0",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "protocol",
            "run_id",
            "candidate",
            "implementation",
            "configuration_digest",
            "report_digests",
        ],
        "properties": {
            "protocol": {"const": "w6-acceptance/1"},
            "run_id": {"type": "string"},
            "candidate": {"type": "object"},
            "implementation": {"type": "object"},
            "configuration_digest": {
                "type": "string",
                "pattern": "^sha256:[0-9a-f]{64}$",
            },
            "report_digests": {
                "type": "object",
                "additionalProperties": {
                    "type": "string",
                    "pattern": "^sha256:[0-9a-f]{64}$",
                },
            },
        },
    }
    common.append(put("project/schemas/w6-receipt.yaml", receipt))
    assessment = {
        "id": "w6:schema/w6-assessment",
        "version": "1.0.0",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "protocol",
            "gate",
            "stage",
            "candidate_digest",
            "fresh",
            "report_digests",
            "report_refs",
        ],
        "properties": {
            "protocol": {"const": "w6-assessment/1"},
            "gate": {"type": "object"},
            "stage": {"enum": ["review", "product"]},
            "candidate_digest": {"type": "string"},
            "fresh": {"type": "boolean"},
            "report_digests": {"type": "object"},
            "report_refs": {"type": "object"},
        },
    }
    common.append(put("project/schemas/w6-assessment.yaml", assessment))

    def step(name, inputs, outputs):
        return {
            "authoring": "prifly-step/1",
            "id": "w6:step/" + name,
            "version": "1.0.0",
            "title": name,
            "kind": "worker",
            "inputs": {k: {"schema_ref": v} for k, v in inputs.items()},
            "outputs": {
                k: {"schema_ref": v, "required_for": ["pass"]}
                for k, v in outputs.items()
            },
            "executor": {"adapter_ref": "{{w6-process}}", "operation": "process"},
            "effects": {"class": "none", "retry_class": "pure"},
            "result_schema_ref": "{{w6-result}}",
        }

    def program(op, mode):
        return {
            "executable": "python",
            "args": ["-B", "acceptance.py", op, mode],
            "files": {
                "acceptance.py": "project/files/w6-acceptance.py",
                "evidence.py": "project/files/w6-evidence.py",
                "product.py": "project/files/w6-product.py",
                "settings.json": "project/files/w6-settings.json",
            },
            "timeout_ms": 120000,
            "grace_ms": 100,
            "max_output_bytes": 1048576,
        }

    impl = "{{schema_implementation}}"
    cand = "{{schema_w6-candidate}}"
    rec = "{{schema_w6-receipt}}"
    assessment_ref = "{{schema_w6-assessment}}"
    common.append(
        put(
            "project/steps/w6-committed-check.yaml",
            step("w6-committed-check", {"implementation": impl, "receipt": rec}, {}),
        )
    )
    post = {
        "authoring": "prifly-workflow/1",
        "schema_version": "6",
        "id": "w6:workflow/w6-committed",
        "version": "1.0.0",
        "title": "Verify committed bytes against original acceptance",
        "refs": {
            "check": "{{step_w6-committed-check}}",
            "implementation": impl,
            "receipt": rec,
            "assessment": assessment_ref,
            "policy": "{{w6-policy}}",
        },
        "inputs": {"implementation": "implementation", "receipt": "receipt"},
        "outputs": {},
        "entry": "check",
        "policy_ref": "policy",
        "limits": {
            "max_step_instances": 1,
            "max_control_transitions": 4,
            "max_parallelism": 1,
            "max_child_depth": 1,
        },
        "stages": {
            "check": {
                "kind": "step",
                "step_ref": "check",
                "input_bindings": {
                    "implementation": "$inputs.implementation",
                    "receipt": "$inputs.receipt",
                },
                "on": {
                    "pass": "done",
                    "fail": "rejected",
                    "needs_revision": "rejected",
                    "no_work": "rejected",
                },
                "impossible_verdicts": ["blocked"],
            },
            "done": {"kind": "finish", "outcome": "succeeded"},
            "rejected": {"kind": "finish", "outcome": "rejected"},
        },
    }
    common.append(put("project/workflows/w6-committed.yaml", post))
    manifest = {
        "protocol": "w6-project-bundle/1",
        "version": "1.0.0",
        "sources": sources,
        "references": {"w6-" + k: v for k, v in CORE.items()},
        "modes": {},
    }
    for mode in MODES:
        review = mode in ("review", "combined")
        product = mode in ("uiux", "combined")
        files = list(common) + [
            f"project/files/w6-{f}"
            for f in ("evidence.py", "product.py", "acceptance.py")
        ]
        if review:
            files += groups["review"]
        if product:
            files += groups["product"]
        output = {"candidate": cand, "implementation": impl}
        seal_inputs = {"candidate": cand, "implementation": impl}
        refs = {
            "prepare": "{{step_w6-" + mode + "-prepare}}",
            "seal": "{{step_w6-" + mode + "-seal}}",
            "implementation": impl,
            "candidate": cand,
            "receipt": rec,
            "assessment": assessment_ref,
            "policy": "{{w6-policy}}",
        }
        prep_bindings = {"implementation": "$inputs.implementation"}
        seal_bind = {
            "implementation": "$stages.prepare.implementation",
            "candidate": "$stages.prepare.candidate",
        }
        exports = {
            "receipt": {"schema_ref": "receipt", "required_for": ["succeeded"]},
            "assessment": {
                "schema_ref": "assessment",
                "required_for": ["succeeded", "partial"],
            },
        }
        stages = {
            "prepare": {
                "kind": "step",
                "step_ref": "prepare",
                "input_bindings": prep_bindings,
                "on": {
                    "pass": "review" if review else "product",
                    "fail": "rejected",
                    "needs_revision": "rejected",
                    "no_work": "rejected",
                },
                "impossible_verdicts": ["blocked"],
            }
        }
        success_exports = {
            "receipt": "$stages.seal.receipt",
            "assessment": "$stages.seal.assessment",
        }
        for group in (["review"] if review else []) + (["product"] if product else []):
            alias = "w6-" + group + "-"
            refs[group] = "{{workflow_" + alias + "quality}}"
            group_outputs = (
                ["gate", "report"]
                if group == "review"
                else ["gate", "ui_report", "ux_report", "environment", "release"]
            )
            for port in group_outputs:
                schema = "report" if port in ("ui_report", "ux_report") else port
                key = group + "_" + port
                refs[key] = "{{schema_" + alias + schema + "}}"
                exports[key] = {"schema_ref": key, "required_for": ["succeeded"]}
                success_exports[key] = "$stages." + group + "." + port
                if port == "gate" or port.endswith("report"):
                    seal_inputs[key] = refs[key]
                    seal_bind[key] = "$stages." + group + "." + port
            if group == "review":
                output["request"] = "{{schema_w6-review-request}}"
                refs["request"] = output["request"]
                ins = {"request": "$stages.prepare.request"}
            else:
                for port, schema in [
                    ("configuration", "configuration"),
                    ("ui", "request"),
                    ("ux", "request"),
                ]:
                    output[port] = "{{schema_w6-product-" + schema + "}}"
                refs.update(
                    configuration=output["configuration"],
                    ui=output["ui"],
                    ux=output["ux"],
                )
                ins = {p: "$stages.prepare." + p for p in ("configuration", "ui", "ux")}
            stages[group] = {
                "kind": "call",
                "workflow_ref": group,
                "input_bindings": ins,
                "on": {
                    "succeeded": "product" if group == "review" and product else "seal",
                    "partial": group + "-diagnostic",
                    "rejected": "rejected",
                },
            }
            diagnostic = "w6-" + mode + "-" + group + "-diagnostic"
            refs[group + "_diagnostic"] = "{{step_" + diagnostic + "}}"
            ports = ["report"] if group == "review" else ["ui_report", "ux_report"]
            diagnostic_inputs = {"candidate": cand, "gate": refs[group + "_gate"]}
            diagnostic_bind = {
                "candidate": "$stages.prepare.candidate",
                "gate": "$stages." + group + ".gate",
            }
            for port in ports:
                key = group + "_" + port
                diagnostic_inputs[key] = refs[key]
                diagnostic_bind[key] = "$stages." + group + "." + port
            files.append(
                put(
                    "project/steps/" + diagnostic + ".yaml",
                    step(diagnostic, diagnostic_inputs, {"assessment": assessment_ref}),
                )
            )
            stages[group + "-diagnostic"] = {
                "kind": "step",
                "step_ref": group + "_diagnostic",
                "input_bindings": diagnostic_bind,
                "on": {
                    "pass": group + "-partial",
                    "fail": "rejected",
                    "needs_revision": "rejected",
                    "no_work": "rejected",
                },
                "impossible_verdicts": ["blocked"],
            }
            stages[group + "-partial"] = {
                "kind": "finish",
                "outcome": "partial",
                "output_bindings": {
                    "assessment": "$stages." + group + "-diagnostic.assessment"
                },
            }
        files.append(
            put(
                "project/steps/w6-" + mode + "-prepare.yaml",
                step("w6-" + mode + "-prepare", {"implementation": impl}, output),
            )
        )
        files.append(
            put(
                "project/steps/w6-" + mode + "-seal.yaml",
                step(
                    "w6-" + mode + "-seal",
                    seal_inputs,
                    {"receipt": rec, "assessment": assessment_ref},
                ),
            )
        )
        stages["seal"] = {
            "kind": "step",
            "step_ref": "seal",
            "input_bindings": seal_bind,
            "on": {
                "pass": "done",
                "fail": "rejected",
                "needs_revision": "rejected",
                "no_work": "rejected",
            },
            "impossible_verdicts": ["blocked"],
        }
        stages["done"] = {
            "kind": "finish",
            "outcome": "succeeded",
            "output_bindings": success_exports,
        }
        stages["rejected"] = {"kind": "finish", "outcome": "rejected"}
        graph = {
            "authoring": "prifly-workflow/1",
            "schema_version": "6",
            "id": "w6:workflow/w6-" + mode,
            "version": "1.0.0",
            "title": "Project " + mode + " acceptance",
            "refs": refs,
            "inputs": {"implementation": "implementation"},
            "outputs": exports,
            "entry": "prepare",
            "policy_ref": "policy",
            "limits": {
                "max_step_instances": 12,
                "max_control_transitions": 60,
                "max_parallelism": 1,
                "max_child_depth": 2,
            },
            "stages": stages,
        }
        files.append(put("project/workflows/w6-" + mode + ".yaml", graph))
        selected = {
            k: v
            for k, v in bindings.items()
            if (review and k.startswith("w6-review-"))
            or (product and k.startswith("w6-product-"))
        }
        selected.update(
            {
                "w6-" + mode + "-prepare": program("prepare", mode),
                "w6-" + mode + "-seal": program("seal", mode),
                "w6-committed-check": program("committed", mode),
            }
        )
        for group in (["review"] if review else []) + (["product"] if product else []):
            selected["w6-" + mode + "-" + group + "-diagnostic"] = program(
                "diagnostic", group
            )
        manifest["modes"][mode] = {
            "files": sorted(files),
            "bindings": selected,
            "call": "w6-" + mode,
        }
    manifest["files"] = {
        str(p.relative_to(target)): "sha256:"
        + hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(target.rglob("*"))
        if p.is_file()
    }
    put("manifest.json", manifest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="w6-bundle-") as tmp:
        output = Path(tmp)
        build(output)
        if args.check:
            files = lambda root: {
                str(p.relative_to(root)): p.read_bytes()
                for p in root.rglob("*")
                if p.is_file() and "__pycache__" not in p.parts
            }
            assert files(output) == files(
                TARGET
            ), "W6 bundle differs: run tools/build_review_uiux_bundle.py"
        else:
            if TARGET.exists():
                shutil.rmtree(TARGET)
            shutil.copytree(output, TARGET)
