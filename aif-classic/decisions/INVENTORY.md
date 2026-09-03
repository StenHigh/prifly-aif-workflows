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

`commit_grouping` is the one current dynamic bridge mapping. When the pinned
skill asks how an active Commit Plan should group staged changes, the package
adapter emits `DecisionRequest/1` for the declared `follow`, `together` or
`adjust` value. Pri-Fly records the answer, waits, and redelivers the same
Attempt with `decision_context.commit_grouping`.

Native dialogs can still concern free-form adjusted groups, confirming or
editing a generated commit message, splitting unrelated staged changes and
pushing a completed commit. Push is an external effect and remains subject to
its own Pri-Fly authorization; a preference is not an Approval or Grant.

An upstream native `AskUserQuestion` is not a Pri-Fly decision. It remains a
normal attended host interaction until the executor emits `DecisionRequest/1`.
