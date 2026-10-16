"""W5 trust boundary: exact bytes/refs first, deterministic W1 assessment second."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'aif-feature/files'))
import parallel_reports as p
import feature
import parallel_host
from test_feature import task_input, captured, report


class ParallelReportTest(unittest.TestCase):
    def setUp(self):
        self.task = task_input()
        _, self.requests, _ = feature.begin(self.task, '0' * 40, 0, 'parallel-backend')
        self.candidate = captured()
        self.manifest = {'schema_version': '1', 'stage_activation_id': 'activation:fixture',
                         'selection_seq': 2, 'selected_branch_ids': list(p.READERS),
                         'join_result': 'satisfied', 'branches': []}
        self.bundle = {'schema_version': '1', 'manifest_digest': 'sha256:' + 'a' * 64,
                       'status': 'ready', 'reason': '', 'reports': []}
        for lens in p.READERS:
            value = report(self.requests[lens], self.candidate)
            value['session'] = 'separate'
            value['checks'][0]['id'] = self.requests[lens]['checks'][0]['id']
            # Whitespace/order are deliberately unlike the package serializer.
            raw = json.dumps(value, indent=3).encode() + b' \n'
            ref = {'artifact_id': 'artifact:' + lens, 'revision': 1, 'digest': p.w1.digest(raw)}
            self.manifest['branches'].append({'id': lens, 'run_id': 'run:fixture',
                'workflow_invocation_id': 'invocation:' + lens, 'status': 'completed',
                'outcome': 'succeeded', 'has_waivers': False, 'output_refs': {'report': ref}, 'effect_receipt_refs': []})
            self.bundle['reports'].append({'branch': lens, 'ref': copy.deepcopy(ref),
                                         'raw_base64': base64.b64encode(raw).decode()})

    def unpack(self):
        return p.unpack(self.manifest, 'sha256:' + 'a' * 64, self.bundle)

    def test_original_bytes_and_provenance_survive_transport(self):
        result = self.unpack()
        for entry in self.bundle['reports']:
            raw = base64.b64decode(entry['raw_base64'])
            self.assertEqual(p.w1.digest(raw), entry['ref']['digest'])
            self.assertNotEqual(raw, p.w1.encoded(result[entry['branch']]) + b'\n')
        self.assertEqual(list(result), list(p.READERS))

    def test_substituted_ref_is_rejected_even_with_same_content(self):
        self.bundle['reports'][0]['ref']['artifact_id'] = 'artifact:other'
        with self.assertRaises(p.w1.Invalid): self.unpack()

    def test_changed_bytes_do_not_pass_original_digest(self):
        self.bundle['reports'][0]['raw_base64'] = base64.b64encode(b'{}').decode()
        with self.assertRaises(p.w1.Invalid): self.unpack()

    def test_bundle_from_another_manifest_is_rejected(self):
        self.bundle['manifest_digest'] = 'sha256:' + 'b' * 64
        with self.assertRaises(p.w1.Invalid): self.unpack()

    def test_missing_duplicate_and_unknown_readers_block(self):
        original = copy.deepcopy(self.bundle)
        for entries in ([], original['reports'][:1], original['reports'] * 2,
                        list(reversed(original['reports'])), ['wrong']):
            self.bundle = {**original, 'reports': entries}
            with self.assertRaises(p.w1.Invalid): self.unpack()

    def test_unsettled_or_waived_join_never_allows_repair(self):
        original = copy.deepcopy(self.manifest)
        for key, val in (('status', 'running'), ('outcome', 'partial'), ('has_waivers', True)):
            self.manifest = copy.deepcopy(original)
            self.manifest['branches'][0][key] = val
            with self.assertRaises(p.w1.Invalid): self.unpack()
        self.manifest = copy.deepcopy(original)
        self.manifest['join_result'] = 'unsatisfied'
        with self.assertRaises(p.w1.Invalid): self.unpack()

    def test_one_artifact_cannot_impersonate_two_readers(self):
        self.manifest['branches'][1]['output_refs']['report'] = self.manifest['branches'][0]['output_refs']['report']
        with self.assertRaises(p.w1.Invalid): self.unpack()

    def test_unavailable_export_is_diagnostic(self):
        self.bundle = p.unavailable(self.bundle['manifest_digest'], 'Public export refused')
        with self.assertRaises(p.w1.Invalid): self.unpack()

    def test_invalid_encoding_and_duplicate_json_keys_are_rejected(self):
        original = self.bundle['reports'][0]['raw_base64']
        for value in (original + '\n', '**', 12):
            self.bundle['reports'][0]['raw_base64'] = value
            with self.assertRaises(p.w1.Invalid): self.unpack()
        with self.assertRaises(p.w1.Invalid): p.strict_json(b'{"round":1,"round":2}')
        with self.assertRaises(p.w1.Invalid): p.strict_json(b'{"round":NaN}')

    def test_digest_valid_stale_report_still_fails_w1(self):
        reports = self.unpack()
        reports['security']['round'] = 2
        gate = p.w1.evaluate(self.requests['security'], self.candidate, reports['security'], self.candidate)
        self.assertEqual(gate['status'], 'blocked')

    def test_parallel_requires_real_separate_reports_and_rejects_frontend(self):
        self.assertTrue(all(self.requests[lens]['require_separate_session'] for lens in p.READERS))
        reports = self.unpack(); reports['security']['session'] = 'shared'
        gate = p.w1.evaluate(self.requests['security'], self.candidate, reports['security'], self.candidate)
        self.assertEqual(gate['status'], 'blocked')
        with self.assertRaises(p.w1.Invalid): feature.configuration(task_input(True), 'frontend', 'parallel-backend')

    def test_host_controller_must_match_the_sealed_source_contract(self):
        files = {'parallel_host.py': Path(parallel_host.__file__), 'parallel_reports.py': Path(p.__file__),
                 'evidence.py': Path(p.w1.__file__)}
        contract = {'protocol': parallel_host.PROTOCOL, 'files': {name: p.w1.digest(path.read_bytes()) for name,path in files.items()}}
        with tempfile.TemporaryDirectory(prefix='w5-adapter-pin-') as directory:
            root = Path(directory); path = root/'context/skills/aif-feature-context-parallel-adapter-contract-1.0.0'
            path.parent.mkdir(parents=True)
            raw = p.w1.encoded(contract)
            path.write_bytes(raw)
            ref = {'id': 'aif-feature:context/parallel-adapter-contract', 'version': '1.0.0', 'digest': p.w1.digest(raw)}
            task = {'workspace': str(root), 'skill_refs': [ref]}
            parallel_host.verify_adapter(task)
            contract['files']['parallel_host.py'] = 'sha256:' + '0' * 64
            raw = p.w1.encoded(contract); path.write_bytes(raw); ref['digest'] = p.w1.digest(raw)
            with self.assertRaises(p.w1.Invalid): parallel_host.verify_adapter(task)
            path.write_bytes(b'{}')
            with self.assertRaises(p.w1.Invalid): parallel_host.verify_adapter(task)


if __name__ == '__main__': unittest.main()
