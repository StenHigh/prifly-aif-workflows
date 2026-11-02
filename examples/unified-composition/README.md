# Unified composition on Pri-Fly v0.13.85

This candidate requires the explicit shared schema dependency described in
[contracts](../../contracts/README.md). Install the current package sources first;
shipping v1.56.0 packages do not publish these exports.

## Public UI/UX components

`aif-ui-ux` folder `/3` publishes the `configure` Step and the `quality` workflow.
The standalone launch remains available. The example imports those components
through `/5`; it does not copy the provider's private stages or programs.

```sh
python3 tools/install_composition_contracts.py \
  --binary /absolute/prifly-v0.13.85 --project /absolute/authority
python3 examples/unified-composition/setup.py --repository /absolute/project
/absolute/prifly-v0.13.85 --project /absolute/authority project compile \
  --repository /absolute/project --package ui-ux-composed --host codex-app \
  --output /absolute/scratch/compiled
/absolute/prifly-v0.13.85 --project /absolute/authority project questionnaire \
  --repository /absolute/project --launch ui-ux-composed --host codex-app \
  --workspace worktree --input configuration=/absolute/configuration.json \
  --allow-execution --prepare --json
```

`configuration.json` follows `aif-ui-ux/schemas/configuration.yaml`: task/candidate
basis, explicit applicability, requiredness, viewports, scenarios and an owned
environment contract. It is project input, not a universal default.

Review the complete summary. Start with the same arguments through `project start`
and `--expected-launch-digest` equal to its exact `review_digest`. Program execution
requires the explicitly configured Python executable and execution consent.
For a stopped Run, use this same launch and `project continue --prepare --source-run
RUN`, without new configuration. Continue replays the root quality Call where
required; a nested resume stage is not supported. Show the new reviewed summary
and use its top-level digest before continuing.

```text
shared schemas → configure (public Step) → quality (public Call)
                                              ↓
                               capture → environment → UI → UX
                                              ↓
                                    evaluate → release → finalize
```

## Nested measurement points

Classic/profiled expose `before-verify` and `before-review` inside each repeat
body. Fix exposes `before-build`, `before-quality` and output-free `after-commit`. Their
`extension-points.yaml` owns anchors, routes, input bindings and consumers.
The project writes only `extend.yaml` and `project/**`:

```yaml
authoring: prifly-extension/5
extensions:
  - id: project-measurement
    point: before-verify
    step: measurement
    output_bindings:
      verify-implementation: implementation
      fix-implementation: implementation
      clean-implementation: implementation
```

The project Step binds `implementation` to `{{contract_schema_implementation}}`
and emits that same schema on every success path. It preserves original report
refs and appends newly published report refs. Each ordinary ArtifactRef has
`artifact_id`, integer `revision` and `digest`. A ref does not attest applicability
or success. The project declares provisioning effects separately from read-only
readers. Omit the implementation or set `enabled: false` for passthrough.

Runnable bounded native checks against the actual shipping workflows:

```sh
python3 -B tests/probes/unified_measurement.py --binary /absolute/prifly-v0.13.85 \
  --package aif-classic --case repair --report /absolute/scratch/classic.json
python3 -B tests/probes/unified_measurement.py --binary /absolute/prifly-v0.13.85 \
  --package aif-profiled --case repair --report /absolute/scratch/profiled.json
python3 -B tests/probes/unified_fix_measurement.py --binary /absolute/prifly-v0.13.85 \
  --case repair --report /absolute/scratch/fix.json
```

These checks run real regression commands, Git changes, native Runs and artifact
exports. Their host assessments are scripted. Actual browser/live reader and
private consumer results are recorded separately in the change evidence.

## Task-aware acceptance Call

`aif-ui-ux` also publishes `review-for-change` and its `before-applicability`
point. The Call receives the original `task`, the fresh `implementation` carrier
and optional project `configuration`. A fresh read-only reader judges actual
code and callers, including server-rendered UI. A guard binds that judgement to
the task digest and a fresh Git candidate. Wrong-task or stale judgements create
a new `unknown` assessment; the original report remains unchanged.

```text
project measurement → capture → applicability → guard
                                                ├ required → configuration → quality
                                                ├ not-required → succeeded (no browser Attempts)
                                                └ unknown → partial (no browser Attempts)
```

Required review without a valid frontend configuration returns partial/blocked.
An unavailable browser cannot become not-required. `implementation.reports`
retains the original judgement, the guard assessment and any actual UI/UX reports.
Not-required means browser acceptance does not apply; it never means a browser passed.

A consumer selects the public Call at its own nested point:

```yaml
authoring: prifly-extension/5
imports:
  ui: aif-ui-ux
extensions:
  - id: acceptance
    point: before-verify
    call: ui.review-for-change
    output_bindings:
      verify-implementation: implementation
      fix-implementation: implementation
      clean-implementation: implementation
  - id: measurement
    point: {import: ui, export: before-applicability}
    step: measurement
    output_bindings:
      capture-implementation: implementation
      applicability-implementation: implementation
      guard-implementation: implementation
```

Both points bind task and implementation. The project measurement Step must
accept both exact shared schemas. Provisioning belongs to an earlier declared
external-write Step, or the measurement's own declared effects; readers remain read-only.
The setup helper supports this mode with `--applicability`; its launch accepts
typed task/implementation files and an optional configuration file.

Bounded native applicability probes use `product_check.py --applicability --case`
with `pass`, `backend`, `unknown`, `wrong-task`, or `missing-configuration`.
These scripted decisions test routing and correlation. Add `--browser-library`,
`--live-skills`, `--artifacts` and one explicit browser case for fresh live UI/UX readers.
The fixture applicability decision remains scripted; private acceptance uses an
actual fresh applicability reader. The minimal applicability wrapper has only
one root Call and does not declare resume: it has no accepted prefix before that
Call. Embed it after meaningful stages in a development consumer to use native
root continue. The low-level configure/quality example retains its existing resume.

[Core #15](https://github.com/StenHigh/prifly/issues/15): Pri-Fly v0.13.85 has a start refusal when composition and project worktree naming
are enabled together. Preparation succeeds, but start rechecks a different summary
version and returns `project_start_stale_launch` before creating a Run. The pilot
uses ordinary native worktree allocation in a separate source profile. It keeps
the reviewed digest check, exact staging base and primary project profile intact.
Do not claim the named-worktree path passed acceptance on v0.13.85.
