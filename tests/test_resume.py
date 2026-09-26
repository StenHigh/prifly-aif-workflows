#!/usr/bin/env python3
"""The continuation tails' resume program, run the way Pri-Fly runs it: envelope
on stdin, context.json by PRIFLY_CONTEXT_FILE, result on fd 3, the claimed tree
by PRIFLY_REPOSITORY_WORKSPACE and PATH=/usr/bin:/bin."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "tools" / "continuation" / "resume.mjs"
NODE = shutil.which("node")


def git(cwd, *arguments):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *arguments], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


@unittest.skipUnless(NODE, "the resume step's executable is node")
class ResumeProgramTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="aif-resume-"))
        self.tree = self.root / "tree"
        self.tree.mkdir()
        git(self.tree, "init", "-q", "-b", "main")
        (self.tree / "a.txt").write_text("a\n")
        git(self.tree, "add", "a.txt")
        git(self.tree, "commit", "-q", "-m", "base")
        self.base = git(self.tree, "rev-parse", "HEAD")
        (self.tree / "b.txt").write_text("b\n")
        git(self.tree, "add", "b.txt")
        git(self.tree, "commit", "-q", "-m", "implement")
        self.head = git(self.tree, "rev-parse", "HEAD")

    def tearDown(self):
        shutil.rmtree(self.root)

    def resume(self, previous, workspace=True):
        work = self.root / "attempt"
        work.mkdir(exist_ok=True)
        (work / "previous.json").write_text(json.dumps(previous))
        context = {"inputs": {"previous_implementation": {"path": str(work / "previous.json")}},
                   "outputs": {"implementation": {"artifact_id": "artifact:x", "revision": 1, "path": str(work / "implementation")}}}
        (work / "context.json").write_text(json.dumps(context))
        env = {"PATH": "/usr/bin:/bin", "PRIFLY_CONTEXT_FILE": str(work / "context.json"), "PRIFLY_ENVELOPE_DIGEST": "sha256:e"}
        if workspace:
            env["PRIFLY_REPOSITORY_WORKSPACE"] = str(self.tree)
        envelope = json.dumps({"run_id": "run:r", "step_instance_id": "step:s", "attempt_id": "attempt:a"})
        channel = work / "result.json"  # fd 3, the result channel
        process = subprocess.run(["/bin/sh", "-c", 'exec "$0" "$1" 3>"$2"', NODE, str(PROGRAM), str(channel)],
                                 input=envelope, capture_output=True, text=True, env=env)
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(channel.read_text())
        implementation = work / "implementation"
        return result, json.loads(implementation.read_text()) if implementation.exists() and result["verdict"] == "pass" else None

    def test_the_tree_as_left_is_described_uncommitted_files_included(self):
        (self.tree / "c.txt").write_text("fix in progress\n")
        result, implementation = self.resume({"base_commit": self.base, "head_commit": self.head, "changed_files": ["b.txt"]})
        self.assertEqual(result["verdict"], "pass", result["summary"])
        self.assertEqual(implementation, {"base_commit": self.base, "head_commit": self.head, "changed_files": ["b.txt", "c.txt"]})
        self.assertTrue(result["outputs"]["implementation"]["digest"].startswith("sha256:"))

    def test_a_tree_without_the_source_implementation_fails(self):
        git(self.tree, "reset", "-q", "--hard", self.base)
        result, _ = self.resume({"base_commit": self.base, "head_commit": self.head, "changed_files": ["b.txt"]})
        self.assertEqual(result["verdict"], "fail", result["summary"])
        self.assertIn(self.head, result["summary"])
        self.assertEqual(result["outputs"], {})

    def test_no_claimed_tree_is_blocked_not_failed(self):
        result, _ = self.resume({"base_commit": self.base, "head_commit": self.head, "changed_files": ["b.txt"]}, workspace=False)
        self.assertEqual(result["verdict"], "blocked", result["summary"])
        self.assertIn("PRIFLY_REPOSITORY_WORKSPACE", result["summary"])


if __name__ == "__main__":
    unittest.main()
