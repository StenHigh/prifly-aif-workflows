# Core v0.13.86: named composition acceptance

[Release](https://github.com/StenHigh/prifly/releases/tag/v0.13.86) source is
`14145964b3c2fde3a450a11f8c4e8923922fd4d7`. It removes the erroneous downgrade
of a launch summary during the second naming review. Reviewed input/config/naming
changes still refuse. Schemas and published `/4` semantics remain unchanged.

Exact-SHA [verify](https://github.com/StenHigh/prifly/actions/runs/41472125704)
and [qualify](https://github.com/StenHigh/prifly/actions/runs/41472173497) passed.
Both native platform builds and signed publication passed in the
[release workflow](https://github.com/StenHigh/prifly/actions/runs/41476277110).

The Linux binary SHA256 is
`f46270b8046a95a03b39ce2c67bcee7212e944d68db74db8cc0e2852f90e0d13`.
Both manifest signatures were verified with the previously trusted release key.
Both archive hashes matched. A real managed update from 0.13.85 produced these same bytes.

The published binary ran the existing generic public-import/typed-carrier/parallel
example with project naming enabled. Prepare returned summary `/7`; start returned
`/7`, created the actual named directory and branch, and the Run ended `succeeded`.
The test used a clean checkout of the exact release commit. Its fixture released
its claim and removed its temporary authority registration.

[Machine-readable evidence](core-0.13.86-results.json) records exact refs and hashes.
Host replies were scripted. No live LLM, application or browser acceptance is
inferred from this Core scenario. Historical v0.13.85 evidence stays unchanged;
its combined named path did fail and is not relabelled as passed.
