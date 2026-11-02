# Read project context and seal the Run's original base
Follow the pinned aif-warmup: read context, configuration and relevant skill
paths; distil handoff without changing any repository file. The handoff is
{summary, entry_points, conventions, sources, open_questions}; summary <=4000
characters, entries <=400 characters; at most 24 entry_points, 24 conventions,
64 sources and 16 open_questions. The last field is optional.
Also return implementation with base_commit=head_commit=git rev-parse HEAD,
and changed_files from git diff --name-only HEAD plus untracked files. This
initial snapshot fixes the base for direct fix, planning, repair and resume.
Read the actual claimed repository_workspace, not the host's original checkout.
Do not classify/select a workflow: the user already chose aif-fix.

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
