# Fix the task now
Use the pinned aif-fix in Fix now mode under the supplied common protocol.
The input implementation fixes the original base, not a restriction to an old
HEAD. Establish expected behavior and investigate callers before editing.
If safe work requires a fix-plan, return needs_revision with outcome
needs_planning and describe everything already done. First check that the
selected capture path named in the common protocol is free and config matches the selected
profile. A pre-existing file or conflicting config is owner_required, not
permission for the later capture to overwrite it. No plan is created here.
Report pass only with outcome fixed and after evidence. Other unresolved
causes return needs_revision; unavailable dependencies return blocked.
Both latter verdicts stop this Run unless the cause is needs_planning.

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
