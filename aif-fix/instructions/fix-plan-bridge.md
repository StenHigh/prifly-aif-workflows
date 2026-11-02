# Prepare this task's native fix-plan, then report
Use pinned aif-fix --plan-first, but the common protocol governs task ownership.
Create only the exact file named by workspace-trees.json. The task, prior result
and current implementation are the brief: preserve initial base, work and
regression evidence and plan only what remains. Mark the file with this task's
reference/title so execution can establish its subject. This step plans only;
do not apply implementation edits. pass means result.outcome planned.
For the custom profile, stage only this newly owned custom fix-plan so Pri-Fly
retains it as a repository document after capture; do not stage other work.
Default FIX_PLAN is untracked Run working state: do not stage or commit it.
Capture seals the native plan; do not send a JSON substitute or delete it.
If planning cannot finish, leave a native incomplete draft identifying this
task, what was established and why execution is not ready. Report the
appropriate verdict with implementation/result. Pri-Fly captures every
declared tree on every verdict, so keep this owned draft until submission.
Only pass/planned can reach the execution decision; stopped drafts are not
executable plans and are retained for diagnosis, not automatically executed.

Before reporting pass, use decision_context.fix_plan_execution if present.
Otherwise request that declared runtime decision through prifly-run with
--yield-execution (timed delivery must release its execution slot), then
stop without reporting or executing; continue on the redelivered same Attempt.
Never infer approval. Return result.execute_plan equal to that boolean answer;
false exports the prepared fix-plan and ends partial for owner review.

## Original report references

`implementation.reports`, when present, contains ordinary ArtifactRefs.
Preserve every original ref, its basis and its failed/unavailable/unknown state.
Read each declared ref through Pri-Fly artifact export; use declared report/log
refs only. Never scan arbitrary JSON or depend on an earlier Attempt directory.
A digest or schema does not establish success or applicability. Compare the
actual candidate, behavior, settings, selection, methods and environment with
what the original report measured. A changed SHA alone is not an instruction
to repeat all checks. Reuse sufficient applicable evidence without rerunning
its measurement. Missing, stale, corrupt or unavailable required evidence
requires the missing measurement or an honest blocked assessment. Do not run
an implicit full suite. A read-only reader cannot provision an external runtime;
a project-owned /5 measurement with declared effects runs before this reader.
Writers preserve inherited reports and append declared new report refs when
available. Never relabel old counts, subject, basis, exits or status for new work.
