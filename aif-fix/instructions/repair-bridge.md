# Repair findings on the current tree
Use pinned aif-fix in Fix now mode. Work only on the supplied gate findings
and within the task; leave owner-only issues for the owner. The original base
and earlier regression evidence are input, never recomputed from a later HEAD.
Apply regression-first to the repair and return current implementation/result.
If gate_warnings is stop, return needs_revision/outcome owner_required without
editing. pass means a safe repair was performed and outcome fixed. Pri-Fly
then repeats check-change, enabled security and task review. Do not run them
here. An unavailable dependency is blocked; no safe repair is needs_revision.
No new plan or execution of an existing unrelated FIX_PLAN.

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
