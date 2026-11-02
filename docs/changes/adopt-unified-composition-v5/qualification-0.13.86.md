# Downstream qualification on published Core v0.13.86

The Linux binary SHA256 is
`f46270b8046a95a03b39ce2c67bcee7212e944d68db74db8cc0e2852f90e0d13`.
[Core publication checks](core-0.13.86.md) verified signatures and exact release bytes.

Local candidate checks passed:

- 122 unit tests; versions, folders and ownership guards included.
- Reproducible profiled derivation, shared contracts and W6 bundle checks.
- Native verify: 8 packages, 132 components, 88 Steps and 3 hosts.
- Compatibility: 5 launches and 4 distinct builds.
- 13 shipping measurement scenarios: classic/profiled clean, repair, disabled,
  continue, permissions; fix clean, repair, disabled.
- Public composed UI/UX import with actual Chromium: two browser readers,
  succeeded, unchanged candidate and owned cleanup. Reader assessments used the deterministic test adapter.
- W6 compile contract: 18 positive cases and 8 expected refusals.

```text
measurement → report/log artifacts → implementation.reports → current reader
                         ↑ repair/continue produces new current evidence
```

[Recorded results](qualification-0.13.86/) retain reports and raw command logs.
The matrix records its pre-commit source HEAD and a fingerprint of shipping,
contracts, tools and test inputs. These inputs stayed unchanged during all cases.
Documentation edits outside those inputs are not relabelled as the measured source commit.
CI will qualify the final committed source and preserve the same native matrix.

The fixture hosts were scripted. No live LLM judgement or private application
acceptance is inferred. Historical85 live sessions and the separate backend pilot
remain in [acceptance.md](acceptance.md). Old failed evidence was not rewritten.
