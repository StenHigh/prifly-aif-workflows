# Unified composition: draft release guide

This is an unpublished candidate. Active catalog refs retain their published
packages. Do not move a catalog pin or claim a release from this document.

Classic/profiled/fix/UIUX become package 2.0.0 because the setup now requires an
explicit exact schema dependency. Feature becomes 1.4.0 for the shared optional
reports shape; its embedded review contract and launch stay unchanged. Other
package versions retain their current values.

```text
candidate source → explicit schemas → native prepare → reviewed start
```

Install the source candidate into a project, then install its inert schema
closure with `tools/install_composition_contracts.py --binary ABS --project ABS`.
The stdlib installer checks locks/payloads before importing frozen1.0.0 and
additive1.2.0. Compile/prepare never import dependencies implicitly. A package
installer that merges old bundle files instead of replacing the owned bundle
must fail strict validation; it must not weaken the lock check.

Migrate project extensions deliberately to /5 and add task inputs where the
owner point declares task + implementation. Public import uses the same exact
external schemas in both owners. Keep project code under its own source owner;
never copy private provider control stages into a consumer.

Use the complete commands in examples/unified-composition/README.md. Prepare is
read-only; start uses the reviewed digest and explicit execution authorization.
The low-level configure/quality root can continue from its accepted prefix.
The minimal task-aware wrapper has only one root Call and does not declare resume.
Real development consumers must supply meaningful accepted stages before that Call.
Saved Runs and installed project files are not automatically migrated.

Release qualification uses the exact signed published v0.13.85 Linux asset,
SHA256 d512311554b31f469c912b3e1a2d65128edf99362d8ab29314c91448134fe954.
Compilation/compatibility, scripted native transport/routing, actual Chromium
with two fresh UI/UX sessions and the separate private backend pilot have
separate evidence. None is a claim of full application/browser acceptance.

[Core #15](https://github.com/StenHigh/prifly/issues/15) remains a rollout limit:
composition + project worktree_naming refuses during start on v0.13.85. The
private pilot selected ordinary native allocation in a separate source profile;
its primary naming policy stayed intact. Do not label the named path qualified.
Before publication, check latest Core and complete the release decision around
that limitation. Catalog draft descriptions are in catalog.draft.yaml; assign
an actual repository release ref and exact commit only after publication.
