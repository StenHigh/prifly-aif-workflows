# Project-configured task description limit

This fixture isolates [workflow issue #3](https://github.com/StenHigh/prifly-aif-workflows/issues/3#issuecomment-6751418651).
The root calls a child workflow. The child dispatches one assisted worker.
All six task input/output ports use the same compiled schema reference.
The driver echoes synthetic task bytes; no LLM or application code runs.

```text
author profile or explicit compile value -> compiled task schema
                                                   |
                                      root -> child -> worker
                                                   |
                                      unchanged task output
```

Run from this repository with Python 3:

```sh
PRIFLY_BIN=/absolute/path/to/released/prifly
python3 -B tests/probes/task_description_limit.py \
  --binary "$PRIFLY_BIN" --output /tmp/task-description-limit-results.json
```

`PRIFLY_BIN` is a placeholder for the official release binary.
The recorded run uses Pri-Fly v0.13.89.
The script creates and removes its own temporary repositories and authority.
It removes its own monitor registration and verifies that no active claims remain.
It never installs this fixture into the owner's project.

The driver checks default boundaries, a declared project setting, `/5` inheritance,
reference collisions, author-declared package profiles and standalone `compile --value`.
It also tests whether prepare/start can reuse explicit compile values.
The generated report records actual refusals, compiled definitions, binary and source digests.
It verifies unchanged earlier Runs after later configuration changes.

The package declares only `standard: 12000` and `expanded: 32000` profiles.
These profiles are positive controls for existing compiler functionality.
They do not provide an owner-selected arbitrary numeric value.
The driver generates a separate source without profiles to test a compile value of 40000.
This source is synthetic; the driver never rewrites a published package.

No continue, catalog update, live model or shipping workflow acceptance is claimed.
See [native results and interpretation](../../../docs/changes/configure-task-description-limit/native.md).
