# E3 — Reviewed continue after resolved cancellation of an assisted writer

Status: **CLOSED — [Pri-Fly #13](https://github.com/StenHigh/prifly/issues/13)**,
fixed in released **Pri-Fly 0.13.81**, independently checked2026-10-19.
Consumer positive recovery uses unchanged `aif-feature@1.2.3`; Core, server,
canonical classic/profiled and all shipping package bytes are unchanged here.

## Current supported route,0.13.81+

- Unknown writer effects still refuse `recover_source_unsettled`. Stop the
  actor and inspect its actual work before attesting applied/not_applied.
- After owner resolution, same-launch `project continue --prepare` identifies
  `frontier_action: execute`. Prepare preserves source version/state, Run
  inventory, claim, candidate/index/HEAD, owner and partial-plan bytes.
- The new reviewed Run repeats writer and following quality. The original
  Run keeps failed/outcome:null/cancel_requested and resolution diagnostics;
  resolution is not a successful implementation or StepResult.
- An occupied producer `PLAN.md` still gives `workspace_tree_output_exists`.
  The fixture owner preserves/moves only its own partial file outside the
  candidate, then prepares recovery from the **current claim owner**. No
  implicit deletion or acceptance of partial plan bytes occurs.

Verified positive cases: implement/not_applied→succeeded (2 Runs),
plan/applied→occupied-path refusal→explicit owner move→succeeded (3 Runs),
read-only cancellation→succeeded (2 Runs). One workspace claim is preserved.
Synthetic synchronous actors and actual CLI/programs/Git; live models/private
providers remain outside this qualification.

[Results and supporting release notes](../engine/release-0.13.81.md),
[current prepare/start recipe](../../../examples/small-feature/README.md#продолжение-после-отмены-пишущего-шага).
Current probes require0.13.81+ and assert successful recovery:

```sh
python3 -B tests/probes/feature_check.py --binary /absolute/released/prifly --case implement-cancel --report /tmp/e3-implement-81.json
python3 -B tests/probes/feature_check.py --binary /absolute/released/prifly --case plan-cancel --report /tmp/e3-plan-81.json
python3 -B tests/probes/feature_check.py --binary /absolute/released/prifly --case cancel-resume --report /tmp/e3-read-only-81.json
```

## Historical boundary on0.13.80

Both `plan-cancel` + inspected `applied` and `implement-cancel` + inspected
`not_applied` still refuse `recover_source_unsettled` after resolution:
Run failed, outcome:null, cancel_requested:true, no uncertain Attempts.
Resolve preserves work; prepare preserves source Run version/state, candidate,
owner/plan bytes and Run inventory. The `cancel-resume` read-only control
continues and succeeds with one workspace claim. All fixtures/claims/private
HOME cleaned; actors synthetic, native CLI/Git real. No package/Core changes.
[Native states/evidence](../engine/E3-writer-cancellation-0.13.80-results.json),
[published issue body](../engine/E3-reviewed-writer-cancellation.md).
Binary SHA256: `b5bc6d33206281c52afd3b17827e8cd416812d223d091f699d7883a382037a82`.

The original observation was on0.13.76. Historical recheck:

2026-10-16: rechecked `implement-cancel` on released **0.13.77**. Inspected
`not_applied` resolution still ends at `recover_source_unsettled`, with work/claim
preserved and fixture cleanup successful. No issue was published by this check;
`plan-cancel` was not rerun. Closing parallel cancellation #6 does not close E3.

## Observed behavior on0.13.76–0.13.80

Root declares resumable partial/rejected/cancelled. Its assisted plan/implement
worker is workspace_write/retry_class:never. Cancelling a handed-out writer
correctly gives an uncertain obligation and `recovery_required`; no blind retry
is allowed. After the synchronous host returns, the fixture owner inspects and
preserves exact local bytes and attests `run resolve --outcome applied` for the
producer that wrote partial bytes, or `not_applied` for the consumer cancelled
before any actor write. Engine-materialized input bytes remain preserved.

The Run then becomes **failed**, outcome:null, with `cancel_requested:true` and
corresponding `resolved_applied` / `resolved_not_applied` diagnostic. Reviewed `project continue --prepare` still
refuses **recover_source_unsettled**, even though the obligation was resolved.
Source/tree remain unchanged by prepare. Both producer plan and consumer
implement reproduce this; read-only quality cancellation resumes normally.
The guard in recoveryFrontier rejects CancelRequested before selecting the
settled failed frontier. This may be an intentional current boundary; the issue
requests a supported reviewed route, not removal of cancellation safeguards.

## Historical reproduction

Use `StenHigh/prifly-aif-workflows` at pinned source
`081931fb395d09311a49cb5037f0531db18c9c09` and official0.13.80 for the old
negative probes. The current working-tree probes instead expect the fix.

```sh
python3 -B tests/probes/feature_check.py --binary /absolute/released/prifly --case plan-cancel
python3 -B tests/probes/feature_check.py --binary /absolute/released/prifly --case implement-cancel
```

The fixture starts an owned temp authority/worktree, prepares and starts the
feature launch, reaches the writer, cancels it, observes recovery_required,
resolves only that returned fixture writer, and prepares continue. Tests expect
the named refusal, assert one claim/work preservation and read-only prepare,
then clean their own Run/claim/monitor/temp data. A passing probe means the
**negative boundary was reproduced**, not that writer continuation succeeded.

Historical0.13.76 Linux AMD64 binary SHA256:
`03ac382112a12001ea9e2a86e5a20db2d5e24ec79ce5339f6257c473d0f3322d`.

## Original requested engine behavior and acceptance

Offer an explicit reviewed recovery after all obligations of the cancelled
writer are owner-resolved. Do not infer successful implementation from an
applied attestation and do not auto-run the next stage. Replay the appropriate
writer/root call with original base, claim and sealed decisions, preserving
existing bytes and native materialisation/ownership checks.

- Before resolution, continue refuses with a precise unresolved obligation.
- After inspected resolution, prepare can identify a valid replay boundary,
  without editing the source or starting work.
- The reviewed continuation repeats that writer and all affected quality; old
  PASS does not survive a new edit.
- An interrupted producer's occupied unsealed plan path is still refused;
  preserve it and name the exact owner action needed. No automatic deletion.
- Effective prefix mismatch keeps the named refusal and work untouched.
- Validate applied/not_applied, producer/consumer, unresolved external effects,
  chained recovery and repeated cancellation on supported hosts.

W3 does not clear cancel_requested, reset/clean or synthesize a replacement
source. Successful writer recovery now uses the0.13.81 reviewed native route
described above. Graceful accepted blocked/partial remains supported.
