#!/usr/bin/env python3
"""Static contract of the AI Factory workflow folders: YAML only, distinct roles, pinned inventory."""

import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLASSIC = ROOT / "aif-classic"
FANOUT = ROOT / "aif-fanout"
PROFILED = ROOT / "aif-profiled"


class WorkflowFolderTest(unittest.TestCase):
    def test_folders_are_marked_yaml_only_workflow_folders(self):
        for folder in (CLASSIC, FANOUT, PROFILED):
            workflow = (folder / "workflow.yaml").read_text()
            self.assertTrue(workflow.startswith("authoring: prifly-project-workflow/1\n"), folder)
            self.assertTrue((folder / "extend.yaml").is_file(), folder)
            # Since Pri-Fly 0.13.24 `project/` inside a package folder is the
            # project's own subtree, carried across `workflows update` like
            # extend.yaml. An upstream package that ships one is refused by
            # `workflows add` and `workflows update` since 0.13.25 (on 0.13.24
            # only `update`, and only once the project has a `project/` of its
            # own — `add` installed it silently as the team's files, and
            # `update` then never touched it). `compile` never
            # refuses: in an installed copy the folder is exactly where it
            # belongs, so this guard is what stands between the source tree and
            # that refusal.
            self.assertFalse((folder / "project").exists(), f"{folder} ships a project/ subtree, which belongs to the installing project")
            self.assertEqual(list(folder.rglob("*.yaml.tmpl")), [])
            yaml_sources = [item.read_text() for item in folder.rglob("*.yaml")]
            self.assertFalse(any(line.strip() == "---" for source in yaml_sources for line in source.splitlines()), folder)

    def test_classic_decision_catalog_names_its_own_install_path(self):
        for folder in (CLASSIC, PROFILED):
            workflow = (folder / "workflow.yaml").read_text()
            self.assertIn("decision_catalog:", workflow)
            for line in workflow.splitlines():
                if line.startswith("  - .prifly/workflows/"):
                    self.assertTrue(line.startswith(f"  - .prifly/workflows/{folder.name}/decisions/"), line)
                    self.assertTrue((folder / line.split(f"{folder.name}/", 1)[1]).is_file(), line)

    def test_profiled_is_classic_derived_by_the_tool_and_nothing_else(self):
        # aif-profiled is not edited by hand: it is what tools/derive_profiled.py
        # writes from aif-classic, so a fix to a classic bridge reaches it by
        # regeneration and a hand edit here is a divergence the gate names.
        spec = importlib.util.spec_from_file_location("derive_profiled", ROOT / "tools" / "derive_profiled.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        files = module.derive()
        self.assertGreater(len(files), 50, "the derivation produced almost nothing")
        for relative, text in files.items():
            with self.subTest(file=str(relative)):
                self.assertEqual((PROFILED / relative).read_text(), text, f"aif-profiled/{relative} is not what tools/derive_profiled.py writes")
        generated = set(files)
        for path in PROFILED.rglob("*.yaml"):
            self.assertIn(path.relative_to(PROFILED), generated, f"{path} is not derived from aif-classic")
        # The README is the one file written by hand, and a regeneration from an
        # empty folder does not bring it back: v1.41.0 shipped without it.
        self.assertIn("model_profiles", (PROFILED / "README.md").read_text())
        # Every step carries a profile, and a profile names work, not a product.
        for name, (requested, reason) in module.PROFILES.items():
            step = (PROFILED / "steps" / f"{name}.yaml").read_text()
            self.assertIn(f"requested: {requested}\n", step)
            self.assertNotRegex(requested, r"claude|gpt|opus|sonnet|haiku|gemini", requested)
            self.assertTrue(0 < len(reason) <= 512, name)

    def test_continuation_tails_are_derived_by_the_tool_and_nothing_else(self):
        # Both tails are what tools/derive_continuation.py writes from their
        # sources: a hand edit, or a source change nobody regenerated, is named
        # here. Their versions live in the tool, not in the source's.
        spec = importlib.util.spec_from_file_location("derive_continuation", ROOT / "tools" / "derive_continuation.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        files = module.derive()
        self.assertGreater(len(files), 100, "the derivation produced almost nothing")
        for relative, text in files.items():
            with self.subTest(file=str(relative)):
                self.assertEqual((ROOT / relative).read_text(), text, f"{relative} is not what tools/derive_continuation.py writes")
        for _, name, _, version in module.TAILS:
            for path in (ROOT / name).rglob("*"):
                if path.is_file() and path.name != ".DS_Store":
                    self.assertIn(path.relative_to(ROOT), files, f"{path} is not derived")
            workflow = (ROOT / name / "workflow.yaml").read_text()
            self.assertIn(f"\n  version: {version}\n", workflow)
            self.assertIn(f"\nversion: {version}\n", workflow)

    def test_classic_inventory_records_the_skill_revisions_it_was_written_against(self):
        # This compares the document with itself on purpose: the skills live on
        # the host, not here, so the only thing a static gate can hold is that
        # the provenance record was not quietly dropped.
        inventory = (CLASSIC / "decisions" / "INVENTORY.md").read_text()
        # ai-factory 2.19.0: plan, implement, commit (unchanged since 2.18.1).
        for skill_hash in (
            "086d68806b9c8a27d8de51ae6389492715e9b4caa5abb277f9bc02fde047fe9d",
            "0269d7931c6a0c001c1fe6c99fec98b0a466e177259c302033fd4f02e5f8ae19",
            "3dbeec8295c3cc592faf67d1669295803d472944c30ee7daeb8d330b0c9c9028",
        ):
            self.assertIn(skill_hash, inventory)
        # The security step pins the skill under the name upstream ships, not
        # the one a host may have copied it to.
        self.assertIn("path: aif-security-checklist/SKILL.md", (CLASSIC / "contexts" / "aif-security.yaml").read_text())
        self.assertIn("not a Pri-Fly decision", inventory)
        self.assertIn("when: {answers: {roadmap_linkage: link}}", (CLASSIC / "decisions" / "plan" / "roadmap-milestone.yaml").read_text())

    def test_the_commented_extension_example_would_compile(self):
        # A commented example is invisible to the compiler, so it rots while the
        # contract moves. The pilot uncommented this one and was refused.
        example = [line for line in (CLASSIC / "extend.yaml").read_text().splitlines() if line.startswith("#     on: {")]
        self.assertEqual(len(example), 1, example)
        for verdict in ("pass", "fail", "needs_revision", "no_work"):
            self.assertIn(verdict + ":", example[0], example[0])
        # The prose example rots the same way: it named `choose-verify` for a
        # release after that stage was gone, and a reader copying it was refused
        # `project_extension_unknown_stage`. Every stage a `between` names,
        # commented or not, has to exist in the root graph it points at.
        stages = {line[2:-1] for line in (CLASSIC / "workflow.yaml").read_text().splitlines() if re.fullmatch(r"  [a-z-]+:", line)}
        named = re.findall(r"between: \{from: ([a-z-]+), to: ([a-z-]+)\}", (CLASSIC / "extend.yaml").read_text())
        self.assertGreaterEqual(len(named), 2, named)
        for pair in named:
            for stage in pair:
                self.assertIn(stage, stages, f"extend.yaml names stage {stage!r}, which the root graph does not have")

    def test_classic_is_sequential_and_fanout_is_parallel(self):
        classic_workflows = sorted((CLASSIC / "workflows").rglob("*.yaml"))
        # The plan is what a repeat carries forward; everything else it binds is
        # constant, so a match on the plan alone keeps this check about ordering.
        self.assertEqual(sum(item.read_text().count("next_bindings: {plan: $iteration.plan") for item in classic_workflows), 2)
        self.assertFalse(any("kind: parallel" in item.read_text() for item in classic_workflows))
        fanout_workflows = sorted((FANOUT / "workflows").rglob("*.yaml"))
        self.assertTrue(any("kind: parallel" in item.read_text() for item in fanout_workflows))
        self.assertFalse(any("opus" in item.read_text() or "sonnet" in item.read_text() for item in fanout_workflows))

    def test_gate_needs_revision_reaches_the_existing_decision(self):
        for name in ("verify-once.yaml", "review-once.yaml"):
            workflow = (CLASSIC / "workflows" / name).read_text()
            self.assertIn("needs_revision: decide", workflow, name)
            self.assertNotIn("needs_revision: inconclusive", workflow, name)
        for name in ("aif-verify-bridge.yaml", "aif-review-bridge.yaml"):
            bridge = (CLASSIC / "contexts" / name).read_text()
            self.assertIn("with a usable gate takes that\n  same decision", bridge, name)


if __name__ == "__main__":
    unittest.main()
