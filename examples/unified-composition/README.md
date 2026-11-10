# Unified composition on released Pri-Fly v0.13.90

The public UI/UX provider remains 2.0.0. Its task-aware Call uses frozen task1.1.0.
Classic/profiled/fix in main are 3.0.0 and use owned `schema_task` with a project limit.
These task types have different exact references. A public task-aware UI/UX Call
from 2.0.0 cannot receive the owned task of a 3.0.0 consumer.

All examples require the explicit [shared schema dependency](../../contracts/README.md).
Use checked source `72eb8861263d15079d767c6c6106e8c240f738d0` for `contracts/`, `tools/` and helpers.
[Checkout commands](../task-description-limit/README.md#подготовка-и-самостоятельный-запуск) use that exact commit.
Catalog installation copies only the selected package folder. Old installed extensions
and sealed Runs are not migrated automatically.

| Recipe | Task contract | Consumer |
| --- | --- | --- |
| Public configure → quality | Configuration input; no root task port | Generated UI/UX wrapper below |
| Nested measurement on classic/profiled/fix3.0.0 | Owned `schema_task` | Current packages; Core0.13.90+ |
| Public review-for-change | Frozen task1.1.0, limit12 000 | Compatible2.0.0 consumer from v1.57.0, or its own frozen wrapper |

For task-aware review/UIUX inside classic/profiled3.0.0, use the separate
[W6 project-copy recipe](../review-uiux-extensions/README.md). It binds copied
definitions to the caller's `schema_task`.

## Public UI/UX components

`aif-ui-ux` folder `/3` publishes the `configure` Step and the `quality` workflow.
The standalone launch remains available. This example imports those components
through `/5`; it does not copy the provider's private stages or programs.

Set the absolute paths below. `REPOSITORY` is an initialized Git project with
its project profile and real host skills. `AUTHORITY` is its existing authority.
`WORKFLOW_SOURCE` is a separate checkout of the exact source above. Choose a fresh
`SCRATCH` directory. Supply the project's real configuration and executable bindings.

```sh
PRIFLY_BIN=/absolute/path/to/prifly-v0.13.90
REPOSITORY=/absolute/project
AUTHORITY=/absolute/authority
WORKFLOW_SOURCE=/absolute/prifly-aif-workflows-source
SCRATCH=/absolute/fresh-scratch
CONFIGURATION=/absolute/configuration.json
mkdir -p "$SCRATCH"

"$PRIFLY_BIN" project workflows add StenHigh/prifly-aif-workflows \
  --path aif-ui-ux --ref 72eb8861263d15079d767c6c6106e8c240f738d0 --repository "$REPOSITORY"
python3 "$WORKFLOW_SOURCE/tools/install_composition_contracts.py" \
  --binary "$PRIFLY_BIN" --project "$AUTHORITY"
python3 "$WORKFLOW_SOURCE/examples/unified-composition/setup.py" \
  --repository "$REPOSITORY"
```

Review and commit the generated package and profile changes. Ensure the project
is clean before preparing a worktree Run. Configure the package's Python
executable and environment sources before prepare, as described in the UI/UX README.

```sh
"$PRIFLY_BIN" --project "$AUTHORITY" project compile \
  --repository "$REPOSITORY" --package ui-ux-composed --host codex-app \
  --output "$SCRATCH/compiled"
"$PRIFLY_BIN" --project "$AUTHORITY" project questionnaire \
  --repository "$REPOSITORY" --launch ui-ux-composed --host codex-app \
  --workspace worktree --input configuration="$CONFIGURATION" \
  --allow-execution --prepare --json > "$SCRATCH/prepare.json"
cat "$SCRATCH/prepare.json"
```

`configuration.json` follows `aif-ui-ux/schemas/configuration.yaml`: task/candidate
basis, explicit applicability, requiredness, viewports, scenarios and an owned
environment contract. It is project input, not a universal default.

Review the complete summary and its execution effects. Set `REVIEW_DIGEST` to
its exact `review_digest`. Then start with the same inputs and options:

```sh
REVIEW_DIGEST='sha256:REPLACE_WITH_REVIEWED_PREPARE_DIGEST'
"$PRIFLY_BIN" --project "$AUTHORITY" project start \
  --repository "$REPOSITORY" --launch ui-ux-composed --host codex-app \
  --workspace worktree --input configuration="$CONFIGURATION" \
  --allow-execution --expected-launch-digest "$REVIEW_DIGEST" --json \
  > "$SCRATCH/start.json"
cat "$SCRATCH/start.json"
```

For a supported stopped Run, take its actual ID from `start.json`. Prepare a
continuation with the same launch and no new configuration input:

```sh
RUN_ID='run:REPLACE_WITH_ACTUAL_SOURCE_RUN_ID'
"$PRIFLY_BIN" --project "$AUTHORITY" project continue \
  --repository "$REPOSITORY" --launch ui-ux-composed --source-run "$RUN_ID" \
  --host codex-app --allow-execution --prepare --json > "$SCRATCH/continue.json"
cat "$SCRATCH/continue.json"
```

Review the recovery frontier, inherited prefix and effects. Set the new top-level
digest and continue:

```sh
CONTINUE_DIGEST='sha256:REPLACE_WITH_REVIEWED_CONTINUE_DIGEST'
"$PRIFLY_BIN" --project "$AUTHORITY" project continue \
  --repository "$REPOSITORY" --launch ui-ux-composed --source-run "$RUN_ID" \
  --host codex-app --allow-execution --expected-launch-digest "$CONTINUE_DIGEST" --json
```

This root can replay its quality Call from a supported accepted prefix.
A nested resume stage is not supported. A genuine empty-prefix or freshness
refusal remains a refusal; do not substitute a different launch to bypass it.

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

For these 3.0.0 packages, a project Step that consumes task binds it to `{{schema_task}}`.
The project Step binds `implementation` to `{{contract_schema_implementation}}`
and emits that same schema on every success path. It preserves original report
refs and appends newly published report refs. Each ordinary ArtifactRef has
`artifact_id`, integer `revision` and `digest`. A ref does not attest applicability
or success. The project declares provisioning effects separately from read-only
readers. Omit the implementation or set `enabled: false` for passthrough.

Runnable bounded native checks against the actual shipping workflows:

```sh
python3 -B tests/probes/unified_measurement.py --binary "$PRIFLY_BIN" \
  --package aif-classic --case repair --report /absolute/scratch/classic.json
python3 -B tests/probes/unified_measurement.py --binary "$PRIFLY_BIN" \
  --package aif-profiled --case repair --report /absolute/scratch/profiled.json
python3 -B tests/probes/unified_fix_measurement.py --binary "$PRIFLY_BIN" \
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

The following nested recipe requires a compatible **2.0.0 consumer from v1.57.0**
with frozen task1.1.0. Install that pinned consumer explicitly if you use this recipe.
It does not apply to classic/profiled/fix3.0.0 or inherit their task limit.
The standalone `setup.py --applicability` wrapper also uses frozen task1.1.0.

A compatible consumer selects the public Call at its own nested point:

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

Both points bind task and implementation. In this 2.0.0 recipe, the project Step
binds task to `{{contract_schema_task}}` and implementation to `{{contract_schema_implementation}}`.
Its task limit remains12 000. The 3.0.0 measurement recipe above uses `{{schema_task}}` instead. Provisioning belongs to an earlier declared
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

[Core #15](https://github.com/StenHigh/prifly/issues/15) affected the combined
composition/naming path on v0.13.85. It is fixed in v0.13.86. The published86
binary passed a real named public-import/typed-carrier/parallel Run; see
[Core acceptance](../../docs/changes/adopt-unified-composition-v5/core-0.13.86.md).
The earlier pilot's ordinary-allocation result remains historical85 evidence.
