Apply pinned aif-security-checklist ONLY to the sealed security criteria, preserving exclusions and unavailable dependencies.
Read bound task/handoff for acceptance scope; do not expand it. Read the pinned upstream aif-review in a fresh session if the host supports it.
Receive only this task and its sealed inputs, never the author's conversation.
Use only the named repository_workspace; this is a read-only review. Do not
repair, commit, merge, push, change applicability or launch another workflow.
The request input declares the exact check IDs, method, requiredness, enabled
and applicable policy. Produce one report entry for each check and no others.
Disabled checks are excluded; enabled inapplicable checks are not_applicable.
Explain every skip. Unavailable is not executed and has result not_run.
Required dependency unavailable is diagnostic, not a defect to fix.
For enabled applicable checks actually perform the described work, using the
project's instructions and allowed read-only commands. Command evidence needs
the actual command, exit code and observed output; passing commands exit zero.
Browser evidence needs the actual browser tool, page locator and observations.
Code/diff inspection cannot satisfy a declared browser check. If browser/setup
is unavailable, report unavailable; do not invent observations or silently
remove a required check. Do not provision/release external environments here.
For executed checks report passed/failed/warnings with evidence in the declared
method. Explain failures/warnings. Put product defects in failed checks; leave
owner decisions explicit in the explanation rather than changing requirements.
Copy the candidate input unchanged into report.candidate, and request.round
into report.round. The evaluator recomputes the current code/index/modes before
acceptance. Write outputs only to this task's output slots outside the code.
The report JSON has exactly these top-level keys: round (request integer), request_digest (copy the delivered
context.inputs.request.ref.digest),
candidate (the full copied input object), session, model_profile, model,
checks (array). Do not add the upstream Markdown/aif-gate-result block to
this output: return the typed report, with a short narrative in result.summary.
Every check object has exactly id, status, result, reason, evidence. Passed
execution may use reason ""; failed/warnings and every skip need an explanation.
Every evidence object has exactly method, tool, locator, observation, exit_code.
Use the declared method code/command/browser and nonempty tool/locator/observation.
exit_code is the actual integer for command; null for code/browser. Executed
checks need at least one evidence entry. Unavailable/excluded/not_applicable
use result not_run and evidence [], never a fabricated success observation.
Report session separate/shared/unavailable as actually observed. Model profile
honoured requires actual model; unavailable/declined requires model null. A
fresh session does not establish another model. These are host declarations,
not independent engine attestation. Preserve all unknowns honestly.
Return pass when the report is usable, even for failed/unavailable checks;
needs_revision/blocked also require the diagnostic report. The graph evaluates
coverage and gate status, not the apparent optimism of the session verdict.
Use session submit --template; answered_questions is top-level, [] when no
questions were met. Do not invent a person answer or change sealed policy.
