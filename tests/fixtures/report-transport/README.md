# Generic report transport and nested extension reproducer

This is a test fixture. It is not an installable AI Factory package.
It uses public artifact outputs, bindings, repeat, assisted sessions and project extensions.
The Python driver supplies synthetic replies. No model, application suite or external service runs.

Run from the repository root with an absolute path to the released Pri-Fly binary:

```sh
python3 -B tests/probes/report_transport.py \
  --binary /absolute/path/to/released/prifly \
  --output /tmp/report-transport-results.json
```

The driver creates an isolated Git repository and authority for each case.
It compiles the fixture, prepares the launch, starts real Runs and answers their sessions.
It releases claims, removes monitor registrations and deletes its temporary directories.
No host skills, execution allowlist or application configuration are needed.
`--cases success` runs the smallest positive control and nested-anchor refusal.

```text
produce(report + log + carrier)
  -> project measure
  -> repeat round: read -> repair -> partial -> read
  -> project consume(original report)
  -> succeeded
```

Producer publishes the log before the report and the report before the carrier.
All three use reserved output slots. The carrier holds the exact report ArtifactRef.
The report holds the exact log ArtifactRef. A ref has artifact_id, integer revision and digest.
Readers export these declared refs through the public artifact API.
They do not scan disk, JSON or history for reports.

The driver deletes the completed producer Attempt directory before reading its artifacts.
Readers and the project consumer still obtain the original report and log bytes.
The consumer compares the carrier's explicit report ref with the original producer ref.
Unknown artifacts, missing revisions and substituted digests must refuse export.

The repair case changes and commits only `metadata.txt` in the owned worktree.
The report's subject, basis, method, raw exit and result remain unchanged.
The fixture explicitly defines this metadata as unrelated to its synthetic check.
This does not qualify a model's judgment about real code changes.

The failed case carries exit=1/status=failed without relabeling the report.
Its reader returns blocked and the root finishes partial with the carrier.
The continue case stops a reader, then uses reviewed `project continue` at `cycle`.
It reuses producer and project-measurement stages without changing the source Run.
Core can allocate new output refs for reused stages. Explicit original refs inside the carrier remain unchanged.
It does not model recovery inside a child Attempt or migrate an older sealed graph.

`extend.yaml` inserts project measure before the root repeat and project consume after it.
The measurement step declares external_write and an explicit system/operation/target.
Its synthetic reply provisions nothing. This verifies reachability, not an external service lifecycle.
The read step declares repository_workspace: read_only and effects: none.

After the positive Run, the driver replaces only `extend.yaml` with `nested-extension.yaml`.
The latter targets the existing child edge `round.repair -> fixed`.
Pri-Fly 0.13.82 refuses compilation with:

```text
project_extension_unknown_workflow: round (known: transport)
```

The child exists and the edge is valid. The parent calls it through a native repeat.
The supported root insertion measures once. It does not run after the nested repair.
This reproduces a project-extension boundary, not a failure of artifact transport.
No Core files or shipping package files are changed by the test.
