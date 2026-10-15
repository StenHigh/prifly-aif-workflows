`parallel_check.py` qualifies W5's isolated backend graph with synthetic reports
and real native Attempts, W1 evaluation, all-join, cancellation and crash replay.
It is not an automatic parallel feature mode. `parallel_contract.py` compiles
the same graph on three hosts. The separate opt-in `parallel_live.py` consumes
real host usage and observes two fresh Codex CLI readers in each of sequential
and parallel modes; raw prompts/events/submissions belong in a private fresh
artifact directory. Compile/synthetic cases do not establish live host support.
See [W5 acceptance](../../docs/changes/qualify-parallel-implementation-review/acceptance.md)
for commands, exact host limits and measured scope. Shipping feature stays
sequential; browser resource concurrency and other live hosts remain unqualified.

`product_check.py` qualifies standalone W2 with synthetic reports, real Git,
program evaluators and owned loopback environments. `--browser-library` uses
real Playwright/Chromium for the notes fixture, still deterministic assertions.
Fresh real Codex CLI readers are opt-in (`--live-skills`, `--case`, `--artifacts`)
and consume host usage; blocked host/tool access is not a browser pass.
`--manual-directory` delivers tasks to the current host and waits for its exact
submission.json, without selecting or rewriting verdict/report. Report shared
session honestly. `--auto-review` uses Codex --approve-for-me (workspace-write
sandbox with automatic review of eligible per-command escalation); no blanket
sandbox bypass is offered. Live CLI requests require separate sessions and
assert unique thread IDs, unchanged authority version and unchanged candidate. Exact live skills directory
contains aif-review.md and severity.md from AI Factory 2.19.0.

    python3 -B tests/probes/product_check.py --binary /path/to/released/prifly --report /tmp/product-runtime.json
    python3 -B tests/probes/product_check.py --binary /path/to/released/prifly --browser-library /path/to/playwright --report /tmp/product-browser.json

Browser dependencies are pinned by tests/fixtures/product/package-lock.json.
Install them outside any claimed candidate. All modes clean their own Runs,
claims, loopback processes/leases and monitor entry, including a Run created
before resource_busy is returned. Cancellation explicitly uses operator cleanup;
it does not assert a cancelled graph ran its tail.

`live_readers.py` is a manual, real-LLM acceptance probe for released aif-fix
1.0.2. It installs exact v1.51.2, uses full AI Factory 2.19.0 skills, removes
an owner-managed required dependency after deterministic fix setup, and lets
fresh Codex CLI sessions choose every reader verdict and gate. The controller
submits their files unchanged, asserts partial/exact gate/no repair or commit,
restores the dependency and resumes through fresh readers and a local commit.
Warmup/fix/commit are deterministic setup, not new LLM observations. This probe
uses the user's configured Codex model, consumes real host usage, and is not CI.
Each fixture cleans its Run/claim/monitor entries. Exact prompts, events and
reports in evidence-root are private; public result JSON redacts fixture paths.

    python3 -B tests/probes/live_readers.py --binary /path/to/released/prifly --skills-root /path/to/ai-factory-2.19.0/skills --evidence-root /private/tmp/live-reader-evidence

Use `--target check-change|aif-security|review-task` for one controlled case.
No expected verdict is supplied to the LLM. The prompt describes submission
schema constraints, including the required reason for unavailable/declined
model_profile; it does not select a verdict or change submitted reports.

# Probes

`fix_check.py` drives the separate `aif-fix` package with a deterministic
synthetic host on a released binary. It executes actual regression commands,
Git changes and native plan capture/materialisation through commit/finish.
The matrix covers direct fix on three hosts, local-source installation,
security exclusion, a generic extension, default/custom plan handling, blocked
planning/execution, timed decision wait on the same Attempt, repair after
check/security/review and its iteration limit, owner stops, cancellation,
chained resume with intervening edits, foreign plans and output/effect refusals.
Pilot regressions cover pass + blocked gate on check/security/review (partial
with the exact gate, then resume), and the empty question-answer refusal plus
its accepted explanation with an unchanged typed short_checks decision.
It asserts final implementation freshness, one transferred claim, generations,
source/working-tree immutability during prepare and cleanup. This is runtime
wiring evidence with skill stubs, not an LLM or independent-review observation.

    python3 -B tests/probes/fix_check.py --binary /path/to/released/prifly --report /tmp/fix-results.json

[Recorded 0.13.76 results](results/aif-fix-0.13.76.md) separate runtime evidence
from the real host observation and list the remaining limits.

CI runs this matrix. Use `--case NAME` for a focused diagnostic run.

Not gates. The four gates in `tests/` say whether this package is sound; these
two say what a Pri-Fly candidate hands an executor, and they are run by hand
against a candidate binary when the engine changes that path.

    python3 tests/probes/capture_check.py --binary /path/to/prifly
    python3 tests/probes/shapes_check.py  --binary /path/to/prifly
    python3 tests/probes/shapes_check.py  --binary /path/to/prifly --entry two

`route_check.py` is a compile-only probe for issue #4, with `route-probe/` as
its throwaway package. A child chooses planned or local_fix, exports an
implementation on both successful routes and a native captured plan only on
planned. The common tail consumes the required implementation and optional
plan; the root also exports the plan optionally. Five negative variants must
be refused for the intended binding error: a required child plan, a required
tail plan, a missing implementation export, a direct merge referencing just
one producer, and a required root plan. Compilation imports no package and
starts no Run. It does not test capture execution, repair, escalation or resume.

    python3 tests/probes/route_check.py --binary /path/to/prifly

Verified on released Pri-Fly 0.13.75 (darwin/arm64); binary SHA-256:
`debc809779336c5ef7ba514c0bbb718ad44b10293c458f7942d5aeb39cee270e`.
The CLI wraps these flow errors as `project_compile_invalid_workflow`; the
message starts with `missing_binding` or `unavailable_output` and its path.

`capture_check.py` dispatches one Run per capture kind plus one step with no
capture, and reports whether the captured port still appears as a writable slot
in `context.json`, whether the memo matches the compiled step, and — the line to
read first — whether ordinary ports moved. Only that last one can lose a Run's
result instead of raising a refusal.

`shapes_check.py` carries the shapes no product package has: two captures on one
step, a captured port that is the only output, and the same step handed out
twice across a park and a resume. It needs `capture-probe/`, a throwaway package
that exists for exactly those shapes and is never released.

`run_check.py` goes where no gate goes: past the first handoff. It is the host
for one real `aif-classic` Run — warmup, plan and implement answered with the
smallest honest artifacts — and answers verify with `--verdict blocked` (the
default) or `pass`, then prints where the Run ended and any refusal verbatim.

    python3 tests/probes/run_check.py --binary /path/to/prifly [--verdict pass] [--tag v1.44.0] [--keep]

It exists because 0.13.53 compiled and started v1.45.0 without a word and then
refused to hand verify its attempt (`schema_invalid at
/output_contracts/gate/required_for/2`): all four gates were green on a package
whose every Run died at the gate. CI runs it as a fifth gate both ways: `--check
--verdict pass` must carry the Run past verify, `--check --verdict blocked` must
end it `partial` with the submitted gate as the Run's output, byte for byte.
0.13.54 still refused `blocked` at `session submit`; 0.13.55 is the first release
where both pass. `--resume` then resumes the stopped Run with its own `aif-classic` launch
(0.13.61+) and checks that warmup, plan and implement carried over, that verify
was the first attempt handed out and that it was passed on to the next gate;
`--verdict cancelled` cancels the source at verify instead, the case of a host
that went away. CI runs both. Run it by hand before a release that changes what
a gate step declares.

`frozen_stand.py` is the fourth, and it answers a different question: what a
candidate *prints* differently. A change to reading is cheapest to check on data
that cannot change — build the stand once, then read the same settled Run with
the old binary and the candidate.

    python3 tests/probes/frozen_stand.py build   --binary /path/to/prifly
    python3 tests/probes/frozen_stand.py compare --binary /old --binary /new

The stand lives outside the repository, at `~/.prifly/stands/aif-classic`,
because it is an authority with absolute paths and a settled Run inside it. It
sits under `~/.prifly/` on purpose: since 0.13.16 that is the one place for
everything Pri-Fly keeps for a user, and the owner's cleanup is `rm -rf
~/.prifly`. A stand deleted that way is rebuilt in a minute with `build`; a
stand kept somewhere the cleanup cannot reach would outlive the decision that
everything lives in one place.

Two things it does to keep its own answer honest. It reads each command twice
with *both* binaries and masks whatever moved between two reads of the same one
— clocks, session ids, monotonic counters — so a real difference is not buried
under noise nobody hand-listed. And it reads `version` first, where two
different binaries must differ: a report whose every line says "same", including
that one, is comparing a binary with itself and is not evidence.

The stand also has a `--live` mode: the same Run, left open at the handoff
instead of cancelled, so its attempt holds the admission slot. It compares the
same reads on a different shape, and it costs accuracy — a live Run puts far
more into the output from clocks, so far more is masked: 6 and 3 fields vary
between reads on the settled stand against 56 and 42 on the live one. A live
`same` therefore covers less than a settled one. It is another instrument, not
a better one.

## What the frozen stand does not reach

One stand holds one shape, and a report of "nothing changed" is only as wide as
that shape. Written down so the silence is not read as more than it is.

The Run in it: `aif-classic`, default profile, host `codex-cli`, workspace
`worktree`, driven to the first assisted handoff and then cancelled — so the
attempt is **assisted and settled, with no observed process start**. That is
why 0.13.4's `dispatch_latency` change showed here at all.

Not reached by it, and therefore not covered by any comparison it reports:

- every step after `warmup` — nothing answers a handoff here, so no gate result,
  no plan capture, no fix round, no commit;
- a Run that finishes: outcomes `succeeded`, `partial` and their output
  bindings are never read;
- the profiles `full` and `ultra`, and the hosts `codex-app` and `claude-code`;
- an attempt whose process start *is* observed — the engine session's stand
  covers that branch, and the two together showed 0.13.4 changed the assisted
  case and left the local one alone;
- runtime decisions, waivers, parallel stages (`aif-fanout`), more than one
  package edition in the authority;
- `capacity_conflict` and `active_stop`. Both were tried and both are out of
  reach of anything that must leave the stand alone: a second `project start`
  does reach `capacity_conflict`, but the refusal creates and queues the Run —
  `capacity show` listed one more `waiting` entry after each attempt, measured
  10 → 11 — so the probe grows the stand it is meant to freeze. The fingerprint
  is what caught it. They stay uncompared until there is a read-only way to ask
  whether a start would be admitted.

A change to any of those can pass this comparison in silence. When one of them
starts mattering, the answer is another stand with its own list, not a wider
claim about this one.

### Not reached by any stand, ours or the engine's

Four stands exist: these two, and the engine session's settled and paused ones
on their own deterministic fixture. What none of the four reads is worth
keeping in one place, because a release touching only these areas is verified
by its author alone:

- the run monitor and its maintenance requests — 0.13.9 fixed a refused
  request blanking a source's Run list (188 of 200 listings showed 0 of 6 Runs)
  and no stand could have seen it; the engine session watches that side;
- `active_stop`, which only a mutating command reaches;
- anything a Run reaches only after an assisted step is answered — since
  0.13.19 that includes `effect_not_permitted`, the refusal of a report from a
  step that declared no workspace effect and changed the tree: the fixture
  dispatches the first handoff and nobody answers it, so the first reader of
  that refusal is a live pilot Run;
- the text of a compile-time refusal. The stands compile a valid package, so
  the wording of `unavailable_output`, `schema_invalid` and their kin never
  enters a comparison — 0.13.18 and 0.13.22 changed only such text and both
  stands reported `1 of 9`. That class is read outside the stands: break the
  package in one known way per cause, compile on the published binary, and
  assert each refusal's own words and the absence of another cause's words —
  after running the same cuts on the previous release, where they must be red.
  Those cuts have been kept as throwaway scripts so far; a change of that kind
  is verified only if someone runs them.

`capacity_conflict` left this list in 0.13.10. It sat here for four releases
because reaching it meant starting a Run, and the refusal created and queued
one; `capacity show` now reports `available` and `would_refuse` without a
launch, so the live stand compares that refusal and the fingerprint shows the
queue untouched. That is the shape of a way out of this list: not a cleverer
probe, but a read-only way to ask the question.

Two releases in a row landed a change nobody's stand could see, which is why
this list is kept rather than remembered. A stand's silence about what it does
not read is not evidence: "one of nine reads differed" is a complete statement
about those nine, and says nothing about the rest of a release.

## A test Run is removed by whoever started it

Every probe here that starts a Run removes what the Run left: its directory and
the entry its `run start` wrote into the monitor registry
(`~/.prifly/monitor/sources`). `capture_check.py` and `shapes_check.py` do it
on exit and print how many entries they removed; the compatibility gate does
the same and reports `registry_entries_removed` beside its result. A stand kept
on purpose is removed with `frozen_stand.py destroy --at DIR`, never with
`rm -rf`, so its registry entry goes with it. The registry compares real paths:
a temporary directory is handed out as `/var/...` and recorded as
`/private/var/...`, and matching the unresolved string removed nothing while
reporting zero.

They live here rather than in a scratch directory because a scratch directory is
cleared between sessions, and these were once rewritten from nothing for that
reason.
