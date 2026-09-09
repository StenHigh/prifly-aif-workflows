# Probes

Not gates. The four gates in `tests/` say whether this package is sound; these
two say what a Pri-Fly candidate hands an executor, and they are run by hand
against a candidate binary when the engine changes that path.

    python3 tests/probes/capture_check.py --binary /path/to/prifly
    python3 tests/probes/shapes_check.py  --binary /path/to/prifly
    python3 tests/probes/shapes_check.py  --binary /path/to/prifly --entry two

`capture_check.py` dispatches one Run per capture kind plus one step with no
capture, and reports whether the captured port still appears as a writable slot
in `context.json`, whether the memo matches the compiled step, and — the line to
read first — whether ordinary ports moved. Only that last one can lose a Run's
result instead of raising a refusal.

`shapes_check.py` carries the shapes no product package has: two captures on one
step, a captured port that is the only output, and the same step handed out
twice across a park and a resume. It needs `capture-probe/`, a throwaway package
that exists for exactly those shapes and is never released.

`frozen_stand.py` is the third, and it answers a different question: what a
candidate *prints* differently. A change to reading is cheapest to check on data
that cannot change — build the stand once, then read the same settled Run with
the old binary and the candidate.

    python3 tests/probes/frozen_stand.py build   --binary /path/to/prifly
    python3 tests/probes/frozen_stand.py compare --binary /old --binary /new

The stand lives outside the repository, at `~/.prifly-stands/aif-classic`,
because it is an authority with absolute paths and a settled Run inside it.

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

They live here rather than in a scratch directory because a scratch directory is
cleared between sessions, and these were once rewritten from nothing for that
reason.
