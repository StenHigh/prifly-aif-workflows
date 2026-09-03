#!/usr/bin/env python3
"""Static contract of the AI Factory workflow folders: YAML only, distinct roles, pinned inventory."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLASSIC = ROOT / "aif-classic"
FANOUT = ROOT / "aif-fanout"


class WorkflowFolderTest(unittest.TestCase):
    def test_folders_are_marked_yaml_only_workflow_folders(self):
        for folder in (CLASSIC, FANOUT):
            workflow = (folder / "workflow.yaml").read_text()
            self.assertTrue(workflow.startswith("authoring: prifly-project-workflow/1\n"), folder)
            self.assertTrue((folder / "extend.yaml").is_file(), folder)
            self.assertEqual(list(folder.rglob("*.yaml.tmpl")), [])
            yaml_sources = [item.read_text() for item in folder.rglob("*.yaml")]
            self.assertFalse(any(line.strip() == "---" for source in yaml_sources for line in source.splitlines()), folder)

    def test_classic_decision_catalog_names_its_own_install_path(self):
        workflow = (CLASSIC / "workflow.yaml").read_text()
        self.assertIn("decision_catalog:", workflow)
        for line in workflow.splitlines():
            if line.startswith("  - .prifly/workflows/"):
                self.assertTrue(line.startswith("  - .prifly/workflows/aif-classic/decisions/"), line)
                self.assertTrue((CLASSIC / line.split("aif-classic/", 1)[1]).is_file(), line)

    def test_classic_inventory_pins_upstream_skills(self):
        inventory = (CLASSIC / "decisions" / "INVENTORY.md").read_text()
        for skill_hash in (
            "3be3c17f5478d15196832762d565c1d8d792666af4733f02b1d1d9bcf9002dbb",
            "aaad2183c302ead1d2ac7ddf216ad1259ef53b72f7b1d9d9214f84dcb235998a",
            "3dbeec8295c3cc592faf67d1669295803d472944c30ee7daeb8d330b0c9c9028",
        ):
            self.assertIn(skill_hash, inventory)
        self.assertIn("not a Pri-Fly decision", inventory)
        self.assertIn("when: {answers: {roadmap_linkage: link}}", (CLASSIC / "decisions" / "plan" / "roadmap-milestone.yaml").read_text())

    def test_classic_is_sequential_and_fanout_is_parallel(self):
        classic_workflows = sorted((CLASSIC / "workflows").rglob("*.yaml"))
        self.assertEqual(sum(item.read_text().count("next_bindings: {plan: $iteration.plan}") for item in classic_workflows), 2)
        self.assertFalse(any("kind: parallel" in item.read_text() for item in classic_workflows))
        fanout_workflows = sorted((FANOUT / "workflows").rglob("*.yaml"))
        self.assertTrue(any("kind: parallel" in item.read_text() for item in fanout_workflows))
        self.assertFalse(any("opus" in item.read_text() or "sonnet" in item.read_text() for item in fanout_workflows))


if __name__ == "__main__":
    unittest.main()
