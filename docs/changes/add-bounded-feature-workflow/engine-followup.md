# E3 — Reviewed continue after resolved cancellation of an assisted writer

Status: prepared; reproduced on released **Pri-Fly 0.13.76**. This follow-up
does not change the engine as part of W3 and does not block ordinary feature
development, diagnostic partial continuation or cancelled read-only quality.

## Observed behavior

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

## Reproduction

In `StenHigh/prifly-aif-workflows`, run the isolated W3 probes:

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

Released Linux AMD64 binary SHA256:
`03ac382112a12001ea9e2a86e5a20db2d5e24ec79ce5339f6257c473d0f3322d`.

## Requested engine behavior and acceptance

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

W3 does not clear cancel_requested, reset/clean, synthesize a replacement source
or claim successful writer resume. Graceful accepted blocked/partial remains
the supported route when the host can still return its actual outputs.
