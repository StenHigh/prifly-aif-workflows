# AI Factory bug fix workflow

`aif-fix` is a separate package/launch. The user chooses it in `prifly-run` for
a concrete wrong behavior; classic/profiled keep their development graphs.
Pri-Fly 0.13.76 adds optional advice from launch title/description. After a
binary upgrade run `prifly project runners update --repository .`; advice is
not launch permission. The host waits for the user's exact choice and reviewed
prepare before start. This package needs Pri-Fly >=0.13.76 for the documented
runner experience; its workflow uses existing 0.13.75 contracts.

    warmup -> fix-task -> check-change -> enabled security -> review-task -> commit

The task is the shared `{title, description, reference?}` JSON input; description
must name actual/expected behavior and available reproduction. Warmup fixes the
original base and passes a compact handoff. Fix uses the pinned `aif-fix` in Fix
now mode, preserving project overlays, regression-first, logging and learning
patches. Read-only checks judge actual HEAD, dirty and untracked work. There is
one fresh task reviewer, without ordinary PLAN or a challenge reader. A host
that cannot provide independence reports unavailable; warnings follow the
project's explicit choice, rather than being advertised as an independent pass.

If safe work needs a plan:

    fix-task -> fix-plan -> declared execution decision -> fix-from-plan -> checks

Both planning and execution use the pinned `aif-fix`; aif-plan/improve/implement
are not called. Planning receives the initial base, work already done and sealed
regression evidence. It creates a native file captured by Pri-Fly, then asks
`fix_plan_execution`. Owner can preanswer true; false ends partial with the
sealed plan. No implicit approval or native dialog. The prepared file stays
until the Attempt reports; a request suspends the same Attempt, not a new Run.
Timed deliveries explicitly yield execution while waiting; after the answer,
Pri-Fly drive redelivers that Attempt with a fresh envelope. A blocked planner
leaves a clearly incomplete native diagnostic draft for capture, never an
executable success.

The execution step consumes and returns the native manifest. It keeps the file
until capture, explicitly deferring upstream default deletion to the engine:
an exact untracked default file is removed after capture, its bytes retained in
Run artifacts. This order is necessary; deleting it before reporting loses the
required capture. Custom plan is staged as a repository document and preserved
through capture and final commit. No other files are staged by planning.

`extend.yaml.profile` selects one reviewed path:

| Profile | Declared fix-plan path | Lifecycle |
|---|---|---|
| `default` | `.ai-factory/FIX_PLAN.md` | Untracked working state, removed after native capture |
| `custom` | `.ai-factory/fix-plans/FIX_PLAN.md` | Owned custom plan staged/tracked and preserved |

These are explicit supported paths; arbitrary `config.yaml paths.fix_plan`
values are not guessed. A conflicting path or pre-existing unrelated file is
owner_required before planning. Direct fix and repair never execute discovered
foreign FIX_PLAN. Ordinary PLAN and other tasks' files are preserved by commit.
New paths require a reviewed profile/capture contract, not a runtime workaround.

`short_checks` configures additional commands; empty means no additional checks,
not a skipped regression check. `gate_warnings` chooses ignore/fix/stop. Security
is on by default; `exclude: [security]` is the explicit project bypass.
`settings.quality.repair_round_limit` defaults to 3 and can be 1..8. A repair
is a separate workspace-write Attempt; it then repeats checks, enabled security
and review, with the current implementation and regression evidence. All
blockers beyond repair's scope, unavailable required dependencies or an exhausted limit
finish partial with the real gate. A dependency broken by the change is a defect. A usable pass/needs_revision
report whose gate.status is blocked also stops partial with that exact gate;
pass means the report is usable, not that checks passed. For a required check
prevented by an unavailable external dependency, return pass with status blocked
and command/unrun-check evidence. Verdict blocked is for an Attempt that cannot
produce a usable assessment; it must still supply the required diagnostic gate.
blocking=false does not turn unrun required checks into success. Optional external
acceptance deferred outside this workflow is a warning under gate_warnings,
with its missing evidence stated explicitly.

Every fix result is a sealed JSON artifact with outcome/reason, work, execute_plan
and regression `{check,before,after}`. A stopped fix returns current implementation
and diagnostics, not a fabricated gate. Manual/runtime reproduction and safe-cause
fallback follow upstream; missing executable automation alone is not unreproduced.
Success exports the final implementation and quality gate, plus a native fix_plan
only when the plan route ran. No ordinary `plan` output is required or fabricated.

## Continue and project extensions

The same launch is resumable from partial/rejected or cancellation:

    prifly project continue --launch aif-fix --source-run RUN --host HOST --prepare

Use the reviewed digest for start. It transfers the source workspace/claim and
accepted root prefix, not a reset/new checkout. Gates always judge the current
tree; intervening edits invalidate prior evidence. Resume at root `quality`
repeats the whole checks/security/review call; accepted `warmup`/`build` carry.
Resume inside stopped root `build` replays that call, including fix-task and
plan preparation when needed: bridges must account for existing work, not redo
it blindly. Nested steps are not root `--from-stage` targets. Changed contracts
may require an earlier root stage; the engine's prepare/refusal is authoritative.
The custom tracked plan may conservatively require owner review when a stopped
build is replayed and its path already exists; automatic custom-plan restart is
not promised. Default blocked planning/execution resumes are covered by probes.
An owner who preanswered false cannot turn it into true by overriding resume
inputs: preserve that answer; reconsider via an explicitly reviewed new context.

Extensions can anchor root `build -> quality` or `commit -> done`. Inserted steps
receive no bound inputs, and answer pass/needs_revision/fail/no_work/blocked;
unhappy verdicts can finish at `abandoned`. TEST/MR and external systems belong
to installing projects, not this package. Local policy admits reviewed project
external_write insertions; no package step declares external_write or pushes.

Compile gates cover the package on three hosts and both plan profiles. Run:

    python3 -B tests/probes/fix_check.py --binary /path/to/released/prifly --report /tmp/fix-results.json

The probe performs real CLI Runs, Git changes, regression commands, native
capture/materialisation, repair and chained resume through commit/finish. Its
host is deterministic code using skill stubs: it does not prove an LLM follows
the adapters or establish independent model review. Those need separate real
host observations; the probe reports independence unavailable rather than pass.

The first release was v1.51.0 (package 1.0.0). The pilot correction is
v1.51.1 (package 1.0.1). Install
with `prifly project workflows add aif-fix`, or directly from
`StenHigh/prifly-aif-workflows --path aif-fix --ref v1.54.0`.
The central catalog pins the release tag and commit. Local catalog search/add
and completion are probe-covered. See `../docs/pilot-aif-fix-v1.51.0.md`
for pilot acceptance scenarios.
The recorded verification and real host observation are in
[`../tests/probes/results/aif-fix-0.13.76.md`](../tests/probes/results/aif-fix-0.13.76.md).

## Pilot corrections in v1.51.1 / aif-fix 1.0.1

The live pilot confirmed escalation through aif-fix, separate repair and chained
resume on released Pri-Fly 0.13.76; its product path included a real repair,
so it did not establish a clean direct LLM route without repair. Its remaining
limits are recorded in [the pilot report](https://github.com/StenHigh/prifly-aif-workflows/issues/4#issuecomment-6132513896).

The shared session-report context explains every Attempt's question report.
answered_questions.answer is nonempty prose; it is not the typed decision.
For short_checks="", report for example "Empty string: no additional checks
configured", basis decision, decision_id short_checks. Preserve the original
empty typed value and report only questions this Attempt actually met.
Pri-Fly 0.13.76 refuses the literal empty answer; the runtime fixture verifies
both that refusal and acceptance of the explanation without changing the ledger.
A basis instructions question entry alone is not a declared runtime decision.

Continue does not accept --workspace overrides; use the inherited claim mode.
After cancel, drive to settled terminal state before prepare. CLI access to the
authority must be available; persistence_unavailable is not cured by editing
its files. A supporting audit script missing npm in a PHP environment requires
an applicable read-only audit environment and honest coverage reporting, not
dependency edits in this package. Existing advisories remain standing warnings
unless this change introduced/exposed them.

Updating an already stopped v1.51.0 Run to these contracts was checked with
continue --prepare: Pri-Fly 0.13.76 refuses recover_prefix_changed at warmup
because the report context changed. Prepare leaves the source Run and claim
work untouched. Finish old Runs on their installed v1.51.0 before updating,
or review an explicit --from-stage warmup replay; do not assume an accepted
old prefix carries across this contract change. That full cross-version replay
was not executed by the probe. Same-version chained resume remains covered.

## Readability map

Start with `workflow.yaml`: warmup → build → quality → commit.
`workflows/build.yaml` owns direct fix and fix-plan execution.
`workflows/quality.yaml` repeats `quality-round.yaml` after repair, within the configured limit.
`steps/` declares ports, captures and effects; `contexts/` declares pinned instruction metadata.
Long instruction text lives in package-local `instructions/*.md`, including the shared session report.
The Markdown bytes match the former decoded YAML text, including its final newline.
Short host-skill pointers and schema ports stay local; their complete meaning fits beside the key.

[Ready inputs and complete prepare/start/continue commands](../examples/fanout-fix/README.md).
Readability changes do not add an import route or change repair/continue semantics.
