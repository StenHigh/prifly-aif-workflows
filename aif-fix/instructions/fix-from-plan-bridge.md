# Execute only the supplied native fix-plan with aif-fix
Pri-Fly materialized fix_plan at workspace-trees.json's declared path. Read
that exact native file and execute it with the pinned aif-fix, accounting for
work already done and the sealed prior evidence. Do not call aif-implement.
Keep the file until submission on every verdict, including blocked/fail: this
step has an input/output capture. This explicitly defers the skill's default
FIX_PLAN deletion to Pri-Fly, which takes the sealed untracked default file
out of the tree after capture. Custom/non-default plan stays staged/tracked
and is preserved; never delete it. Update its progress truthfully as needed.
Return implementation and result on every verdict; the captured fix_plan is
also guaranteed. A pass must mean fixed; a further planning need is an
owner_required stop, not an unbounded planning loop.

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
