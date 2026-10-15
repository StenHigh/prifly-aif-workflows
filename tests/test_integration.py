"""Meaningful W4 stale acceptance, semantic merge and interrupted-write cases."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from integration_fixture import accepted, fixture, i, FakeGitLab, publication


class IntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='w4-unit-')
        self.root = Path(self.temp.name)
        self.sessions = []

    def tearDown(self):
        for item in self.sessions:
            if item['session'] and Path(item['session']['path']).exists():
                # Only owned sessions from this exact fixture; unresolved writes
                # are inspected below, not cleaned via a production retry.
                path = i.owned(item)
                import shutil
                shutil.rmtree(path)
        self.temp.cleanup()

    def prepare(self, case='ready'):
        source, handoff, before = fixture(self.root, case=case)
        assessment, request, basis = i.prepare(source, handoff, 'owned-unit-fixture')
        self.sessions.append(assessment)
        self.assertEqual(i.w1.snapshot(source, before['base_commit']), before)
        return source, handoff, assessment, request, basis

    def test_semantic_regression_with_no_text_conflict(self):
        _, _, assessment, _, basis = self.prepare('semantic-regression')
        self.assertIsNotNone(basis)
        self.assertEqual(assessment['status'], 'needs_revision')
        self.assertEqual(assessment['checks'][0]['exit_code'], 1)
        self.assertIn('AssertionError: 4', assessment['checks'][0]['stderr'])

    def test_conflict_preserves_source(self):
        _, _, assessment, _, basis = self.prepare('conflict')
        self.assertIsNone(basis)
        self.assertEqual(assessment['status'], 'needs_revision')
        self.assertIn('Merge conflict', assessment['findings'][0])

    def test_merge_tool_error_is_unavailable_not_a_conflict(self):
        source, handoff, _ = fixture(self.root, case='unrelated-target')
        assessment, _, basis = i.prepare(source, handoff, 'unavailable-merge-fixture')
        self.sessions.append(assessment)
        self.assertIsNone(basis)
        self.assertEqual(assessment['status'], 'unavailable')
        self.assertIn('unrelated histories', assessment['findings'][0])

    def test_risk_owner_decision_binds_exact_policy_and_commits(self):
        source, handoff, assessment, _, _ = self.prepare('risk')
        self.assertEqual(assessment['status'], 'owner_required')
        i.release(assessment)
        handoff['risk_approval'] = {'candidate_commit': handoff['candidate_commit'], 'target_commit': handoff['target']['commit'],
                                  'policy_digest': i.w1.digest(i.w1.encoded(handoff['policy'])), 'categories': ['migrations'],
                                  'reference': 'fixture-owner-decision', 'reason': 'Owner inspected the named migration'}
        result, _, _ = i.prepare(source, handoff, 'approved-fixture')
        self.sessions.append(result)
        self.assertEqual(result['status'], 'ready')
        i.release(result)
        handoff['policy']['declared_risks'].append({'category': 'business_assumptions', 'reason': 'A business requirement changed'})
        changed, _, _ = i.prepare(source, handoff, 'changed-policy-fixture')
        self.sessions.append(changed)
        self.assertEqual(changed['status'], 'owner_required')

    def test_stale_source_report_is_not_ready(self):
        source, handoff, _ = fixture(self.root)
        handoff['acceptance'][0]['report']['request_digest'] = 'sha256:' + '1' * 64
        result, _, _ = i.prepare(source, handoff, 'stale-fixture')
        self.sessions.append(result)
        self.assertEqual(result['status'], 'unavailable')
        self.assertIsNone(result['session'])

    def test_changed_criteria_cannot_use_an_old_acceptance_for_write(self):
        source, handoff, _ = fixture(self.root)
        handoff['mode'] = 'local_merge'
        assessment = accepted(source, handoff)
        self.sessions.append(assessment)
        changed = copy.deepcopy(handoff)
        changed['spot_checks'][0]['description'] = 'A different acceptance requirement'
        value = i.local_merge(source, changed, assessment)
        self.assertEqual(value['status'], 'unavailable')
        self.assertIsNone(value['operation'])
        self.assertEqual(i.target_head(handoff), handoff['target']['commit'])

    def test_integrated_check_edit_invalidates_report(self):
        source, handoff, _ = fixture(self.root)
        handoff['integrated_checks'][0]['argv'] = ['python3', '-B', '-c', 'from pathlib import Path; Path("value.py").write_text("VALUE = 9\\n")']
        result, _, _ = i.prepare(source, handoff, 'editing-check-fixture')
        self.sessions.append(result)
        self.assertEqual(result['status'], 'unavailable')
        self.assertIn('Integration tree moved', result['findings'][-1])

    def test_lost_ack_after_local_cas_is_reconciled_without_retry(self):
        source, handoff, _ = fixture(self.root)
        handoff['mode'] = 'local_merge'
        assessment = accepted(source, handoff)
        self.sessions.append(assessment)
        original = i.command
        def lose_ack(tree, *args, **kwargs):
            result = original(tree, *args, **kwargs)
            if args[0] == 'update-ref':
                raise OSError('Ack lost after successful atomic Git update')
            return result
        with mock.patch.object(i, 'command', side_effect=lose_ack):
            value = i.local_merge(source, handoff, assessment)
        self.assertEqual(value['status'], 'reconcile_required')
        self.assertEqual(i.reconcile(value)['status'], 'applied')
        self.assertEqual(i.release(value)['cleanup'], 'reconcile_required')
        self.assertEqual(i.target_head(handoff), assessment['integration_head'])

    def test_target_race_at_cas_preserves_foreign_commit(self):
        source, handoff, _ = fixture(self.root)
        handoff['mode'] = 'local_merge'
        assessment = accepted(source, handoff)
        self.sessions.append(assessment)
        original = i.command
        def race(tree, *args, **kwargs):
            if args[0] == 'update-ref':
                original(tree, 'update-ref', handoff['target']['ref'], handoff['candidate_commit'])
            return original(tree, *args, **kwargs)
        with mock.patch.object(i, 'command', side_effect=race):
            result = i.local_merge(source, handoff, assessment)
        self.assertEqual(result['operation']['status'], 'not_applied')
        self.assertEqual(result['status'], 'owner_required')
        self.assertEqual(i.target_head(handoff), handoff['candidate_commit'])

    def test_cleanup_refuses_foreign_owner(self):
        _, _, assessment, _, _ = self.prepare()
        foreign = copy.deepcopy(assessment)
        foreign['session']['marker']['owner'] = 'foreign'
        self.assertEqual(i.release(foreign)['cleanup'], 'reconcile_required')
        self.assertTrue(Path(assessment['session']['path']).exists())

    def test_retained_unknown_operation_blocks_a_new_prepare(self):
        source, handoff, assessment, _, _ = self.prepare()
        held = i.diagnostic(copy.deepcopy(assessment), 'reconcile_required', 'Unknown publication result')
        self.assertEqual(i.release(held)['cleanup'], 'reconcile_required')
        next_assessment, _, basis = i.prepare(source, handoff, 'new-attempt-after-unknown')
        self.assertEqual(next_assessment['status'], 'reconcile_required')
        self.assertIsNone(basis)
        self.assertEqual(next_assessment['session'], assessment['session'])
        self.assertTrue(Path(assessment['session']['path']).exists())


class PublicationTest(unittest.TestCase):
    def setUp(self):
        self.spec = {'title': 'Draft: TRK-1 · Feature', 'body': 'Owned integration handoff', 'identity': 'owner-one',
                     'candidate_commit': '1' * 40, 'target_commit': '2' * 40, 'handoff_digest': 'sha256:' + '3' * 64,
                     'source_branch': 'feature', 'target_branch': 'main', 'project': 'fixture-project'}

    def test_one_draft_repeat_and_human_text_preserved(self):
        client = FakeGitLab(self.spec['target_commit'])
        first = publication.publish(client, self.spec)
        self.assertEqual(first['status'], 'created')
        self.assertEqual(client.mrs[0]['title'], self.spec['title'])
        client.mrs[0]['body'] += '\nHuman note'
        client.mrs[0]['revision'] += 1
        self.assertEqual(publication.publish(client, self.spec)['status'], 'reused')
        self.assertEqual(client.create_calls, 1)
        self.assertIn('Human note', client.mrs[0]['body'])

    def test_lost_ack_discovers_the_created_mr(self):
        client = FakeGitLab(self.spec['target_commit'], lose_ack=True)
        value = publication.publish(client, self.spec)
        self.assertEqual(value['status'], 'reused')
        self.assertIsNotNone(value['url'])
        self.assertEqual(client.create_calls, 1)

    def test_format_failure_is_existing_write_and_addressed_repair(self):
        client = FakeGitLab(self.spec['target_commit'], duplicate=True)
        before = publication.publish(client, self.spec)
        self.assertEqual(before['status'], 'reconcile_required')
        self.assertIsNotNone(before['url'])
        repaired = publication.repair_owned_title(client, self.spec, before)
        self.assertEqual(repaired['status'], 'reused')
        self.assertEqual(client.mrs[0]['title'], self.spec['title'])
        self.assertEqual(client.create_calls, 1)

    def test_format_repair_refuses_intervening_human_edit(self):
        client = FakeGitLab(self.spec['target_commit'], duplicate=True)
        before = publication.publish(client, self.spec)
        client.mrs[0]['body'] += '\nHuman update'
        client.mrs[0]['revision'] += 1
        self.assertEqual(publication.repair_owned_title(client, self.spec, before)['status'], 'reconcile_required')
        self.assertIn('Human update', client.mrs[0]['body'])

    def test_format_repair_without_revision_refuses_unconditional_write(self):
        client = FakeGitLab(self.spec['target_commit'], duplicate=True)
        before = publication.publish(client, self.spec)
        before['revision'] = None
        client.mrs[0]['revision'] = None
        title = client.mrs[0]['title']
        self.assertEqual(publication.repair_owned_title(client, self.spec, before)['status'], 'reconcile_required')
        self.assertEqual(client.mrs[0]['title'], title)

    def test_foreign_source_and_mr_are_not_overwritten(self):
        client = FakeGitLab(self.spec['target_commit'])
        client.branch = {'identity': 'foreign', 'commit': '4' * 40}
        self.assertEqual(publication.publish(client, self.spec)['status'], 'reconcile_required')
        self.assertEqual(client.create_calls, 0)
        self.assertEqual(client.branch['commit'], '4' * 40)
        client = FakeGitLab(self.spec['target_commit'])
        publication.publish(client, self.spec)
        client.mrs[0]['identity'] = 'foreign'
        self.assertEqual(publication.publish(client, self.spec)['status'], 'reconcile_required')
        self.assertEqual(client.mrs[0]['identity'], 'foreign')

    def test_target_move_before_write_prevents_creation(self):
        client = FakeGitLab('4' * 40)
        self.assertEqual(publication.publish(client, self.spec)['status'], 'reconcile_required')
        self.assertEqual(client.create_calls, 0)


if __name__ == '__main__':
    unittest.main()
