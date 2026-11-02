# Candidate acceptance on published v0.13.85

These are separate checks of an unpublished downstream candidate. The active
catalog retains its published pins. The exact release binary SHA256 is
`d512311554b31f469c912b3e1a2d65128edf99362d8ab29314c91448134fe954`.

- Unit checks: 122 passed. Versions, folder structure, reproducible profiled
  derivation and exact schema locks passed.
- Native verify: 8 packages, 132 components, 88 Steps and 3 hosts passed.
  Compatibility: 5 launches and 4 distinct builds passed.
- Native classic/profiled repair cases measured both candidates and delivered
  the current reports to both readers. The fix repair case preserved original
  failed-before and passed-after report refs.
- The vendored extension matrix compiled 18 cases and refused 8 negative cases.
- Task-aware public imports exercised backend, wrong-task and missing-config
  routes. Those routes made no browser Attempts. Wrong-task preserved the
  original report bytes and returned an uncertain decision.
- A separate live public-import fixture used Chromium and two fresh Codex UI/UX
  sessions. It succeeded and released its owned fixture environment. Its
  applicability decision was scripted; it was not private product acceptance.
- A private backend pilot began from freshly fetched staging. Its ordinary
  procps baseline passed. An actual BusyBox selector reproduced the fault:
  2 failed tests, 10 assertions. The portable fix passed both BusyBox and
  procps: 2 tests, 18 assertions each. Fresh applicability sessions correctly
  selected no browser work for this CLI regression.

An independent private review found a consumer installation error: merging the
new additive schema bundle left 16 redundant schema files. The repair replaced
only the owned bundle, retained strict lock checks and passed installation in a
fresh disposable authority. This was not a native schema compatibility defect.

Core #15 remains open: composition with project worktree_naming cannot start
on v0.13.85. Ordinary allocation passed in a separate pilot source profile.
The delivered global naming policy remains intact. The named path and full
product suite are not qualified by these results.

Minimal task-aware wrappers do not declare resume: their only root stage is a
Call, so they have no accepted prefix before a failed nested quality attempt.
The low-level configure/quality example retains its supported continuation.

The private native Run completed successfully, including an actual Draft MR
program targeted at the same freshly checked staging branch. The server
confirmed Draft state and exact committed head. A final captured snapshot
covered 123 changed paths. Its selected checks passed: strict schema closure,
actual native compile, delivery shell syntax, 33 evidence validator self-checks,
and BusyBox/procps focused tests. Before/after snapshots matched. Original
failed/pass reports remained historical; the process receipt did not invent
native PHPUnit counts. The owned private environment and native claim were
released. Private repository URLs and task details are intentionally omitted.

This candidate is retained in a local commit. Publication needs a separate
release decision that accounts for Core #15. Existing Runs, published schema
identities and active catalog pins retain their original meaning.
