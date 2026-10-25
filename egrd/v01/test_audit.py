import json
import unittest
from audit import assertion_syntax, pytest_summary, production, joined_calls, verdict, stop_class, HERE

class OfflineAuditTests(unittest.TestCase):
    def test_assert_syntax_not_execution(self):
        self.assertEqual(assertion_syntax('def test_x(): pass')['assert_nodes'],0)
        self.assertEqual(assertion_syntax('assert True')['nonconstant_assert_nodes'],0)
        self.assertEqual(assertion_syntax('x=1\nassert x==x')['nonconstant_assert_nodes'],1) # Can still be tautological.
        self.assertIsNone(assertion_syntax('def'))
    def test_error_word_in_test_data(self):
        self.assertEqual(pytest_summary('E Found 4 errors in 2 files\n4 failed, 19 passed in 0.11s\n'),{'failed':4,'passed':19})
    def test_actual_fixture_errors(self):
        self.assertEqual(pytest_summary('142 passed, 1 skipped, 1 xfailed, 4 warnings, 194 errors in 72.73s (0:01:12)')['errors'],194)
    def test_no_summary_is_unknown(self):
        self.assertEqual(pytest_summary('ERROR arbitrary tool text'),{})
    def test_guard_and_timeout_distinct(self):
        self.assertEqual(stop_class('{"decision": "reject", "output_reserved":16384}'),'CONTEXT_RESERVATION_STOP')
        self.assertEqual(stop_class('TimeoutError'),'AGENT_TIMEOUT')
    def test_source_scope(self):
        self.assertTrue(production('docs_src/metadata/example.py'))
        self.assertFalse(production('repro.py'))
        self.assertFalse(production('tests/test_x.py'))
    def test_parallel_calls_join_by_id(self):
        row=lambda parts,t:{'event':{'content':{'parts':parts}},'recorded_monotonic':t}
        calls,responses=joined_calls([row([{'function_call':{'id':'a'}},{'function_call':{'id':'b'}}],1),row([{'function_response':{'id':'b'}},{'function_response':{'id':'a'}}],2)])
        self.assertEqual(len(calls),2);self.assertEqual(calls[0]['event_index'],calls[1]['event_index']);self.assertEqual(set(responses),{'a','b'})
    def test_preinference_false_not_failure(self):
        self.assertIsNone(verdict({'resolved':False},{},None,0)[0])
    def test_dataset_invariants(self):
        data=json.loads((HERE/'TRAJECTORY_DATASET.json').read_bytes())
        self.assertEqual(len(data['sessions']),26)
        self.assertEqual(sum(s['observed_tool_calls'] for s in data['sessions']),784)
        for s in data['sessions']:
            self.assertIsNotNone(s['candidate_zip_sha256'])
            self.assertIsNone(s['semantic_information_gain_count'])
            for event in s['events']:
                self.assertNotIn('args',event);self.assertNotIn('response',event)
            if s['reviewed_behavioral_edit_event'] is not None:
                row=next(e for e in s['events'] if e['event_index']==s['reviewed_behavioral_edit_event'])
                self.assertTrue(row['production_mutation'],s['id'])
        self.assertEqual(sum(s['native_resolved'] is None for s in data['sessions']),1)
    def test_declared_edit_observation_after_agent_start(self):
        data=json.loads((HERE/'TRAJECTORY_DATASET.json').read_bytes())
        for s in data['sessions']:
            for e in s['source_changes']:self.assertGreaterEqual(e['seconds'],0)

if __name__=='__main__':unittest.main(verbosity=2)
