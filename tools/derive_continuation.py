#!/usr/bin/env python3
"""Generate the two quality-tail folders from their classic counterparts."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# (source, tail, id prefix, tail version). The version is the tail's own, not
# its source's: bump it by hand whenever the regenerated tail's bytes change —
# tests/test_versions.py fails a release that forgets.
TAILS = (
    ("aif-classic", "aif-classic-continuation", "aif-continuation", "1.2.0"),
    ("aif-profiled", "aif-profiled-continuation", "aif-profiled-continuation", "1.2.0"),
)
RESUME = Path(__file__).resolve().parent / "continuation" / "resume.mjs"
# Pri-Fly 0.13.56 stopped knowing any package: what a tail continues from, and
# where each input comes from, is declared here (WorkflowRevision 7). The
# implementation is not carried over: the resume step reads it off the tree the
# tail is handed, which may have moved since the source Run stopped.
CONTINUATION = """continuation:
  from_workflows: [aif:workflow/classic, aif-profiled:workflow/classic]
  from_outcomes: [partial, rejected]
  from_cancelled: true
  inputs:
    task: {source_input: task}
    handoff: {stage: warmup, output: handoff, verdict: pass}
    plan: {stage: implement, output: plan, verdict: pass}
    previous_implementation: {stage: implement, output: implementation, verdict: pass}
"""
BINDINGS = """execution_bindings:
  steps:
    {prefix}:step/resume:
      executable: node
      args: [resume.mjs]
      files: {{resume.mjs: files/resume.mjs}}
      timeout_ms: 60000
      grace_ms: 1000
      max_output_bytes: 65536
"""
RESUME_STEP = """authoring: prifly-step/1
id: {prefix}:step/resume
version: 1.0.0
title: Check the handed-over tree still holds the source implementation
kind: worker
inputs:
  previous_implementation: {{schema_ref: "{{{{schema_implementation}}}}"}}
outputs:
  implementation: {{schema_ref: "{{{{schema_implementation}}}}", required_for: [pass]}}
executor: {{adapter_ref: "{{{{process_adapter}}}}", operation: process}}
effects: {{class: none, retry_class: pure}}
result_schema_ref: "{{{{step_result_schema_v2}}}}"
"""
TAIL = """inputs:
  task: {schema_ref: schema_task}
  handoff: {schema_ref: schema_warmup-handoff}
  plan: {schema_ref: schema_plan_manifest}
  previous_implementation: {schema_ref: schema_implementation}
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
entry: resume
stages:
  resume:
    kind: step
    step_ref: step_resume
    input_bindings: {previous_implementation: $inputs.previous_implementation}
    on: {pass: verify, fail: unrelated, blocked: unresumed}
    # A program of this package, not a host: it returns what it is written to.
    impossible_verdicts: [needs_revision, no_work]
  unrelated:
    kind: finish
    outcome: rejected
    description: The handed-over tree does not contain the implementation the source Run accepted, so there is nothing here to continue.
  unresumed:
    kind: finish
    outcome: rejected
    description: The tree could not be read — no claimed workspace or no git — so nothing was judged; the resume step names what was missing.
  verify:
    kind: call
    workflow_ref: workflow_verify-batch
    input_bindings: {implementation: $stages.resume.implementation, handoff: $inputs.handoff, plan: $inputs.plan}
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
    on: {pass: security-decision, needs_revision: fix-after-security, fail: abandoned, no_work: abandoned, blocked: security-blocked}
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
    impossible_verdicts: [blocked]
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
  security-blocked:
    kind: finish
    outcome: partial
    output_bindings: {gate: $stages.security.gate}
    description: A dependency the security checks need was unavailable, so the work was not judged; repeat with project continue once it is back.
  fix-after-review:
    kind: finish
    outcome: partial
    output_bindings: {gate: $stages.review.gate}
  abandoned: {kind: finish, outcome: rejected}
"""


def files(source, name, prefix, version):
    result = {}
    old = "aif-profiled" if source.name == "aif-profiled" else "aif"
    for path in sorted(source.rglob("*")):
        if not path.is_file() or path.name == ".DS_Store":
            continue
        relative = path.relative_to(source)
        text = path.read_text()
        if relative == Path("workflow.yaml"):
            text = text.split("\ninputs:\n", 1)[0] + "\n" + TAIL + BINDINGS.format(prefix=prefix)
            header, tail = text.split("inputs:\n", 1)
            header = header.replace('schema_version: "6"', 'schema_version: "7"')
            header = header.replace("  step_commit: \"{{step_commit}}\"\n", "  step_commit: \"{{step_commit}}\"\n  step_resume: \"{{step_resume}}\"\n")
            header = header.replace("    step_result_schema_v2: core:schema/step-result@2.0.0\n", "    step_result_schema_v2: core:schema/step-result@2.0.0\n    process_adapter: core:adapter/local-process@2.0.0\n")
            text = header + (
                "decision_catalog:\n"
                f"  - .prifly/workflows/{name}/decisions/gates/checks.yaml\n"
                f"  - .prifly/workflows/{name}/decisions/gates/warnings.yaml\n"
            ) + CONTINUATION + "inputs:\n" + tail
            text = text.replace(f"id: {old}:package/classic", f"id: {prefix}:package/classic")
            text = text.replace(f"id: {old}:workflow/classic", f"id: {prefix}:workflow/classic-continuation")
            text = re.sub(r"^(  )?version: \S+$", rf"\g<1>version: {version}", text, flags=re.M)
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
            text = (f"# {name}\n\nContinuation quality tail generated from `{source.name}`: `resume → verify → security → review → commit` "
                    "over the tree a partial, rejected or cancelled classic Run left. Start it with `prifly project continue`; its first step "
                    "is a Node program, so allow `node` in `.prifly/local.yaml` and pass `--allow-execution`. Needs Pri-Fly 0.13.58. "
                    "See \"Продолжение\" in the repository README.\n")
        result[relative] = text
    result[Path("steps/resume.yaml")] = RESUME_STEP.format(prefix=prefix)
    result[Path("files/resume.mjs")] = RESUME.read_text()
    return result


def derive():
    """Every tail file keyed by its path from the repository root."""
    return {
        Path(name) / relative: text
        for source_name, name, prefix, version in TAILS
        for relative, text in files(ROOT / source_name, name, prefix, version).items()
    }


def main(check=False):
    generated = derive()
    stale = []
    for relative, text in generated.items():
        path = ROOT / relative
        if check:
            if not path.is_file() or path.read_text() != text:
                stale.append(str(relative))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    if check:
        for _, name, _, _ in TAILS:
            stale.extend(str(path.relative_to(ROOT)) for path in (ROOT / name).rglob("*") if path.is_file() and path.relative_to(ROOT) not in generated)
    if stale:
        sys.exit("stale continuation files: " + ", ".join(stale))

if __name__ == "__main__":
    main("--check" in sys.argv)
