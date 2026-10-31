# Explicit review evidence (W1)

Standalone package `aif-evidence:package/review-evidence@1.1.0`, prepared for the readability release. Requires Pri-Fly **0.13.76**. It supplies a quality component for W2/W3; it does not
change the canonical classic/profiled route or the installed bug workflow.

```text
configure request → quality { capture current candidate → review → evaluate }
                     → succeeded or partial with sealed report + gate
```

Three declared Python programs validate the request, measure the candidate and
assess coverage/freshness. The reader runs pinned `aif-review` plus its pinned
`references/SEVERITY.md`, read-only. No repair, commit, merge or external write
is performed by this package. Evaluation is executable code in this new package;
existing canonical packages remain instruction-only.

## Standalone setup

Install with `prifly project workflows add aif-review-evidence --repository .`.
For a manual project profile, declare:

```yaml
packages:
  aif-review-evidence:
    source: .prifly/workflows/aif-review-evidence
launches:
  aif-review-evidence:
    title: Explicit review evidence
    description: Review declared checks against the current candidate.
    kind: workflow
    workflow: .prifly/workflows/aif-review-evidence/workflow.yaml
```

Install the native `aif-review/SKILL.md` and `aif-review/references/SEVERITY.md`
in the chosen host's skills root. The compiler pins both; `+check` is not enabled.
Python 3.10+ and Git are required. Python runtime uses only the standard library;
PyYAML is not required in the installed package. Allow your actual interpreter:

```sh
prifly project local set --repository . --allow-executable python=/absolute/path/to/python3
prifly project questionnaire --repository . --launch aif-review-evidence \
  --host codex-cli --workspace checkout --input request=/absolute/path/to/request.json \
  --allow-execution --prepare
# Review the returned summary, then use its review_digest:
prifly project start --repository . --launch aif-review-evidence \
  --host codex-cli --workspace checkout --input request=/absolute/path/to/request.json \
  --allow-execution --expected-launch-digest DIGEST
```

`checkout` assesses current staged/dirty work in that repository; a new worktree
contains tracked state from its base, not dirty files from another checkout.
Never copy or guess a live Run's claimed tree to get around ownership. The
W3 consumer calls the quality graph inside its own Run, with explicit bindings.
The catalog publishes the previous package1.0.0 in v1.54.0. Candidate1.1.0 targets v1.55.0.

## Declared composition

Example request (`base_commit` is the original full 40-character SHA-1):

```json
{
  "base_commit": "0000000000000000000000000000000000000000",
  "round": 1,
  "optional_policy": "ignore",
  "require_separate_session": false,
  "checks": [{
    "id": "acceptance",
    "description": "Run the project's declared acceptance command and inspect its exit/output.",
    "method": "command",
    "required": true,
    "enabled": true,
    "applicable": true
  }]
}
```

Replace the example base with a real commit. Check IDs must be unique. Report `request_digest` copies the delivered request
artifact digest; an old report with the same IDs and code cannot satisfy changed
criteria or policy. Methods
are `code`, `command`, `browser`; enabled/applicable/required are sealed policy,
not fields the reader may override. Disabled checks are `excluded`, declared
inapplicable ones `not_applicable`; both require reasons. An executed entry has
passed/failed/warnings and nonempty method-matching evidence. Command evidence
records tool, actual command, observed output and exit code; browser evidence
records tool, page and actual observations. Static code inspection cannot satisfy
a browser check. Reports and program logs are outside the product tree.

Missing/duplicate/unknown checks, wrong evidence method, unavailable required
checks or stale candidate produce `gate.status: blocked` and Run `partial`.
A confirmed defect produces failed/blocking and partial. Optional unavailable
checks remain warnings; `optional_policy: ignore|stop` determines whether
warnings may finish or require owner attention. A usable report can have session
verdict pass while its gate is blocked. Schema-invalid reports are refused by
Pri-Fly before evaluation, without a fabricated successful result.

Session independence and actual model choice are separate host declarations.
`require_separate_session` checks that declaration; unavailable/declined model
profiles remain visible warnings, and never establish another-model review.

## Candidate basis and limits

The machine recomputes `git-candidate/1` before review and at evaluation: original
base, current HEAD, logical index (paths/blob IDs/modes), bytes and filesystem
modes of tracked and nonignored untracked paths, including missing paths and
symlink targets. Symlinks are not followed. Ignored caches/dependencies and `.git`
metadata are excluded; environment freshness is separate check evidence.
Submodules, unmerged index, unsupported file kinds and more than 10000 paths
are refused, not silently omitted. Two reads must agree for a snapshot.

This is a cooperative local check, not an atomic filesystem snapshot or hard
sandbox. A passed gate describes the measured candidate at evaluation; a future
consumer must invalidate it after any further write before integrating/committing.
Evidence observations, session and model fields remain host claims; structurally
valid fabricated observations cannot be independently disproved by this evaluator.
It verifies composition and current code identity, not truth of arbitrary prose.

## Continue

```sh
prifly project continue --repository . --launch aif-review-evidence \
  --source-run RUN --host codex-cli --allow-execution --prepare
# Execute the reviewed continuation with --expected-launch-digest.
```

Stopped root quality is replayed as a whole: fresh capture, reader and evaluation.
Configure can carry only when its effective contract is unchanged. Original base,
answers and claimed work are inherited; no `--workspace` override or reset.
Changes to the stopped quality contract can retain configure and rerun quality.
Changing the accepted configure contract gives `recover_prefix_changed`; on
0.13.76 explicit `--from-stage configure` gives `resume_prefix_empty` because
no earlier root stage was accepted. Preserve the source work and finish on the
old installed contract or review a separate new-start plan; this package does
not automate transferring that candidate. A version bump alone does not
necessarily change the effective contract. Cancel must be settled before continuation.

## Validation

```sh
python3 -B tests/test_review_evidence.py
python3 -B tests/probes/evidence_check.py --binary /path/to/released/prifly --report /tmp/w1.json
```

The probe uses a synthetic host, real declared programs, Git and released CLI.
It covers completeness, policy, stale dirty/index/untracked/deleted/mode states,
blocked/cancelled/chained resume and contract-change reuse/refusal. Compile
checks cover three hosts. Separate real host observations and their limits are
recorded in the W1 change acceptance report; synthetic evidence is not an LLM
or browser pass. See [W1 proposal](../docs/changes/add-explicit-review-evidence/proposal.md).

## File map

Read `workflow.yaml`, then `workflows/quality.yaml`: configure → capture → review → evaluate.
`steps/` declares each port and effect; `files/evidence.py` implements candidate and coverage checks.
`contexts/review-bridge.yaml` pins package-local `instructions/review-bridge.md` through context.source.
The Markdown preserves the former decoded YAML bytes, including its final newline.
Short ports, host-skill pointers and executable contexts retain their existing form.
Their complete binding stays visible beside the key; code remains code.

[Ready input and full prepare/start/continue commands](../examples/review-ui-ux/README.md).
[Project opt-in calls](../examples/review-uiux-extensions/README.md) remain separate from standalone installation.
