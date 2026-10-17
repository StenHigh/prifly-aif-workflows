"""Project W6 adapters. Native child execution; no scheduler, writes or cleanup here."""

import json
import os
from pathlib import Path
import sys

import evidence as w1
import product as w2


def prepare(settings, implementation, tree, mode):
    w1.obj(settings, ("mode", "review", "product"), "settings")
    if settings["mode"] != mode:
        raise w1.Invalid("Installed mode and sealed configuration differ")
    base = implementation["base_commit"]
    captured = w1.snapshot(tree, base)
    if captured["head_commit"] != implementation["head_commit"]:
        raise w1.Invalid("Implementation HEAD is stale; replay the upstream producer")
    values = {"candidate": captured, "implementation": implementation}
    if mode in ("review", "combined"):
        request = dict(settings["review"])
        request["base_commit"] = base
        w1.request(request)
        values["request"] = request
    elif settings["review"] is not None:
        raise w1.Invalid("UI/UX-only mode must declare review:null")
    if mode in ("uiux", "combined"):
        config = json.loads(json.dumps(settings["product"]))
        for lens in ("ui", "ux"):
            config[lens]["base_commit"] = base
        w2.configuration(config)
        values.update(
            configuration=config,
            ui=w2.project(config, "ui"),
            ux=w2.project(config, "ux"),
        )
    elif settings["product"] is not None:
        raise w1.Invalid("Review-only mode must declare product:null")
    return values


def seal(inputs, tree, run_id, settings_bytes, report_digests):
    captured = inputs["candidate"]
    w1.candidate(captured)
    if w1.snapshot(tree, captured["base_commit"]) != captured:
        raise w1.Invalid(
            "Candidate changed during acceptance; fresh whole-child replay required"
        )
    for name in ("review_gate", "product_gate"):
        if name in inputs:
            gate = inputs[name]
            if (
                gate["blocking"]
                or gate["blocking_owner_only"]
                or gate["status"] not in ("passed", "warnings")
            ):
                raise w1.Invalid("Blocking or unavailable acceptance gate: " + name)
    return {
        "protocol": "w6-acceptance/1",
        "run_id": run_id,
        "candidate": captured,
        "implementation": inputs["implementation"],
        "configuration_digest": w1.digest(settings_bytes),
        "report_digests": report_digests,
    }


def committed(receipt, implementation, tree, run_id):
    if receipt["protocol"] != "w6-acceptance/1":
        raise w1.Invalid("Unknown acceptance protocol")
    # Native bindings validate provenance, including accepted-prefix inheritance.
    # receipt.run_id records its producer; a reviewed continuation has a new Run.
    w1.candidate(receipt["candidate"])
    if implementation["base_commit"] != receipt["candidate"]["base_commit"]:
        raise w1.Invalid("Original base changed")
    current = w1.snapshot(tree, implementation["base_commit"])
    if current["head_commit"] != implementation["head_commit"]:
        raise w1.Invalid("Commit result does not name actual HEAD")
    if current["files_digest"] != receipt["candidate"]["files_digest"]:
        raise w1.Invalid(
            "Files differ from accepted candidate; local commit may exist, Run is rejected"
        )
    # Commit may advance HEAD/index, never replace accepted files or history.
    w1.git(
        tree,
        "merge-base",
        "--is-ancestor",
        receipt["candidate"]["head_commit"],
        current["head_commit"],
    )
    return receipt


def worker(operation, mode):
    envelope = json.load(sys.stdin)
    context = json.loads(Path(os.environ["PRIFLY_CONTEXT_FILE"]).read_text())
    result = {
        "schema_version": "1",
        **{k: envelope[k] for k in ("run_id", "step_instance_id", "attempt_id")},
        "envelope_digest": os.environ["PRIFLY_ENVELOPE_DIGEST"],
        "verdict": "pass",
        "outputs": {},
        "evidence_refs": [],
        "effect_receipt_refs": [],
        "summary": "W6 " + operation,
    }

    def read(port):
        return json.loads(Path(context["inputs"][port]["path"]).read_bytes())

    def output(port, value):
        slot = context["outputs"][port]
        raw = w1.encoded(value) + b"\n"
        Path(slot["path"]).write_bytes(raw)
        result["outputs"][port] = {k: slot[k] for k in ("artifact_id", "revision")}
        result["outputs"][port]["digest"] = w1.digest(raw)

    try:
        tree = os.environ["PRIFLY_REPOSITORY_WORKSPACE"]
        if operation == "prepare":
            values = prepare(
                json.loads(Path("settings.json").read_bytes()),
                read("implementation"),
                tree,
                mode,
            )
            for port in context["outputs"]:
                output(port, values[port])
        elif operation in ("seal", "diagnostic"):
            inputs = {p: read(p) for p in context["inputs"]}
            digests = {
                p: w1.digest(Path(context["inputs"][p]["path"]).read_bytes())
                for p in inputs
                if p.endswith("_report")
            }
            refs = {p: context["inputs"][p]["ref"] for p in digests}
            if operation == "seal":
                output(
                    "receipt",
                    seal(
                        inputs,
                        tree,
                        envelope["run_id"],
                        Path("settings.json").read_bytes(),
                        digests,
                    ),
                )
                stage = "product" if "product_gate" in inputs else "review"
                gate = inputs[stage + "_gate"]
                fresh = True
            else:
                stage = mode
                gate = inputs["gate"]
                fresh = (
                    w1.snapshot(tree, inputs["candidate"]["base_commit"])
                    == inputs["candidate"]
                )
            output(
                "assessment",
                {
                    "protocol": "w6-assessment/1",
                    "gate": gate,
                    "stage": stage,
                    "candidate_digest": inputs["candidate"]["digest"],
                    "fresh": fresh,
                    "report_digests": digests,
                    "report_refs": refs,
                },
            )
        elif operation == "committed":
            committed(read("receipt"), read("implementation"), tree, envelope["run_id"])
        else:
            raise w1.Invalid("Unknown W6 operation")
    except (
        ValueError,
        OSError,
        KeyError,
        TypeError,
        w1.subprocess.SubprocessError,
    ) as error:
        result.update(
            verdict="fail", outputs={}, summary="W6 diagnostic stop: " + str(error)
        )
    os.write(3, w1.encoded(result) + b"\n")


if __name__ == "__main__":
    worker(*sys.argv[1:])
