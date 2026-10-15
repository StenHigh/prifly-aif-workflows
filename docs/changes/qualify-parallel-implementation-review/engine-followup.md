# E4 / W5 — Parallel read-only cancellation cannot settle after one branch completed

Status as of 2026-10-16: **closed — fixed in released Pri-Fly 0.13.77**;
[Pri-Fly #6](https://github.com/StenHigh/prifly/issues/6).
[Requalification](release-0.13.77.md) checks terminal cancel, native release and
full-round reviewed replay. Below is the historical reproducer on **0.13.76**;
its stopping/refusal expectations are no longer the current test contract.
No engine changes are included in W5. This remains distinct from W3's E3
cancelled-writer follow-up, which has not been requalified by this check.

## Concrete trigger and observed result

A claimed worktree has two independent assisted read-only Attempts (effects none,
retry pure). One candidate/request feeds both through `parallel`, `join all`,
`selection all`, `remainder wait`. The first actor submits a valid W1 report;
its evaluate step and branch finish. The sibling still awaits its report.
Both synthetic actors have returned; no OS process or external write remains.

The owner runs `run cancel`, then `run drive`:

- The remaining reader Attempt becomes cancelled; every Attempt is settled.
- Drive exits 2 with **invalid_input**, without a field-level violation.
- Run remains **stopping**, `cancel_requested:true`, outcome absent. Repeated
  drive returns the same error. `run next` still offers action cancel for a
  workflow invocation.
- `claim release` exits 2 with **claim_run_active**.
- Reviewed `project continue --prepare` exits 3 with
  **recover_source_ineligible**, because the source never reaches cancelled.
- Candidate/owner bytes remain intact; no stale PASS or repair is accepted.

This reproduces **without any source edit**. A second case changes an owner file
while the last reader is active: native submit correctly refuses
**effect_not_permitted**; cancelling that delivery then produces the same stop.
The freshness guard is correct; the defect is failure to finish cancellation.

The final fixture includes an inner call/on_error wrapper. It supports ordinary
partial and timeout replay, but cannot fix cancellation settlement. Removing
error handling gives recover_frontier_unsupported; root-only handling gives
resume_frontier_ambiguous. Those separate authoring negatives have a package
solution and are **not** requests for new engine operators.

## Reproduce

From `StenHigh/prifly-aif-workflows` at the W5 implementation commit:

[Exact implementation 776746487859](https://github.com/StenHigh/prifly-aif-workflows/commit/7767464878593481818d9f3a7f84017485e42391),
[full qualifier CI success](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/38721905656).
Success of this gate means the named negative was reproduced, not fixed.

```sh
python3 -B tests/probes/parallel_check.py --binary /absolute/released/prifly \
  --case cancel-after-first --report /tmp/w5-cancel.json --keep
python3 -B tests/probes/parallel_check.py --binary /absolute/released/prifly \
  --case during-reader-edit --report /tmp/w5-edit-cancel.json --keep
```

`--keep` prints the owned fixture path and retains the authority/worktree for
native inspection; the fixture unregisters only its own monitor entry. Omit
`--keep` for CI: after recording this named negative, the harness removes its
entire owned temporary sandbox. This physical test teardown is **not** a
successful native claim release, and must not be used on a consumer project.
No force-release, state edits, reset, clean, replacement source or forged reader
report is used. No browser, credentials or external provider is needed.

The minimal graph overlay is `tests/probes/parallel-review/`, assembled with
unchanged W1 workers/schemas by `tests/parallel_fixture.py`. Default graph compiles
8 sealed workflow/step definitions. The probe uses the public native CLI only.
The case exits zero when it reproduces the **negative boundary**, not successful
cancellation or recovery. The full W5 runtime report preserves exact diagnostics.

Binary SHA256:
`03ac382112a12001ea9e2a86e5a20db2d5e24ec79ce5339f6257c473d0f3322d`.

## Expected behavior / acceptance

Use the existing parallel/cancel/recovery contracts to finish the stop once all
real obligations are settled. Do not weaken read-only guards or infer report
success from cancellation; no new model router/parallel operator is requested.

- Cancel before reports, after either branch settles, and after both settle.
- Cover first branch succeeded/partial/failed and reverse completion order;
  include read-only source drift and refused effect_not_permitted submission.
- While a real obligation remains, keep it visible and refuse unsafe continuation.
- Once all obligations settle, Run reaches terminal cancelled instead of
  stopping/invalid_input; preserve source, index, owner files and reports.
- When abandoning that stopped fixture, native claim release succeeds.
- When retaining its claim for work, reviewed continue repeats the complete root
  quality call and all enabled readers with a fresh candidate; late reports from
  the cancelled delivery cannot satisfy new Attempts.
- Keep timeout/partial and existing writer uncertainty behavior unchanged.

Until this is qualified, W5 does not enable parallel implementation review in
`aif-feature`. Classic/profiled and all shipping package bytes remain unchanged.
