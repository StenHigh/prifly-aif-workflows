# Shared composition contracts

`aif:package/composition-contracts@1.2.0` exports the applicability schema and
pins `composition-contracts@1.0.0` as an exact native dependency. The dependency
exports 16 shared schemas; the complete closure contains 17. Neither package
declares programs, effects or capabilities. `lock.json` pins all bytes and the
dependency lock. The current manifest digest is
`sha256:36c5f25d2bebb8c5cd9d77967ec5a2c8f2d6cec71f04b0b864c339bd8ef8eb6d`.

The `baselines/admitted-1.0.0/` bytes were already admitted in an acceptance
authority. They are frozen, not a claim of a public repository release. The
additive package never re-exports an existing schema identity: native admission
rejects overlapping exports, even when the bytes match. Both versions coexist.

Classic/profiled/fix 3.0.0 and UI/UX 2.0.0 explicitly depend on this package.
Run the following command once for each authority before compiling these packages:

```sh
python3 tools/install_composition_contracts.py \
  --binary /absolute/path/to/prifly-v0.13.86 \
  --project /absolute/path/to/authority
```

The installer first checks the pinned bytes, then imports the exact dependency closure through native `package import`.
`--check` checks bytes without authority access. Repeated imports are native
idempotent operations. Compile, questionnaire prepare and start never install
this dependency silently. An unavailable dependency remains a refusal.

Private schemas compiled independently in two owners have different exact refs.
Identical schema text does not make these refs equal. Shared external refs give
public component callers and providers one exact type. Copying private schemas
into a consumer is not the supported migration.

The YAML under each package's `schemas/` remains the editable source. Most unused
local aliases do not define public ports in these packages. The
`contract_schema_*` references bind those ports to the native dependency.
`tools/build_composition_contracts.py` regenerates the bundle and lock from these
sources; authoring requires PyYAML 6.0.1. CI checks reproducibility. A changed
published schema requires a new schema version and a new contract package version;
never replace already published bytes under an existing version.

Saved Runs keep their old sealed schemas. Updating the package source does not
migrate a saved Run. New Run preparation exposes the new dependency and build.

Classic/profiled/fix3.0.0 own their parameterised task1.2.0 schema.
It is excluded from this inert export; `contract_schema_task` no longer binds their ports.
Project-owned consumers use `{{schema_task}}` from the installing source owner.
The frozen task1.1.0 export remains available for UI/UX and existing public imports.
Its bytes, manifest digest and dependency closure remain unchanged.
`lock.json.bindings` describes the current external aliases; baseline locks stay frozen.
