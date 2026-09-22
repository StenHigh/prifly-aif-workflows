#!/usr/bin/env python3
"""Generate the two quality-tail folders from their classic counterparts."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAIL = """inputs:
  task: {schema_ref: schema_task}
  handoff: {schema_ref: schema_warmup-handoff}
  plan: {schema_ref: schema_plan_manifest}
  implementation: {schema_ref: schema_implementation}
  security_enabled:
    schema_ref: schema_feature-enabled
    required: false
    configuration: {scope: project, default: true}
outputs:
  implementation: {schema_ref: schema_implementation, required_for: [succeeded]}
  plan: {schema_ref: schema_plan_manifest, required_for: [succeeded]}
  gate: {schema_ref: schema_gate-result, required_for: [partial]}
limits: {max_step_instances: 160, max_control_transitions: 800, max_parallelism: 1, max_child_depth: 4}
policy_ref: local_policy
features:
  security: {input: security_enabled}
entry: verify
stages:
  verify:
    kind: call
    workflow_ref: workflow_verify-batch
    input_bindings: {implementation: $inputs.implementation, handoff: $inputs.handoff, plan: $inputs.plan}
    on: {succeeded: choose-security, partial: fix-after-verify}
  choose-security:
    kind: choice
    selection: exclusive
    branches:
      - id: enabled
        predicate: {op: eq, left: $inputs.security_enabled, right: true}
        next: security
    default: review
  security:
    kind: step
    step_ref: step_security
    input_bindings: {implementation: $stages.verify.implementation}
    on: {pass: security-decision, needs_revision: fix-after-security, fail: abandoned, no_work: abandoned}
  security-decision:
    kind: choice
    selection: exclusive
    branches:
      - id: blockers
        predicate: {op: eq, left: $stages.security.gate#/blocking, right: true}
        next: fix-after-security
    default: review
  review:
    kind: call
    workflow_ref: workflow_review-batch
    input_bindings: {implementation: $stages.verify.implementation, handoff: $inputs.handoff, plan: $inputs.plan}
    on: {succeeded: commit, partial: fix-after-review}
  commit:
    kind: step
    step_ref: step_commit
    input_bindings: {implementation: $stages.review.implementation}
    on: {pass: done, needs_revision: abandoned, fail: abandoned, no_work: abandoned}
  done:
    kind: finish
    outcome: succeeded
    output_bindings: {implementation: $stages.commit.implementation, plan: $inputs.plan}
  fix-after-verify:
    kind: finish
    outcome: partial
    output_bindings: {gate: $stages.verify.gate}
  fix-after-security:
    kind: finish
    outcome: partial
    output_bindings: {gate: $stages.security.gate}
  fix-after-review:
    kind: finish
    outcome: partial
    output_bindings: {gate: $stages.review.gate}
  abandoned: {kind: finish, outcome: rejected}
"""


def files(source, name, prefix):
    result = {}
    old = "aif-profiled" if source.name == "aif-profiled" else "aif"
    for path in sorted(source.rglob("*")):
        if not path.is_file() or path.name == ".DS_Store":
            continue
        relative = path.relative_to(source)
        text = path.read_text()
        if relative == Path("workflow.yaml"):
            text = text.split("\ninputs:\n", 1)[0] + "\n" + TAIL
            header, tail = text.split("inputs:\n", 1)
            text = header + (
                "decision_catalog:\n"
                f"  - .prifly/workflows/{name}/decisions/gates/checks.yaml\n"
                f"  - .prifly/workflows/{name}/decisions/gates/warnings.yaml\n"
            ) + "inputs:\n" + tail
            text = text.replace(f"id: {old}:package/classic", f"id: {prefix}:package/classic")
            text = text.replace(f"id: {old}:workflow/classic", f"id: {prefix}:workflow/classic-continuation")
            text = text.replace("version: 1.42.0", "version: 1.0.0")
            text = text.replace("version: 1.43.0", "version: 1.0.0")
            text = text.replace("Canonical AI Factory development workflow with bounded plan improvement.", "Continuation of an existing implementation through the quality gates.")
            text = text.replace("title: AI Factory classic development workflow", "title: AI Factory continuation quality tail")
            text = text.replace("title: AI Factory profiled development workflow", "title: AI Factory profiled continuation quality tail")
            text = text.replace(f".prifly/workflows/{source.name}/", f".prifly/workflows/{name}/")
        elif relative.parts[0] in ("steps", "workflows"):
            text = text.replace(f"id: {old}:", f"id: {prefix}:", 1)
        elif relative == Path("schemas/implementation.yaml"):
            text = text.replace("id: aif:schema/implementation", f"id: {prefix}:schema/implementation")
            text = text.replace("maxItems: 200", "maxItems: 1000")
        elif relative == Path("extend.yaml"):
            models = ""
            if "model_profiles:\n" in text:
                models = "model_profiles:\n" + text.split("model_profiles:\n", 1)[1].split("# `extensions`", 1)[0]
            text = "profile: fast\nexclude: []\n" + models + "extensions: []\n"
        elif relative == Path("README.md"):
            text = f"# {name}\n\nContinuation quality tail generated from `{source.name}`. Start it with `prifly project continue`.\n"
        result[relative] = text
    return result


def main(check=False):
    stale = []
    for source_name, name, prefix in (
        ("aif-classic", "aif-classic-continuation", "aif-continuation"),
        ("aif-profiled", "aif-profiled-continuation", "aif-profiled-continuation"),
    ):
        target = ROOT / name
        generated = files(ROOT / source_name, name, prefix)
        for relative, text in generated.items():
            path = target / relative
            if check:
                if not path.is_file() or path.read_text() != text:
                    stale.append(str(path.relative_to(ROOT)))
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
        if check:
            stale.extend(str(path.relative_to(ROOT)) for path in target.rglob("*") if path.is_file() and path.relative_to(target) not in generated)
    if stale:
        sys.exit("stale continuation files: " + ", ".join(stale))


if __name__ == "__main__":
    main("--check" in sys.argv)
