"""Changed-test selection and acceptance against real Git trees, without an LLM."""
import copy
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

FILES = Path(__file__).resolve().parents[1] / 'openclaw-test-audit/files'
sys.path.insert(0, str(FILES))
spec = importlib.util.spec_from_file_location('test_audit_worker', FILES / 'audit.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
sys.path.pop(0)


def git(tree, *args):
    return subprocess.run(['git', '-c', 'user.name=Audit fixture', '-c', 'user.email=audit@example.invalid',
                           '-c', 'commit.gpgsign=false', '-C', str(tree), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def settings(base):
    return {'base_commit': base, 'round': 1, 'test_patterns': ['tests/*', '*.test.js'],
            'require_separate_session': False}


def report(request, status='passed'):
    return {'request_digest': a.digest(a.encoded(request) + b'\n'), 'candidate': copy.deepcopy(request['candidate']),
            'round': request['config']['round'], 'session': 'unavailable', 'model': None, 'skip_reason': '',
            'files': [{'path': path, 'status': status,
                       'behavior': 'Fixture assertion protects the public greeting response.',
                       'regression': 'A missing greeting would fail; baseline not executed by this synthetic host.',
                       'existing_proof': 'Fixture has no other greeting assertion.',
                       'evidence': [{'locator': path, 'observation': 'Synthetic host observation; no LLM judgement claimed.'}],
                       'findings': [] if status == 'passed' else ['Concrete fixture defect' if status == 'failed' else 'Required owner source unavailable']}
                      for path in request['paths']]}


class AuditTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='audit-unit-')
        self.addCleanup(self.directory.cleanup)
        self.tree = Path(self.directory.name)
        git(self.tree, 'init', '-q', '-b', 'main')
        (self.tree / 'tests').mkdir()
        self.test = self.tree / 'tests/test_greeting.py'
        self.test.write_text('def test_greeting():\n    assert greet() == "Hello"\n')
        (self.tree / 'greeting.py').write_text('def greet():\n    return "Hello"\n')
        (self.tree / '.gitignore').write_text('tests/cache/\n')
        git(self.tree, 'add', '.')
        git(self.tree, 'commit', '-qm', 'Independent baseline')
        self.config = settings(git(self.tree, 'rev-parse', 'HEAD'))

    def changed(self):
        self.test.write_text(self.test.read_text() + 'def test_name():\n    assert greet("Ada") == "Hello Ada"\n')
        return a.prepare(self.tree, self.config)

    def evaluate(self, request, value):
        return a.evaluate(self.tree, request, value, a.digest(a.encoded(request) + b'\n'))

    def test_original_base_covers_committed_dirty_index_and_new_test_files(self):
        self.changed()
        git(self.tree, 'add', '.')
        git(self.tree, 'commit', '-qm', 'Test added in existing file')
        (self.tree / 'tests/new.py').write_text('assert greeting()\n')
        (self.tree / 'tests/nested').mkdir()
        (self.tree / 'tests/nested/proof.py').write_text('assert greeting()\n')
        (self.tree / 'tests/cache').mkdir()
        (self.tree / 'tests/cache/ignored.py').write_text('ignored cache\n')
        (self.tree / 'greeting.py').write_text('changed production code\n')
        self.assertEqual(a.prepare(self.tree, self.config)['paths'],
                         ['tests/nested/proof.py', 'tests/new.py', 'tests/test_greeting.py'])

    def test_staged_test_change_is_visible_even_if_worktree_reverses_it(self):
        original = self.test.read_text()
        self.changed()
        git(self.tree, 'add', str(self.test))
        self.test.write_text(original)
        self.assertEqual(a.prepare(self.tree, self.config)['paths'], ['tests/test_greeting.py'])

    def test_deleted_and_renamed_tests_remain_auditable(self):
        self.test.rename(self.tree / 'tests/renamed.py')
        self.assertEqual(a.prepare(self.tree, self.config)['paths'], ['tests/renamed.py', 'tests/test_greeting.py'])
        git(self.tree, 'add', '.')
        self.assertEqual(a.prepare(self.tree, self.config)['paths'], ['tests/renamed.py', 'tests/test_greeting.py'])

    def test_no_test_change_has_explicit_skip(self):
        (self.tree / 'greeting.py').write_text('production change only\n')
        request = a.prepare(self.tree, self.config)
        self.assertEqual(request['paths'], [])
        skip = a.skipped(request)
        self.assertEqual(skip['session'], 'not_run')
        self.assertTrue(skip['skip_reason'])
        self.assertEqual(skip['files'], [])

    def test_clean_defect_and_unavailable_reports_produce_distinct_gates(self):
        request = self.changed()
        for status, expected in [('passed', 'passed'), ('failed', 'failed'), ('unavailable', 'blocked')]:
            with self.subTest(status=status):
                self.assertEqual(self.evaluate(request, report(request, status))['status'], expected)

    def test_reader_cannot_omit_duplicate_or_change_paths_or_forge_basis(self):
        request = self.changed()
        cases = []
        value = report(request); value['files'] = []; cases.append(value)
        value = report(request); value['files'] *= 2; cases.append(value)
        value = report(request); value['files'][0]['path'] = 'greeting.py'; cases.append(value)
        value = report(request); value['candidate']['digest'] = 'sha256:' + '1' * 64; cases.append(value)
        value = report(request); value['request_digest'] = 'sha256:' + '2' * 64; cases.append(value)
        value = report(request); value['round'] += 1; cases.append(value)
        value = report(request); value['files'][0]['evidence'] = []; cases.append(value)
        value = report(request); value['files'][0]['findings'] = ['Defect hidden behind passed']; cases.append(value)
        for value in cases:
            with self.subTest(report=value):
                self.assertEqual(self.evaluate(request, value)['status'], 'blocked')
        (self.tree / 'tests/second.py').write_text('assert greet("Ada") == "Hello Ada"\n')
        request = a.prepare(self.tree, self.config)
        value = report(request)
        self.assertEqual(len(value['files']), 2)
        value['files'][1] = copy.deepcopy(value['files'][0])
        self.assertEqual(self.evaluate(request, value)['status'], 'blocked')

    def test_production_edit_invalidates_previously_accepted_test_audit(self):
        request = self.changed()
        value = report(request)
        self.assertEqual(self.evaluate(request, value)['status'], 'passed')
        (self.tree / 'greeting.py').write_text('def greet():\n    return "Broken"\n')
        self.assertEqual(self.evaluate(request, value)['status'], 'blocked')

    def test_index_untracked_delete_and_mode_edits_invalidate_evidence(self):
        for change in ('index', 'untracked', 'delete', 'mode'):
            with self.subTest(change=change):
                request = self.changed(); value = report(request)
                if change == 'index': git(self.tree, 'add', '.')
                elif change == 'untracked': (self.tree / 'new-owner-file').write_text('owner work\n')
                elif change == 'delete': (self.tree / 'greeting.py').unlink()
                elif change == 'mode': self.test.chmod(0o755)
                self.assertEqual(self.evaluate(request, value)['status'], 'blocked')
                git(self.tree, 'reset', '--hard', self.config['base_commit'])
                git(self.tree, 'clean', '-fd')

    def test_session_requirement_is_explicit_and_does_not_claim_another_model(self):
        self.config['require_separate_session'] = True
        request = self.changed(); value = report(request)
        self.assertEqual(self.evaluate(request, value)['status'], 'blocked')
        value['session'] = 'separate'
        self.assertEqual(self.evaluate(request, value)['status'], 'passed')
        self.assertIsNone(value['model'])

    def test_invalid_base_patterns_and_unmerged_index_do_not_skip(self):
        for field, value in [('base_commit', 'HEAD'), ('test_patterns', []), ('test_patterns', ['/tests/*']),
                             ('test_patterns', ['../outside/*'])]:
            settings = copy.deepcopy(self.config); settings[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(a.Invalid):
                a.prepare(self.tree, settings)
        git(self.tree, 'checkout', '-qb', 'other')
        self.test.write_text('other\n'); git(self.tree, 'commit', '-qam', 'Other test')
        git(self.tree, 'checkout', '-q', 'main')
        self.test.write_text('main\n'); git(self.tree, 'commit', '-qam', 'Main test')
        merged = subprocess.run(['git', '-c', 'user.name=Audit fixture', '-c', 'user.email=audit@example.invalid',
                                 '-C', str(self.tree), 'merge', 'other'], capture_output=True, check=False)
        self.assertNotEqual(merged.returncode, 0)
        self.assertIn('tests/test_greeting.py', git(self.tree, 'diff', '--name-only', '--diff-filter=U'))
        with self.assertRaises(a.Invalid):
            a.prepare(self.tree, self.config)


if __name__ == '__main__':
    unittest.main()
