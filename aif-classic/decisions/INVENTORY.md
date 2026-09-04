# Pinned AI Factory decision inventory

This tree is checked against the local AI Factory skill revision used for the
example. The YAML files are the finite, preflightable part of the questionnaire
plus one declared runtime choice. They become a sealed Pri-Fly Decision Sheet.
The rest of the list is an inventory, not a claim that Core intercepts a native
chat dialog.

Pinned sources:

- `aif-plan/SKILL.md` v1.0.0 — SHA-256
  `3be3c17f5478d15196832762d565c1d8d792666af4733f02b1d1d9bcf9002dbb`.
- `aif-implement/SKILL.md` — SHA-256
  `aaad2183c302ead1d2ac7ddf216ad1259ef53b72f7b1d9d9214f84dcb235998a`.
- `aif-commit/SKILL.md` — SHA-256
  `3dbeec8295c3cc592faf67d1669295803d472944c30ee7daeb8d330b0c9c9028`.
- `aif-improve/SKILL.md` (upstream `2.x`) — SHA-256
  `6b61bd2986166a93879b0496991bbe1696f15a7cf4894de3b4b2e0ca4976f25c`. Its
  `references/LIST-MODE.md`, `CHECK-MODE.md`, `EXAMPLES.md` and `VALIDATOR.md`
  are pinned as their own contexts, because a skill's own reference file is not
  carried by pinning the skill.

## aif-improve

Step 5 ends with the exact question “Apply these improvements?” and three
options, and the skill edits nothing before it is answered. That question is
declared as the `improve_apply` runtime decision, so the answer is recorded in
the Run rather than living in a chat window that no later step can see. The
`select` option still needs the upstream free-form follow-up about which
findings to take.

It carries `all` as an automatic recommendation of ordinary sensitivity, which
is what lets an unattended Run answer it. That label was `scope-changing` until
1.8.0, and the first night proved the cost: the engine answers automatically
only for an ordinary automatic decision, so the Run stalled at the question with
nine verified defects left unapplied. Ordinary is also the truthful label —
these refinements are about the task already planned, and the skill keeps what
it judges out of scope in a group it does not apply.

## aif-plan

Preflight YAML records plan depth, tests, Full/Ultra logging, Full/Ultra
documentation, roadmap linkage, conditional milestone and free-form
constraints. A selected `plan_profile` is passed to `aif-plan` as its leading
mode (`fast`, `full` or `ultra`).

## aif-implement

Native dialogs can still concern uncommitted work, missing active plan,
commit checkpoints, project-rule capture, documentation handling, plan cleanup,
worktree merge/cleanup and the final verify-or-commit choice. Their options
depend on repository state and generated plan contents, so this upstream skill
does not currently emit a DecisionRequest for them.

## aif-commit

This route declares no commit-time decision. `commit_grouping` was declared
until 1.4.0 and never fired once: the implementation skill commits at its own
checkpoints, so the commit step always receives a clean workspace and the
upstream skill stops before its grouping question. A declared choice the
developer is never shown is worse than an honest absence, so it was removed
rather than left as evidence of a mechanism nobody exercised.

The step still exists for the case where work is left uncommitted, and its
adapter now says to skip the skill entirely when nothing is staged instead of
spending a session on a "nothing staged" warning.

Native dialogs can concern grouping an active Commit Plan, free-form adjusted
groups, confirming or editing a generated commit message, splitting unrelated
staged changes and pushing a completed commit. Push is an external effect and
remains subject to its own Pri-Fly authorization; a preference is not an
Approval or Grant.

An upstream native `AskUserQuestion` is not a Pri-Fly decision. It remains a
normal attended host interaction until the executor emits `DecisionRequest/1`.
