# W5 qualification fixture

This is a graph overlay for tests, not an installable feature workflow. The
fixture builder copies unchanged W1 workers/schemas/contexts/steps and overlays
these own initial 1.0.0 graphs in an owned temporary project.

One capture feeds two read-only Attempts with separate output directories.
All-join waits for every branch. An inner call catches technical failure so the
outer root call receives a normal rejected outcome and can replay the complete
round. Root-only error handling is insufficient; named negative probes retain
that observation without requesting a new engine operator. A separate native
cancellation gap remains: after one branch settles, cancel can leave stopping /
invalid_input and refuse claim release/continue. This blocks feature promotion.

The controller exports exact sealed refs after join and performs deterministic
assertions outside the actor context. It does not implement an automatic feature
aggregator, writer, browser environment or production host dispatcher.

See [W5 acceptance](../../../docs/changes/qualify-parallel-implementation-review/acceptance.md)
for host limits, actual CLI observations, measurements and remaining rollout work.
