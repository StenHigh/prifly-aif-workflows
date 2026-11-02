# Unified composition: v1.57.0 release guide

The candidate is being qualified for v1.57.0 on published Core v0.13.86.
Active catalog pins retain their old releases until publication and public installation checks.

Classic/profiled/fix/UIUX become package 2.0.0. Their public imports require an
explicit exact schema dependency. Feature becomes 1.4.0 for optional report refs;
its embedded review contract and launch stay unchanged. Other packages retain their versions.

```text
exact release checkout → explicit schemas → native prepare → reviewed start
```

## Installation

Set `PRIFLY_BIN`, `REPOSITORY`, `AUTHORITY` and `WORKFLOW_SOURCE` to actual absolute
paths. The repository and authority must already exist. Obtain the exact source
checkout separately; catalog installation copies only a package folder.

```sh
git clone --branch v1.57.0 --depth 1 \
  https://github.com/StenHigh/prifly-aif-workflows.git "$WORKFLOW_SOURCE"
"$PRIFLY_BIN" project workflows add StenHigh/prifly-aif-workflows \
  --path aif-classic --ref v1.57.0 --repository "$REPOSITORY"
python3 "$WORKFLOW_SOURCE/tools/install_composition_contracts.py" \
  --binary "$PRIFLY_BIN" --project "$AUTHORITY"
```

Choose the desired package path explicitly. The same dependency applies to
profiled, fix and UI/UX. The stdlib installer verifies locks and payloads before
importing frozen1.0.0 and additive1.2.0. It checks exact bytes with `--check`.
Compile, prepare and start never import this dependency implicitly.

For an existing installation, inspect and preserve project extensions before the major update:

```sh
"$PRIFLY_BIN" project workflows update aif-classic \
  --ref v1.57.0 --repository "$REPOSITORY"
```

The native updater preserves owner `extend.yaml` and `project/` files; it does not
translate them to `/5`. Migrate them deliberately and provide task inputs where
the declared point requires task + implementation. Review the resulting source
and native prepare summary before a new Run. Existing sealed Runs keep their old contracts.

A bundle installer must replace its owned schema bundle. Merging old schema files
into the additive package fails strict validation; weakening the lock is not a repair.

## Public imports and continuation

Public callers and providers use the same exact external schemas. Keep project
code under its own source owner. Do not copy private provider control stages.
[Complete example commands](../../../examples/unified-composition/README.md)
cover setup, compile, prepare, reviewed start and supported continuation.
The low-level configure/quality root supports its declared continuation.
The minimal task-aware wrapper has one root Call and does not declare resume.

## Qualification

Current rollout requires Core86 for composition with project worktree naming.
[Core acceptance](core-0.13.86.md) records signed assets, managed update and an
actual named Run. Linux binary SHA256:
`f46270b8046a95a03b39ce2c67bcee7212e944d68db74db8cc0e2852f90e0d13`.

Downstream compile/compatibility and all 13 shipping measurement scenarios passed
on these exact binary bytes. [Local qualification](qualification-0.13.86.md) records the results.
CI preserves each report. Transport
checks use scripted assessments; the historical85 live Chromium/readers and
private backend pilot remain separately scoped in [acceptance.md](acceptance.md).
None of these results is a full private application/browser acceptance claim.

[Catalog draft](catalog.draft.yaml) describes the candidate. Assign an actual
release ref and exact source commit only after publication.
