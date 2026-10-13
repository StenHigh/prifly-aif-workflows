# aif-fix 1.0.2: live reader acceptance

2026-10-13. Published v1.51.2 source
`0e93c36672e23ac404463f815cb89c7c3ffe31fe`, released Pri-Fly **0.13.76**,
darwin/arm64, binary SHA-256
`5df5aceccde63c173d3f38f20426eb9dd131e6c3b0f6511a99002ad874a49f00`.
Full supporting skills, scripts and references from AI Factory **2.19.0**,
commit `e144f95c89de0d0cb6c9b38dbe8c2907b00dc5ce`.

Three isolated Git fixtures declare a mandatory external control for one reader
stage in task/DESCRIPTION before start. A real Python checker reads an
owner-managed file outside the claimed tree. The controller removes this file
after accepted fix, before quality delivery. Readers receive only the sealed
Attempt, inputs and actual tree. No expected verdict or test assertions are
provided to the host. The source/root gate must match the host's exact bytes.

Each reader is a fresh ephemeral Codex CLI session without author conversation.
The user's configured model was gpt-6.1-sol; no model override or different-model
claim. Core submission templates and allocated output paths are supplied. The
controller submits the host's exact file, without editing its verdict, gate or
summary. Format constraints do not select an assessment.

| Required control unavailable at | Natural host result | Root result | After restore/continue |
| --- | --- | --- | --- |
| checks | pass + verify/blocked, blocking=false | partial, exact original gate; no repair/commit | fresh checks/security/review, local commit, succeeded |
| security | pass + security/blocked, blocking=false | partial, exact original gate; no repair/commit | fresh checks/security/review, local commit, succeeded |
| review | pass + review/blocked, blocking=false | partial, exact original gate; no repair/commit | fresh checks/security/review, local commit, succeeded |

All three source reports contain the actual failed command/FileNotFoundError
and identify the mandatory check left unperformed. The supporting full security
audit script actually runs; this standard-library fixture has no dependency
manifests, network/auth/database/browser/deployment surface. Missing optional
roadmap and unavailable model-profile mapping are honest nonblocking warnings
under gate_warnings=ignore. They never downgrade required blocked coverage.

After restoring the original dependency bytes, reviewed same-version continue
reuses warmup/build and executes current quality again. Every resumed reader is
a new CLI session. Each source version/tree remains unchanged during prepare;
one claim transfers generation 1→2, original base and dirty/untracked owner
work survive. Fix is not repeated. Readers leave the claimed tree unchanged.
All temporary Run/claim/monitor entries are cleaned. Fifteen distinct accepted
reader sessions are recorded in the [machine report](aif-fix-bridge-1.0.2-live.json).

## Report-format refusal

The first checks fixture already produced natural pass + blocked and partial,
but its resumed review draft omitted model_profile.reason. Core refused it as
model_profile_reason_missing at /model_profile/reason. This was report format,
not blocked-gate routing. The draft was retained privately and the fixture
cleaned. The neutral host prompt now states the actual model_profile schema:
honoured requires named; unavailable/declined require dedicated nonempty reason.
The checks fixture was rerun with fresh hosts and passed completely. No verdict
or gate was manually switched to obtain the expected outcome.

## Reproduction and bounds

[Manual probe](../live_readers.py), using a full AI Factory 2.19.0 checkout:

```sh
python3 -B tests/probes/live_readers.py \
  --binary /path/to/released/prifly \
  --skills-root /path/to/ai-factory-2.19.0/skills \
  --evidence-root /private/tmp/live-reader-evidence
```

This consumes real host usage and is separate from deterministic CI. Use
--target check-change, aif-security or review-task for one case. Prompts,
events, exact reports/ports and receipts stay in the private evidence directory.
Public fixture paths are redacted; recorded digests describe original files.

Warmup/fix/commit are deterministic fixture setup with real regression/Git,
not new LLM observations of those adapters. This test closes the reader wording
acceptance only. Earlier real pilots and deterministic runtime probes remain
separate evidence for other routes. No additional model, all-host UI acceptance,
product QA or numeric time/token saving is claimed.
