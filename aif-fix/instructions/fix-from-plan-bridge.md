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
