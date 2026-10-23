"""Fail-closed boundaries; no task, Agent, model or Kaggle execution."""
import ast,json,unittest,zipfile
from unittest.mock import patch
from .selection import HERE,ROOT,PREFIX,sha
from .cpu_control import validate_screen,factory

class Selection(unittest.TestCase):
    def test_frozen_order_and_conservative_reservations(self):
        d=json.loads((HERE/'TASK_POOL_FREEZE.json').read_bytes())
        old=json.loads((ROOT/'u_re/v01/experiments/action_priority_01/gpu_readiness_01/TASK_POOL_FREEZE.json').read_bytes())
        self.assertTrue(set(old['excluded_ids'])<set(d['excluded_ids']))
        self.assertTrue({r['instance_id'] for r in old['next_max8_in_order']}<=set(d['excluded_ids']))
        self.assertEqual(d['remaining_count'],34)
        expected=sorted(d['ranked_rows'],key=lambda r:(sha((PREFIX+r['instance_id']).encode()),r['instance_id']))
        self.assertEqual(expected,d['ranked_rows']);self.assertEqual(expected[:16],d['next_max16_in_order'])
    def test_original_candidates_unchanged(self):
        for row in json.loads((HERE/'TASK_POOL_FREEZE.json').read_bytes())['candidates'].values():self.assertEqual(sha((ROOT/row['path']).read_bytes()),row['sha256'])

class Dispatch(unittest.TestCase):
    def test_missing_accepted_gate_rejects_before_auth_or_dispatch(self):
        for attempt in ('screen01','screen02','screen03'):
            with self.assertRaises(KeyError):validate_screen(attempt)
    def test_fixed_screen_complete_gate_hashes(self):
        self.assertTrue(validate_screen('screen04'))
    def test_launch_validation_failure_cannot_reach_network(self):
        m=factory('screen01')
        with patch(__package__+'.cpu_control.validate_screen',side_effect=ValueError('owned validation failure')):
            with self.assertRaisesRegex(ValueError,'owned validation failure'):m.launch()
    def test_no_gpu_or_model_source_in_all_screen_notebooks(self):
        for attempt in ('screen01','screen02','screen03','screen04'):
            d=json.loads((HERE/attempt/'notebook/kernel-metadata.json').read_bytes())
            self.assertFalse(d['enable_gpu']);self.assertFalse(d['enable_tpu']);self.assertFalse(d['enable_internet']);self.assertEqual(d['model_sources'],[])
    def test_unadmitted_cohort_has_no_sealed_gpu_payload_or_dispatch(self):
        self.assertFalse((HERE/'payload.zip').exists())
        self.assertFalse((HERE/'EXPERIMENT_LOCK.json').exists())
        self.assertEqual(list(HERE.glob('batch*/execution/dispatch.claim')),[])

class NativeEvidence(unittest.TestCase):
    def setUp(self):
        self.ledger=json.loads((HERE/'TASK_ADMISSION_LEDGER.json').read_bytes())
    def test_actual_five_checks_and_mandatory_stop(self):
        self.assertEqual(self.ledger['checked'],5)
        self.assertEqual([r['status'] for r in self.ledger['rows'][:5]],['NON_DISCRIMINATING','ENVIRONMENT_BLOCKED','BASELINE_ELIGIBLE','NON_DISCRIMINATING','STOP'])
        self.assertTrue(all(r['status']=='NOT_RUN' and r['counts'] is None for r in self.ledger['rows'][5:]))
    def test_junit_taskresult_provenance_and_cleanup_replay(self):
        from .audit import counts
        path=self.ledger['source_archive']['path']
        with zipfile.ZipFile(path) as z:
            self.assertIsNone(z.testzip())
            for row in self.ledger['rows'][:5]:
                prefix='validation/'+row['raw_evidence']+'/'
                raw=z.read(prefix+'phase2.junit.xml');native=json.loads(z.read(prefix+'official_result.json'))
                self.assertEqual(counts(raw),row['counts']);self.assertEqual(sha(raw),row['JUnit_sha256'])
                self.assertEqual(native['test_exit_code'],row['native_exit_code'])
                self.assertEqual(z.read(prefix+'before_pytest_files.json'),z.read(prefix+'after_pytest_files.json'))
                self.assertTrue(json.loads(z.read(prefix+'cleanup.json'))['complete'])
                self.assertTrue(json.loads(z.read(prefix+'source_provenance.json'))['verified'])
            alias=json.loads(z.read('validation/SNAPSHOT_ALIAS_CHECK.json'))
            self.assertEqual(len(alias['all_task_identities']),129);self.assertEqual(alias['conflicts'],[])

if __name__=='__main__':unittest.main()
