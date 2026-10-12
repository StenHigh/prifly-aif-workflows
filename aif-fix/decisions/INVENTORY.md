# aif-fix source and decision inventory

Adapters were written against AI Factory 2.19.0, Git tag commit
`e144f95c89de0d0cb6c9b38dbe8c2907b00dc5ce`. Git source
`skills/aif-fix/SKILL.md` SHA-256:
`018267ccbe8eda03d3ebc006529b4db8482884458d0acca5d12e0ffda8b21ee1`.
This records upstream provenance, not an installed-byte check. Pri-Fly pins
what the selected host actually has at start; compiler fixtures use stubs.
The installer changes command notation on Codex hosts. Shared warmup/review/
commit/security source pointers preserve the classic package's identities.

- `short_checks`: preflight; optional additional commands for the current tree.
- `gate_warnings`: preflight; ignore, fix, or owner stop.
- `fix_plan_execution`: runtime; boolean permission to execute this task's
  prepared native fix-plan. Scope-changing, not automatic, no assumed answer.
  Owner may preanswer with `--runtime-answer fix_plan_execution=true`; otherwise
  the planner requests it using the runner's declared Decision Bridge, then
  waits on the same Attempt. False seals the prepared plan and finishes partial.

HANDOFF_MODE=1, empty task ID and no MCP sync are truthful for these Attempts.
Undeclared native questions are not a Pri-Fly decision. Supplemental test
suggestions are recorded, not a question a finished Attempt cannot deliver.
Project skill overlays win over the base skill's logging/patch defaults.

The session-report supporting context distinguishes typed values from human
question explanations: a legal empty short_checks answer remains empty in the
decision sheet, while answered_questions.answer uses nonempty descriptive text.
Report basis instructions does not replace the fix_plan_execution decision.
