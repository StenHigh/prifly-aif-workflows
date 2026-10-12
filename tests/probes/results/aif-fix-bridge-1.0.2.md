# aif-fix 1.0.2: verdict and gate status

Tested on released Pri-Fly **0.13.76**, darwin/arm64, binary SHA-256
`5df5aceccde63c173d3f38f20426eb9dd131e6c3b0f6511a99002ad874a49f00`.

The three reader bridges now distinguish report usability from check results.
An established unavailable required dependency is a usable `pass` report with
`gate.status=blocked` and command/unrun-check evidence. It stops the root
`partial`, preserving the gate, without repair or commit. Verdict `blocked`
is reserved for an Attempt unable to produce a usable assessment; its required
diagnostic gate is still supplied. Usable `needs_revision` follows the same
routing. Required blocked checks cannot be relabelled passed/warnings.

Only the three bridge contexts, their three steps, the two quality workflows
and package/root identities moved to 1.0.2. Graph routing, effects, result schemas,
warmup/build and classic/profiled/fanout bytes did not change.

## Own checks

- 10 static tests, derived profiled check and diff check: PASS.
- `tests/verify.py --binary <released>`: PASS, four packages, 59 compiled
  components and 34 step files; compile/import separation checked.
- `tests/compatibility.py --binary <released>`: PASS, five launches and four
  distinct builds in one authority.
- `tests/probes/fix_check.py --binary <released>`: all 28 scenarios PASS.
  Includes direct on three hosts, fix-plan escalation/capture/materialisation,
  repair at all three gates and the limit, owner/foreign-plan stops,
  decision wait/decline, effects/output refusals and chained resume.
- Usable `pass` plus blocked gate at checks/security/review: exact source/root
  gate preserved, no repair/commit before resume; each resumes to succeeded.
- Three additional runs use usable `needs_revision` with the same blocked gate
  instead of pass, through the existing host's assertions: PASS, then succeeded
  on resume. See [data](aif-fix-bridge-1.0.2-needs-revision.json).
- Empty `answered_questions.answer` is refused at the expected pointer;
  descriptive text is accepted while typed short_checks/ledger stay `""`.
  The measurement ends ready after that accepted submit; cleanup cancels it.
- Classic pass, blocked, blocked-resume and cancelled-resume: PASS within the
  existing probe's boundary through the next handoff.

## Contracts and resume

A local Git origin holds the released v1.51.1 folder and the new working-tree
folder under separate fixture tags. Installation and update use the real
`project workflows add/update` commands, not direct edits of installed state.

Partial on blocked quality → update 1.0.1 to 1.0.2 → prepare: accepted, frontier
`quality`, reuse `warmup/build/fix-task/fixed`. Reviewed continue runs fresh
checks/security/review and local commit, ending succeeded. No repeated fix,
one claim generation 1→2, original base and dirty/untracked owner work preserved;
source version/tree unchanged during prepare. See
[data](aif-fix-bridge-1.0.2-upgrade-blocked-quality.json).

A separate source accepts quality, then the synthetic commit returns no_work
with owner_required instead of performing a commit. The root ends partial at
commit. After the same actual update, default prepare refuses
`recover_prefix_changed` at `quality`, without changing source version/tree.
Reviewed `--from-stage quality` reuses warmup/build and repeats
checks/security/review/commit through succeeded. One claim generation 1→2,
base and both owner-work hashes preserved. See
[data](aif-fix-bridge-1.0.2-upgrade-accepted-quality.json).

An exploratory cancellation after quality, before execution of the delivered
workspace-write commit, needs native attestation `not_applied`. Core then settles
failed with an active cancellation; prepare returns `recover_source_unsettled`.
This checks a source-state guard, not changed-prefix recovery. No blind retry or
storage edits were used; the exploratory fixtures were cleaned.

## Boundaries

These are synthetic-host tests with real released CLI, Git, commands, native
captures and claim transfer. They do not establish a new LLM observation,
independent reviewer session/model selection, external product QA or a measured
speed/token advantage. The live 1.0.1 pilot is separate evidence:
[issue #4](https://github.com/StenHigh/prifly-aif-workflows/issues/4#issuecomment-6133548812).
The 1.0.0→1.0.1 full warmup replay remains outside this test.

Every temporary Run, claim and monitor entry created by these tests is cleaned.
[Runtime matrix](aif-fix-bridge-1.0.2-runtime.json),
[gate summary](aif-fix-bridge-1.0.2-gates.json).
