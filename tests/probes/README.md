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

They live here rather than in a scratch directory because a scratch directory is
cleared between sessions, and these were once rewritten from nothing for that
reason.
