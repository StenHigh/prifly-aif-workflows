#!/usr/bin/env python3
"""Every published byte carries a version that moved with it, measured against the last release.

A consumer pins a component by `id@version` and a package by its version. Serving
different bytes under a version it already holds is invisible to it: the content
arrives, nothing says it changed.
"""

from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("aif-classic", "aif-fanout")


def git(*arguments, ok=(0,)):
    result = subprocess.run(["git", "-C", str(ROOT), *arguments], capture_output=True, text=True)
    if result.returncode not in ok:
        raise AssertionError(f"git {' '.join(arguments)}: {result.stderr.strip()}")
    return result.stdout


def declared_version(source):
    for line in source.splitlines():
        if line.startswith("version: "):
            return line[len("version: ") :].strip()
    return None


def released_source(tag, path):
    result = subprocess.run(["git", "-C", str(ROOT), "show", f"{tag}:{path}"], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


class ReleasedVersionTest(unittest.TestCase):
    def setUp(self):
        # No release yet means no version anyone can already hold. A shallow
        # clone reaches no tag either, so CI checks out the full history.
        self.tag = git("describe", "--tags", "--abbrev=0", "--match", "v*", ok=(0, 128)).strip()
        if not self.tag:
            self.skipTest("no release tag is reachable from HEAD")
        self.changed = [path for path in git("diff", "--name-only", self.tag).splitlines() if path.split("/")[0] in PACKAGES]

    def test_a_changed_component_declares_a_new_version(self):
        for path in self.changed:
            if not path.endswith(".yaml"):
                continue
            released = released_source(self.tag, path)
            current = (ROOT / path).read_text() if (ROOT / path).is_file() else None
            if released is None or current is None:
                continue  # Added or removed: the package version below carries it.
            before, after = declared_version(released), declared_version(current)
            if before is None and after is None:
                continue  # Decision definitions are identified by their digest.
            self.assertNotEqual(before, after, f"{path} changed since {self.tag} while it still declares {before}")

    def test_a_changed_package_declares_a_new_package_version(self):
        for package in PACKAGES:
            if not any(path.startswith(f"{package}/") and path.endswith(".yaml") for path in self.changed):
                continue
            manifest = f"{package}/workflow.yaml"
            released = released_source(self.tag, manifest)
            self.assertIsNotNone(released, manifest)
            current = (ROOT / manifest).read_text()
            for field in ("  version: ", "version: "):
                before = next((line for line in released.splitlines() if line.startswith(field)), None)
                after = next((line for line in current.splitlines() if line.startswith(field)), None)
                self.assertNotEqual(before, after, f"{package} changed since {self.tag} while {manifest} still declares {before!r}")


if __name__ == "__main__":
    unittest.main()
