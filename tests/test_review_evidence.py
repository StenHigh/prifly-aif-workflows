"""Meaningful negative coverage/freshness checks for W1; no LLM involved."""
import copy
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('review_evidence', ROOT / 'aif-review-evidence/files/evidence.py')
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


def config(base='0' * 40, method='command', required=True, **updates):
    return {'base_commit': base, 'round': 1, 'optional_policy': 'ignore', 'require_separate_session': False,
            'checks': [{'id': 'acceptance', 'description': 'Check declared behavior', 'method': method,
                        'required': required, 'enabled': True, 'applicable': True}], **updates}


def report(request, basis, status='executed', result='passed'):
    method = request['checks'][0]['method']
    return {'round': request['round'], 'request_digest': evidence.digest(evidence.encoded(request) + b'\n'), 'candidate': basis, 'session': 'shared',
            'model_profile': 'unavailable', 'model': None,
            'checks': [{'id': 'acceptance', 'status': status, 'result': result,
                        'reason': '' if result == 'passed' else 'Fixture dependency or defect',
                        'evidence': [{'method': method, 'tool': 'python' if method == 'command' else 'fixture-tool',
                                      'locator': 'python -B acceptance.py' if method == 'command' else 'fixture page/source',
                                      'observation': 'Actual fixture command exited zero',
                                      'exit_code': 0 if method == 'command' else None}] if status == 'executed' else []}]}


class CoverageTest(unittest.TestCase):
    def setUp(self):
        values = {'base_commit': '0' * 40, 'head_commit': '1' * 40, 'index_digest': 'sha256:' + '2' * 64, 'files_digest': 'sha256:' + '3' * 64}
        self.basis = {'algorithm': 'git-candidate/1', **values, 'digest': evidence.digest(evidence.encoded(values))}
        self.request = config()
        self.report = report(self.request, self.basis)

    def assess(self, request=None, report=None, current=None):
        return evidence.evaluate(request or self.request, self.basis, report or self.report, current or self.basis)

    def test_actual_pass_preserves_unavailable_model(self):
        result = self.assess()
        self.assertEqual(result['status'], 'warnings')
        self.assertFalse(result['blocking'])
        self.assertIn('not established', result['findings'][0])

    def test_missing_duplicate_unknown_and_method_substitution_block(self):
        mutations = [[], self.report['checks'] * 2,
                     [{**self.report['checks'][0], 'id': 'invented'}],
                     [{**self.report['checks'][0], 'evidence': [{**self.report['checks'][0]['evidence'][0], 'method': 'browser'}]}]]
        for checks in mutations:
            with self.subTest(checks=checks):
                self.assertEqual(self.assess(report={**self.report, 'checks': checks})['status'], 'blocked')

    def test_browser_requires_browser_method_and_actual_observations(self):
        cfg = config(method='browser')
        item = report(cfg, self.basis)
        self.assertNotEqual(self.assess(cfg, item)['status'], 'blocked')
        item['checks'][0]['evidence'][0]['method'] = 'code'
        self.assertEqual(self.assess(cfg, item)['status'], 'blocked')
        item = report(cfg, self.basis)
        item['checks'][0]['evidence'][0]['observation'] = ' '
        self.assertEqual(self.assess(cfg, item)['status'], 'blocked')

    def test_required_unavailable_is_not_defect_or_success(self):
        result = self.assess(report=report(self.request, self.basis, 'unavailable', 'not_run'))
        self.assertEqual(result['status'], 'blocked')
        self.assertFalse(result['blocking'])
        self.assertEqual(result['suggested_next'], 'continue')

    def test_optional_unavailable_policy(self):
        cfg = config(required=False)
        item = report(cfg, self.basis, 'unavailable', 'not_run')
        self.assertFalse(self.assess(cfg, item)['blocking'])
        cfg['optional_policy'] = 'stop'
        item = report(cfg, self.basis, 'unavailable', 'not_run')
        result = self.assess(cfg, item)
        self.assertTrue(result['blocking_owner_only'])

    def test_reader_cannot_disable_required_check(self):
        for status in ('excluded', 'not_applicable'):
            self.assertEqual(self.assess(report=report(self.request, self.basis, status, 'not_run'))['status'], 'blocked')
        cfg = copy.deepcopy(self.request)
        cfg['checks'][0]['enabled'] = False
        self.assertNotEqual(self.assess(cfg, report(cfg, self.basis, 'excluded', 'not_run'))['status'], 'blocked')

    def test_candidate_round_and_digest_tampering(self):
        for key, value in [('round', 2), ('candidate', {**self.basis, 'digest': 'sha256:' + 'a' * 64})]:
            self.assertEqual(self.assess(report={**self.report, key: value})['status'], 'blocked')
        changed = {**self.basis, 'files_digest': 'sha256:' + 'b' * 64}
        changed['digest'] = evidence.digest(evidence.encoded({k: changed[k] for k in ('base_commit', 'head_commit', 'index_digest', 'files_digest')}))
        self.assertEqual(self.assess(current=changed)['status'], 'blocked')

    def test_changed_criteria_with_same_ids_and_code_invalidate_report(self):
        cfg = copy.deepcopy(self.request)
        cfg['checks'][0]['description'] = 'A different acceptance requirement, same ID/method'
        self.assertEqual(self.assess(cfg, self.report)['status'], 'blocked')
        self.assertNotEqual(self.assess(cfg, report(cfg, self.basis))['status'], 'blocked')

    def test_nonzero_pass_and_empty_execution_evidence_block(self):
        item = copy.deepcopy(self.report)
        item['checks'][0]['evidence'][0]['exit_code'] = 1
        self.assertEqual(self.assess(report=item)['status'], 'blocked')
        item['checks'][0]['evidence'] = []
        self.assertEqual(self.assess(report=item)['status'], 'blocked')

    def test_failure_is_defect_and_separate_session_is_not_other_model(self):
        item = report(self.request, self.basis, result='failed')
        self.assertEqual(self.assess(report=item)['status'], 'failed')
        cfg = config(require_separate_session=True)
        self.assertEqual(self.assess(cfg)['status'], 'blocked')
        item = {**report(cfg, self.basis), 'session': 'separate'}
        result = self.assess(cfg, item)
        self.assertEqual(result['status'], 'warnings')
        self.assertIn('independent model not established', result['findings'][0])


class CandidateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='w1-candidate-')
        self.addCleanup(self.temp.cleanup)
        self.tree = Path(self.temp.name)
        self.git('init', '-q', '-b', 'main')
        (self.tree / 'tracked.txt').write_text('original\n')
        (self.tree / '.gitignore').write_text('ignored/\n')
        self.git('add', '.')
        self.git('-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Fixture')
        self.base = self.git('rev-parse', 'HEAD').strip()
        self.original = evidence.snapshot(self.tree, self.base)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.tree), *args], text=True)

    def test_dirty_index_untracked_delete_mode_and_head_change_basis(self):
        path = self.tree / 'tracked.txt'
        for action in ('dirty', 'index', 'untracked', 'delete', 'mode', 'head'):
            with self.subTest(action=action):
                self.git('reset', '--hard', '-q', self.base)
                if (self.tree / 'new.txt').exists(): (self.tree / 'new.txt').unlink()
                if action == 'dirty': path.write_text('dirty\n')
                elif action == 'index':
                    path.write_text('staged\n'); self.git('add', 'tracked.txt'); path.write_text('original\n')
                elif action == 'untracked': (self.tree / 'new.txt').write_text('new\n')
                elif action == 'delete': path.unlink()
                elif action == 'mode': path.chmod(0o755)
                elif action == 'head': self.git('-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '--allow-empty', '-qm', 'Next')
                self.assertNotEqual(evidence.snapshot(self.tree, self.base)['digest'], self.original['digest'])

    def test_outputs_outside_tree_and_ignored_cache_do_not_change_basis(self):
        (self.tree / 'ignored').mkdir()
        (self.tree / 'ignored/log').write_text('cache')
        self.assertEqual(evidence.snapshot(self.tree, self.base), self.original)

    def test_symlink_target_is_hashed_without_reading_external_contents(self):
        external = self.tree.parent / (self.tree.name + '-external')
        self.addCleanup(lambda: external.unlink(missing_ok=True))
        external.write_text('outside')
        (self.tree / 'link').symlink_to(external)
        before = evidence.snapshot(self.tree, self.base)
        external.write_text('changed outside')
        self.assertEqual(evidence.snapshot(self.tree, self.base), before)
        (self.tree / 'link').unlink(); (self.tree / 'link').symlink_to('another-target')
        self.assertNotEqual(evidence.snapshot(self.tree, self.base), before)

    def test_snapshot_is_read_only(self):
        before = self.git('status', '--porcelain=v1')
        evidence.snapshot(self.tree, self.base)
        self.assertEqual(self.git('status', '--porcelain=v1'), before)
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.base)


if __name__ == '__main__':
    unittest.main()
