"""Project installation boundaries and whole-candidate acceptance, no model claims."""

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "examples/review-uiux-extensions"
sys.path.insert(0, str(HERE))
import install


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


evidence = module("evidence", HERE / "bundle/project/files/w6-evidence.py")
sys.modules["evidence"] = evidence
product = module("product", HERE / "bundle/project/files/w6-product.py")
sys.modules["product"] = product
adapter = module("acceptance", HERE / "acceptance.py")


class Installation(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="w6-unit-")
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repo"
        self.folder = self.repo / ".prifly/workflows/aif-classic"
        shutil.copytree(ROOT / "aif-classic", self.folder)
        (self.repo / ".prifly/project.yaml").write_text(
            json.dumps(
                {
                    "schema_version": "prifly-project-profile/2",
                    "owner_setting": "preserve",
                }
            )
        )
        self.config = HERE / "configurations/review.json"

    def plan(self, **overrides):
        args = dict(
            repository=self.repo,
            package="aif-classic",
            configuration=self.config,
            mode="review",
            after="review",
            before="commit",
            failure="abandoned",
            finish="done",
            port="implementation",
        )
        return install.plan(**{**args, **overrides})

    def test_preserves_root_and_existing_overlay_and_profile4(self):
        original = (self.folder / "workflow.yaml").read_bytes()
        extension = install.load((self.folder / "extend.yaml").read_text())
        extension["profile"] = "fast"
        extension["exclude"] = ["improve"]
        (self.folder / "extend.yaml").write_text(json.dumps(extension))
        profile = self.repo / ".prifly/project.yaml"
        profile.write_text(
            json.dumps(
                {
                    "schema_version": "prifly-project-profile/4",
                    "worktree_names": {"owner": "kept"},
                }
            )
        )
        summary, changes = self.plan()
        backup = install.apply(self.repo, summary, changes)
        self.addCleanup(shutil.rmtree, backup)
        self.assertEqual((self.folder / "workflow.yaml").read_bytes(), original)
        self.assertEqual(
            install.load(profile.read_text())["schema_version"],
            "prifly-project-profile/4",
        )
        self.assertEqual(
            install.load((self.folder / "extend.yaml").read_text())["exclude"],
            ["improve"],
        )
        with self.assertRaisesRegex(ValueError, "already installed"):
            self.plan()

    def test_invalid_placement_and_success_failure_refused_without_writes(self):
        for override in (
            {"after": "missing"},
            {"after": "warmup"},
            {"failure": "done"},
        ):
            with self.subTest(override=override), self.assertRaises(ValueError):
                self.plan(**override)
        self.assertFalse((self.folder / "project").exists())

    def test_reviewed_source_drift_refused(self):
        summary, changes = self.plan()
        (self.folder / "workflow.yaml").write_text(
            "# changed\n" + (self.folder / "workflow.yaml").read_text()
        )
        with self.assertRaisesRegex(ValueError, "root changed"):
            install.apply(self.repo, summary, changes)
        self.assertFalse((self.folder / "project").exists())

    def test_concurrent_owner_change_rolls_back_own_additions(self):
        summary, changes = self.plan()
        extend = self.folder / "extend.yaml"
        extend.write_text("extensions: []\n# owner edit\n")
        with self.assertRaisesRegex(ValueError, "changed after preview"):
            install.apply(self.repo, summary, changes)
        self.assertIn("owner edit", extend.read_text())
        self.assertFalse(any((self.folder / "project").rglob("*.yaml")))

    def test_schema_invalid_configuration_refused(self):
        settings = json.loads(self.config.read_text())
        settings["review"]["checks"][0]["method"] = "invented"
        path = Path(self.temporary.name) / "invalid.json"
        path.write_text(json.dumps(settings))
        with self.assertRaises(ValueError):
            self.plan(configuration=path)

    def test_alias_and_file_collision_refused(self):
        extend = self.folder / "extend.yaml"
        extend.write_text(
            json.dumps(
                {
                    "extensions": [],
                    "references": {"w6-process": "owner:adapter/process@1.0.0"},
                }
            )
        )
        with self.assertRaisesRegex(ValueError, "alias conflict"):
            self.plan()
        extend.write_text("extensions: []\n")
        path = self.folder / "project/files/w6-evidence.py"
        path.parent.mkdir(parents=True)
        path.write_text("owner bytes")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.plan()
        self.assertEqual(path.read_text(), "owner bytes")


class Freshness(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="w6-candidate-")
        self.addCleanup(self.temporary.cleanup)
        self.tree = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.tree / "source.txt").write_text("base\n")
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD")
        (self.tree / "source.txt").write_text("candidate\n")
        (self.tree / "untracked.txt").write_text("also reviewed\n")
        self.implementation = {
            "base_commit": self.base,
            "head_commit": self.base,
            "changed_files": ["source.txt", "untracked.txt"],
        }
        self.settings = json.loads((HERE / "configurations/review.json").read_text())
        self.prepared = adapter.prepare(
            self.settings, self.implementation, self.tree, "review"
        )

    def git(self, *args):
        return subprocess.check_output(
            ["git", "-C", str(self.tree), *args], text=True
        ).strip()

    def receipt(self):
        return adapter.seal(
            {
                **self.prepared,
                "review_gate": {
                    "status": "passed",
                    "blocking": False,
                    "blocking_owner_only": False,
                },
            },
            self.tree,
            "run:original",
            b"config",
            {},
        )

    def test_new_continue_run_preserves_accepted_receipt_and_files(self):
        receipt = self.receipt()
        self.git("add", ".")
        self.git("commit", "-qm", "candidate")
        implementation = {
            **self.implementation,
            "head_commit": self.git("rev-parse", "HEAD"),
        }
        self.assertEqual(
            adapter.committed(receipt, implementation, self.tree, "run:continued"),
            receipt,
        )

    def test_untracked_edit_after_review_blocks_seal(self):
        (self.tree / "untracked.txt").write_text("unreviewed\n")
        with self.assertRaisesRegex(ValueError, "Candidate changed"):
            self.receipt()

    def test_change_after_acceptance_blocks_post_commit_finish(self):
        receipt = self.receipt()
        (self.tree / "source.txt").write_text("unreviewed\n")
        self.git("add", ".")
        self.git("commit", "-qm", "race")
        with self.assertRaisesRegex(ValueError, "Files differ"):
            adapter.committed(
                receipt,
                {**self.implementation, "head_commit": self.git("rev-parse", "HEAD")},
                self.tree,
                "run:original",
            )

    def test_unavailable_or_owner_gate_cannot_seal(self):
        for gate in (
            {"status": "blocked", "blocking": False, "blocking_owner_only": False},
            {"status": "warnings", "blocking": False, "blocking_owner_only": True},
        ):
            with self.subTest(gate=gate), self.assertRaises(ValueError):
                adapter.seal(
                    {**self.prepared, "review_gate": gate},
                    self.tree,
                    "run:one",
                    b"config",
                    {},
                )


if __name__ == "__main__":
    unittest.main()
