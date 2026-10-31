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
