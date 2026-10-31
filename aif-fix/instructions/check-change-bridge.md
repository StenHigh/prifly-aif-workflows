# Read-only verification of this bug fix
Read task, implementation and result. Judge actual HEAD and working tree with
 git -c core.quotepath=off diff <base_commit> plus untracked files; the old
head/path list is not the scope. Read callers as needed. Run the result's
regression check against this tree; missing or invalid before/after evidence
is a finding, never proof that checks passed. decision_context.short_checks
is the project composition (one command per line); empty means no additional
checks configured, not no regression verification. Do not invoke aif-verify
or require PLAN. No edits, commits or new report files; output only gate.
Output gate.gate verify; blocking true means repairable defects,
blocking_owner_only true only if no repair could help. Under gate_warnings
ignore leave warnings nonblocking, fix makes them repair work, stop sets
blocking_owner_only true and explains the owner's choice. A dependency broken
by this change is a repairable defect.
Gate fields are gate, status (passed/warnings/failed/blocked), blocking,
blocking_owner_only, findings (<=80 strings, each <=4000 chars), suggested_next
(continue or /aif-fix). Every finding needs evidence in the tree or command.
Pri-Fly, not this reader, runs repair and chooses the next stage.
Verdict describes report usability; gate.status describes check results and
availability. Return pass for a usable, evidence-backed gate, including failed
or blocked checks; pass does not mean the checks passed. When an unavailable
external dependency prevents a required in-scope check, return pass with
status blocked, blocking false, suggested_next continue, the failed command
and unrun checks in findings. Pri-Fly stops partial with that exact gate,
without repair or commit. If this Attempt cannot produce a usable assessment,
return verdict blocked with the required diagnostic gate explaining why.
A usable needs_revision follows the same graph decision; fail/no_work ends
rejected. Status blocked takes priority for every usable verdict; never
relabel a required blocked check as passed or warnings to continue.
Optional out-of-scope external acceptance left for later is a warning finding,
governed by gate_warnings. Distinguish it from a required check and never
claim it ran.
