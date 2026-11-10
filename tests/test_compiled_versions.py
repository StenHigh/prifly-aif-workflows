#!/usr/bin/env python3
"""The compiled release guard must fail on the dependency-only drift it guards."""

import json
from pathlib import Path
import tempfile
import unittest

from compiled_versions import check_collisions, fingerprint, previous_release, read_components
from verify import git


def step(version="1.1.0", instruction="1.1.0", schema="1.0.0", source="old"):
    document = {"id": "aif:step/fix", "version": version,
                "instructions_ref": {"id": "aif:context/aif-fix-bridge", "version": instruction},
                "inputs": {"gate": {"schema_ref": {"id": "aif:schema/gate-result", "version": schema}}}}
    return {"kind": "step", "id": document["id"], "version": version,
            "digest": fingerprint(json.dumps(document, sort_keys=True).encode()), "source": source}


class CompiledVersionTest(unittest.TestCase):
    def test_same_identity_and_bytes_are_reusable(self):
        self.assertEqual(check_collisions([step(), step(source="new")]), 1)

    def test_only_instruction_changed_refuses_same_step_version(self):
        with self.assertRaisesRegex(ValueError, "compiled_definition_drift: step aif:step/fix@1.1.0: old.*new"):
            check_collisions([step(), step(instruction="1.4.0", source="new")])

    def test_only_schema_changed_refuses_same_step_version(self):
        with self.assertRaisesRegex(ValueError, "compiled_definition_drift"):
            check_collisions([step(), step(schema="1.1.0", source="new")])

    def test_compiler_assigned_new_version_is_allowed(self):
        self.assertEqual(check_collisions([step(), step(version="0.0.0-b2.new", instruction="1.4.0")]), 2)

    def test_collision_is_detected_across_nonadjacent_builds(self):
        with self.assertRaisesRegex(ValueError, "compiled_definition_drift"):
            check_collisions([step(), step(version="2.0.0"), step(schema="1.1.0")])

    def test_different_id_does_not_collide(self):
        other = {**step(instruction="1.4.0"), "id": "aif:step/other"}
        self.assertEqual(check_collisions([step(), other]), 2)

    def test_empty_measurement_is_not_success(self):
        with self.assertRaisesRegex(ValueError, "No compiled components"):
            check_collisions([])
        with self.assertRaisesRegex(ValueError, "no compiled components"):
            read_components({"components": []}, Path("."), "empty")

    def test_digest_is_checked_against_actual_document(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            raw = b'{"id":"aif:step/fix","version":"1.1.0"}\n'
            (output / "fix.json").write_bytes(raw)
            component = {"kind": "step", "path": "fix.json", "ref": {
                "id": "aif:step/fix", "version": "1.1.0", "digest": fingerprint(raw)}}
            read_components({"components": [component]}, output, "valid")
            (output / "fix.json").write_bytes(raw + b" ")
            with self.assertRaisesRegex(ValueError, "differs from the compiler digest"):
                read_components({"components": [component]}, output, "tampered")

    def test_raw_context_bytes_are_measured(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            raw = b"# Fix instructions\n"
            (output / "fix.md").write_bytes(raw)
            component = {"kind": "context", "path": "fix.md", "ref": {
                "id": "aif:context/aif-fix-bridge", "version": "1.1.0", "digest": fingerprint(raw)}}
            self.assertEqual(read_components({"components": [component]}, output, "context")[0]["digest"], fingerprint(raw))

    def test_tag_pipeline_compares_to_previous_tag(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            git("-C", repository, "init", "-q", "-b", "main")
            git("-C", repository, "commit", "--allow-empty", "-qm", "first")
            git("-C", repository, "tag", "v1.0.0")
            git("-C", repository, "commit", "--allow-empty", "-qm", "candidate")
            self.assertEqual(previous_release(repository), "v1.0.0")
            git("-C", repository, "tag", "v1.1.0")
            self.assertEqual(previous_release(repository), "v1.0.0")
            git("-C", repository, "commit", "--allow-empty", "-qm", "prerelease")
            git("-C", repository, "tag", "v1.2.0-rc1")
            self.assertEqual(previous_release(repository), "v1.1.0")


if __name__ == "__main__":
    unittest.main()
