# W4 acceptance — verified integration handoff

Status: **implemented and qualified for local pilot**, unreleased project
example. No Core or existing package changes. Test binary: released Pri-Fly
**0.13.76**, Linux AMD64 SHA256
`03ac382112a12001ea9e2a86e5a20db2d5e24ec79ce5339f6257c473d0f3322d`.

Implementation: [example](../../../examples/verified-integration/README.md),
[integration guide](../../verified-integration.md), initial own components1.0.0.
Default `assess`; local merge and external Draft publication are explicit modes.

| Criterion | Evidence / qualification boundary |
|---|---|
| A1 — criteria/reports/source/target/final reader | Handoff bundles exact original W1 request bytes and reports; evaluator rechecks coverage/request digest and current clean source candidate. Integrated argv commands and final W1 code spot checks bind the exact merge candidate/target. Whole handoff digest includes criteria, mode and project policy; changed criteria cannot authorize an old accepted write. Final code reader is separately delivered. |
| A2 — actual merged behavior | Owned clone contains a deterministic merge commit of exact target/candidate; actual project argv command judges this tree. Real Git fixture changes value and consumer independently, merges without conflict, and returns AssertionError:4/needs_revision. Source alone passes; absence of a Git conflict does not produce ready. Operational merge failure is unavailable, distinct from exit1 textual conflict. |
| A3 — source/target movement and write guard | Freshness repeats source snapshot, target ref and integration snapshot before acceptance/operation. Local target is bare and update-ref uses exact NEW OLD CAS; racing foreign commit is preserved. Changed integrated bytes/criteria, moving source/target and stale reports stop acceptance. Editing source while a read-only reader is pending triggers native effect_not_permitted; probe preserves owner edit and cancels/cleans its own reader rather than reset or fake PASS. |
| A4 — project risk decision | Project policy names auth_money/migrations/dependencies/deploy/business_assumptions, matching changed paths and explicitly declared risks. Owner decision binds exact commits, policy digest, categories, reference and reason. Missing/stale decision gives owner_required; policy change invalidates approval. No hardcoded provider/business branch in Core. |
| A5 — distinct writes and reconciliation | Default assess only creates/checks/releases its own ephemeral copy. Local integration declares process external_write/reconcile_required and uses intent/ack journal + CAS; lost acknowledgement is inspected by actual ref without repeating write. GitLab has its own assisted external boundary and typed receipt; fail/no receipt after offline creation yields reconcile_required, retains session/journal and never creates again. No MR merge/push tail in generic local mode. |
| A6 — generic portion of #1 | Offline client fixtures model the issue's glab --draft behavior: one prefix, one creation on repeat, read-after-write recovery, addressed title repair, foreign source/MR and intervening human body/revision preservation. Generic example provides client protocol/reference algorithm and no credentials. Real GitLab CLI/API/remote lease/push/MR remain project qualification; issue #1 stays open. |
| A7 — one-input extension | Released compiler accepts standalone one-input insertion and rejects unknown producer, future producer (unavailable_output), unknown output, exact-schema mismatch and two bindings. Final assessment with several inputs is an explicit child graph. All three host skill roots compile the example. |
| A8 — canonical boundaries | Classic/profiled/fix/fanout/W1/W2/W3 bytes unchanged; derive_profiled unchanged. Correct one-input and id-tail naming documentation is added only to standalone guide/root README. Existing static/version/compile/compatibility gates are run against official stable. |
| A9 — full Runs and real host observation | Native fixtures exercise ready/local CAS, escalation/owner approval, conflict, semantic/unavailable checks, stale/moving code/target, spot-report invalidity, read-only cancellation/operator cleanup/reviewed continue, ordinary partial continuation and offline publication/reconciliation. Actual fresh Codex CLI final reader is recorded separately with exact unedited report and independent source/authority snapshots; no other-model or real-provider claim. |

## Boundaries

The source must be committed and clean. W3 pre-commit quality reports have a
different HEAD/index basis after commit; obtain fresh W1 evidence for the final
commit. Importing explicitly named artifacts binds their bytes/composition but
does not prove an authenticated original Run or truth of arbitrary observations.
Final reader reports remain host claims; freshness is cooperative, not atomic
filesystem isolation. The local ref change alone is atomic CAS.

The example targets POSIX `/tmp` sessions and local bare SHA-1 Git repositories.
It does not update a live target checkout, fetch a remote target implicitly,
install dependencies, provision a browser or provide production credentials.
Project commands are separately reviewed; extra service/database writes need
their own project contract. Source/index/dirty owner work is preserved.

Fresh CLI observation proves an actual separate delivered session, not a different
model. Optional unavailable model mapping is visible as warnings under the explicit
ignore/stop policy. Actual Claude and private consumer/provider qualification are
not claimed. No matched classic benchmark or savings measurement was run.

Cancellation of a non-retryable writer may retain the Core boundary documented
in [E3](../add-bounded-feature-workflow/engine-followup.md). W4 does not clear
cancel_requested, reset source or fabricate a successful writer continuation.
Read-only cancellation and ordinary partial are qualified separately. Unknown
external outcome preserves evidence; operator inspects/attests before retry.

## Recorded evidence

- [runtime-results.json](runtime-results.json): 27 complete native cases (25 base
  cases plus two host variants), including intended checkout_dirty and
  effect_not_permitted refusal/cancellation, ordinary partial/cancel continuation,
  exact merged semantic regression and unknown-publication re-entry. Passing the
  matrix means the expected outcomes were observed, not 27 successful merges.
- [compile-results.json](compile-results.json): 13 step/workflow definitions on
  codex-cli/codex-app/claude-code, standalone one-input insertion and five named
  semantic refusals.
- [regression-results.json](regression-results.json): W4 unit18, static7/version3/
  derive, compile100 existing definitions across7 packages and existing compatibility.
- [live-observations.json](live-observations.json): actual Codex CLI0.162.1 fresh
  session on final worker/bridge, exact unedited report/submission, source and
  authority unchanged; final assessment ready/succeeded with visible unavailable
  alternate-model warning under explicit ignore policy. Commands and code were
  actually inspected; another model is not claimed. Raw events and copied
  submissions remain private under `/tmp/w4-current-scoped-reader`.
- [protocol-negative.json](protocol-negative.json): actual earlier reader added
  command evidence to a code spot check. The unchanged report correctly ended
  partial/unavailable; it is not PASS. Own bridge clarified every evidence item
  must preserve the declared method. W1 evaluator/schema were not relaxed.
- [final-bridge-direct.json](final-bridge-direct.json): same native direct case
  after that textual method clarification; graph/schema/effects/program unchanged.
  [source-boundaries.json](source-boundaries.json) pins exact current bytes and
  all310 existing package files unchanged. CI repeats the full suite on the
  implementation commit.

Within one handoff, exclusive creation of its deterministic owned session prevents
new prepare/continue while a previous unknown session remains. This is qualified
within the POSIX temp store lifetime; `/tmp` is not a durable production ledger
through reboot or OS cleanup. Project provider lease/receipts need persistent
storage for those lifetimes. A revision-less provider cannot perform automatic
title repair; unconditional update is not accepted as CAS.

Implementation committed/pushed to main as
[`b5f81614dfc77715ad76420227f7b89f319c80b0`](https://github.com/StenHigh/prifly-aif-workflows/commit/b5f81614dfc77715ad76420227f7b89f319c80b0).
[CI](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/38663568633)
completed **success** against latest stable Pri-Fly0.13.76: all existing gates,
new W4 unit18, three-host compile/extension negatives and runtime27, plus W2/W3
actual-browser checks. [Recorded CI result](ci-results.json) pins the exact
implementation commit; documentation bookkeeping leaves executable bytes unchanged.
No tag/catalog release or successful production GitLab write is implied.
