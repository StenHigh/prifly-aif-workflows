# W3 acceptance — separate small feature workflow

Status: **implemented and qualified for pilot**, unreleased; A8 forced-writer
cancellation remains the explicit deferred E3 portion. No tag/catalog
publication. Released test binary **Pri-Fly 0.13.76** Linux AMD64 SHA256
`03ac382112a12001ea9e2a86e5a20db2d5e24ec79ce5339f6257c473d0f3322d`.

Package [aif-feature](../../../aif-feature/README.md), initial **1.0.0**.
Existing classic/profiled/fanout/fix/W1/W2 source bytes remain unchanged.

Implementation is committed and pushed to main as
[`b7e071e25fd52b9347f52b12adfa2990885a4786`](https://github.com/StenHigh/prifly-aif-workflows/commit/b7e071e25fd52b9347f52b12adfa2990885a4786).
The complete [CI run](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/38653153795)
finished **success** against latest stable Pri-Fly 0.13.76: all existing gates,
W3 install/update and 35 runtime cases, W2 actual browser cases and three W3
actual-browser scenarios. [Recorded CI result](ci-results.json) pins this commit.

| Criterion | Evidence / current boundary |
|---|---|
| A1 — separate package/launch/input/decisions | `aif-feature:package/feature`, launch aif-feature; typed task, backend/frontend profiles, plan_tests/plan_constraints/plan_retention. Local catalog add/update preserves extend/project and refuses project_workflow_modified. Preview exact task bytes then native reviewed prepare; no auto selector/start. |
| A2 — native fast plan/owner guard | AI Factory2.19.0 plan/implement plus TASK-FORMAT and logging/progress references read with matching recorded hashes. Native exact_file capture/materialisation; typed ready result gates implement. Conflict/too-large stops preserve diagnosis and explicitly non-executable BLOCKED snapshot (released capture is unconditional). Foreign PLAN yields workspace_tree_output_exists; no execution/deletion. A real planner/implement conflict was detected and stopped, then planner received the downstream logging guide. |
| A3 — backend/frontend commit | Released synthetic backend and frontend finish locally; actual Playwright direct frontend passes. No browser stages on backend; frontend requires both UI/UX and owned environment. Final scoped real frontend also finishes locally; actual reports and receipts in final-live-observations.json. |
| A4 — complete new quality after repair | Synthetic repairs from checks/security/review/UI/UX all repeat every enabled reader on new candidate. Actual browser separately reproduces UI overflow and UX save failure, scoped repair and full fresh round. W1 request/round/candidate/coverage and W2 scenarios/cleanup remain authoritative over usable session verdicts. |
| A5 — bounded work/partial exhaustion | Default3 full rounds, max8, no repair on final failed round. Max-budget fixture executes8 full backend rounds/7 repairs, partial with evidence/work. Frontend bound14 per repair round, max113 acceptance (111 rounds+guard/commit)/117 root; declared114/128 steps, sequential1, depth4. |
| A6 — unavailable/owner blocker | Backend required-unavailable, optional policy stop and frontend unavailable preserve work and skip repair/commit. Aggregate owner decision outranks a defect in another lens. Genuine live missing-prerequisite observation is recorded separately. |
| A7 — no silent large-task escalation | Too-large/conflict/repair-too-large return diagnostic partial and actual work, without a classic Run or bug skill. One short upstream inline repair stays within original feature scope. |
| A8 — partial/read-only cancel/chained resume | Same-version blocked/cancelled quality/chained and frontend UI cancellation+operator cleanup continue with original base, one claim, decisions and preserved owner edits; full quality repeats, including commit-stopped continuation with an intervening edit (one acceptance call). Effective accepted configure change refuses recover_prefix_changed without source edit. **Forced non-retryable writer cancellation is a current Core boundary:** even after inspected resolve it remains failed/cancel_requested and prepare refuses recover_source_unsettled. This is a tested negative case, not a successful writer resume; [E3 prepared issue](engine-followup.md). |
| A9 — native bytes/retention/local commit | Default captured native plan bytes/progress remain in artifacts; retained tracked plan/progress passes quality/commit and is preserved. Root partial emits the actual diagnostic/progress manifest. No push/MR/merge, no deletion of other documents; exact candidate guard before commit. |
| A10 — independent gates/provenance | All7 packages compile100 sealed step/workflow definitions /67 source steps, profiles on3 hosts and named negatives; static/version/derive and existing compatibility pass. Local install/update and meaningful W3 unit negatives pass. Synthetic/actual-browser/real-model observations are explicitly distinguished; complete matrix/live evidence and regressions are finalized below. Published install remains a future release check. |

## Scope and limitations

The backend fixture is one stdlib greeting callable plus its unit test. The
frontend fixture adds confirmation to an existing local notes form, with fixed
desktop/mobile scenarios and ephemeral page state. Synthetic hosts submit
explicit test reports; browser fixtures execute actual Playwright1.64.1 /
Chromium156.0.8078.4 with deterministic assertions, not LLM visual judgments.
Real CLI hosts use the actual pinned skills and exact unedited submissions.

Fresh session IDs establish separate deliveries without author conversation;
no different model is asserted. Optional unavailable model mapping is visible
under ignore/stop policy. Gate prose/browser observations remain host claims;
Git snapshots are cooperative freshness, not atomic isolation.

Forced writer cancellation requires future Core support for a reviewed resume;
W3 does not implement it or bypass the refusal. A8 is qualified for partial and
read-only cancellation, with this explicit deferred portion. Graceful writer
blocked/partial is distinct from killing an outstanding non-retryable writer.
Private consumer/PHP stack and actual Claude live actors are not qualified by
these fixtures; three-host compilation/synthetic runtime is a different claim.

No time/token savings relative to classic are claimed. Task size, route,
per-Attempt token usage and elapsed time are observations only; classic has not
run the same tasks under the same settings/environment, and concurrent probe
load affects timings. Full A8 and published installation cannot be advertised
as complete before their separate engine/release work.

## Recorded final evidence

- [runtime-results.json](runtime-results.json): 35 released-runtime cases, three
  hosts, complete loops and truthful named negative forced-writer boundary.
- [compile](compile-results.json), [compatibility](compatibility-results.json),
  [install/update](install-results.json), [regressions](regression-results.json).
- [browser-results.json](browser-results.json): 3 complete actual-browser cases;
  15 [screenshots/observations](browser-artifacts/) for direct, UI overflow repair
  and UX confirmation repair, both complete fresh quality rounds.
- [final-live-observations.json](final-live-observations.json): final coherent
  frontend Run and genuine required-prerequisite unavailable → owner supplies
  prerequisite → reviewed full quality continuation. 19 unique fresh CLI sessions,
  exact unedited reports, source partial + final succeeded, original base/one
  claim/owner work and final actual Git implementation checked. Owned environment
  released, fixture claims/monitor/temp data cleaned. UI/UX real screenshots in
  [live-browser-artifacts](live-browser-artifacts/). Sandbox/automatic review
  retained, exact fixture directory granted; no full-access bypass.
- [live-observations.json](live-observations.json): earlier actual backend direct,
  real scoped inline repair with actual failing tests then all fresh readers,
  graceful blocked writer continuation. Their precise earlier contract scope is
  recorded; no claim that they used the final whole-root build. Programs/reader/
  repair behavior remains the same; final source compile/runtime and final live
  Runs verify the finalized composition.
- [protocol-negative.json](protocol-negative.json): actual unedited rejected/
  blocked prototypes and own bridge/fixture corrections, never counted as PASS.
- [source-boundaries.json](source-boundaries.json): exact workers and unchanged
  existing folders. W3 unit8/static7/version3/derive checks PASS.

Native/browser scheduling is now explicit: native Tasks finish code and available
unit/static tests; independent acceptance and actual UI/UX await the later owned
quality environment. No mandatory criteria are silently marked done. Product
policy/session fields must agree with the outer owner choice; contradictory
values are rejected rather than overridden.

Final native program SHA and the source-bounds file identify the exact current
worker. No comparable classic benchmark was run. Reported CLI token usage and
elapsed time remain observations under concurrent fixture load, not a claim of
less cost or faster development. Tag/catalog/published install and E3 are separate
work; actual private consumer/PHP stack and live Claude remain unqualified.
