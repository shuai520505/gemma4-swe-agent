import ast
import hashlib
import json
from pathlib import Path
import subprocess
import unittest
from u_re.v01.experiments.mechanism_02.select import HERE,ROOT


class ReadinessTests(unittest.TestCase):
    def test_no_unexecuted_task_is_fabricated_failure(self):
        d=json.loads((HERE/'TASK_SCREENING_LEDGER.json').read_text())
        self.assertEqual(d['checked'],0);self.assertEqual(d['selected'],[])
        self.assertEqual(len(d['rows']),50)
        for r in d['rows']:
            self.assertEqual(r['status'],'not_run');self.assertFalse(r['cpu_entered'])
            for k in ('passed','failed','errors','skipped','xfailed','setup_errors','collection_errors','native_exit_code','environment_admitted'):
                self.assertIsNone(r[k],(r['instance_id'],k))

    def test_diversity_block_not_repaired_by_silent_task_substitution(self):
        d=json.loads((HERE/'RANKED_POOL.json').read_text())['rows']
        self.assertEqual({r['repo'] for r in d},{'fastapi/fastapi'})
        p=json.loads((HERE/'PAIR_PROTOCOL.json').read_text())
        self.assertEqual([r['arm'] for r in p['prospective_order']],['A','B','B','A'])
        self.assertTrue(all(r['task'] is None for r in p['prospective_order']))
        identities=json.loads((HERE/'TASK_IDENTITY_MANIFEST.json').read_text())
        self.assertEqual(identities['selected'],[])

    def test_gpu_draft_is_locked_and_not_a_saved_gpu_notebook(self):
        d=json.loads((HERE/'GPU_EXECUTION_DRAFT.json').read_text())
        for k in ('execute','gpu_authorized','formal_submission','GPU_Notebook_generated','GPU_Notebook_saved','resource_admission','runtime_model_hashes_verified'):
            self.assertIs(d[k],False,k)
        self.assertIsNone(d['current_GPU_quota']);self.assertIsNone(d['Notebook_sha256'])
        for p in (HERE/'notebooks').glob('*/kernel-metadata.json'):
            meta=json.loads(p.read_text());self.assertIs(meta['enable_gpu'],False);self.assertEqual(meta['model_sources'],[])
        tree=ast.parse((HERE/'gpu_execution_stub.py').read_text())
        self.assertIsInstance(tree.body[-1],ast.Raise)

    def test_frozen_selection_was_not_adjusted_after_block(self):
        commit='ac20c4745027c6068571292898b45c4ea0cfb630'
        for name in ('select.py','screen.py','SELECTION_PROTOCOL.json','EXCLUSION_LEDGER_V02.json','TASK_POOL_METADATA.json','RANKED_POOL.json'):
            old=subprocess.check_output(['git','show',commit+':'+(HERE/name).relative_to(ROOT).as_posix()],cwd=ROOT)
            self.assertEqual(old,(HERE/name).read_bytes(),name)

    def test_history_and_old_block_are_preserved(self):
        before=json.loads((HERE/'evidence/INITIAL_HISTORY.json').read_text())
        for p,h in before.items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h,p)
        old=json.loads((ROOT/'u_re/v01/GPU_EXPERIMENT_PROTOCOL_DRAFT.json').read_text())
        self.assertEqual(old['status'],'DRAFT_BASELINE_BLOCKED')

    def test_authentication_failure_did_not_send_save_request(self):
        d=json.loads((HERE/'evidence/AUTH_AVAILABILITY.json').read_text())
        self.assertFalse(d['existing_cache_auth_available']);self.assertEqual(d['initial_save_requests'],0)
        self.assertFalse(list((HERE/'results').rglob('SAVE_REQUEST.json')))
        self.assertFalse(list((HERE/'results').rglob('SAVE_INTENT.json')))

    def test_resource_numbers_are_plans_without_probability_claim(self):
        d=json.loads((HERE/'RESOURCE_PLAN.json').read_text())
        self.assertEqual(sum(d['seconds'].values()),8940)
        self.assertEqual(d['each_worker']['total'],1110)
        self.assertIsNone(d['actual_Gemma_P50']);self.assertIsNone(d['quota_billing_rate'])
        self.assertFalse(d['resource_admitted'])


if __name__=='__main__':unittest.main()
