import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from u_re.v01.experiments.mechanism_02.select import rank,PREFIX,HERE
from u_re.v01.experiments.mechanism_02.screen import decide


class PolicyTests(unittest.TestCase):
    def test_complete_pool_partition_and_determinism(self):
        pool=json.loads((HERE/'TASK_POOL_METADATA.json').read_text())['rows']
        excluded=set(json.loads((HERE/'EXCLUSION_LEDGER_V02.json').read_text())['excluded_task_ids'])
        expected=json.loads((HERE/'RANKED_POOL.json').read_text())['rows']
        ids=lambda rows:[r['instance_id'] for r in rows]
        self.assertEqual(ids(rank(pool,excluded)),ids(expected))
        self.assertEqual(ids(rank(list(reversed(pool)),excluded)),ids(expected))
        self.assertFalse(excluded.intersection(ids(expected)))
        self.assertEqual(len(pool),len(excluded)+len(expected))
        self.assertTrue({'fastapi_14458','requests_7433','fastapi_15800','rich_3471','rich_3676','fastapi_14492'}.issubset(excluded))
        for row in expected:self.assertEqual(row['sort_sha256'],hashlib.sha256((PREFIX+row['instance_id']).encode()).hexdigest())

    def test_only_behavior_failure_is_eligible(self):
        base=dict(category='assertion_failure',infrastructure_stop=False)
        self.assertEqual(decide(base,evidence_ok=True)[0],'ELIGIBLE')
        self.assertEqual(decide(base,evidence_ok=False)[0],'STOP')
        self.assertEqual(decide(dict(category='passed',infrastructure_stop=False),evidence_ok=True)[0],'REJECT')

    def test_known_fixture_block_is_rejection_not_algorithm_failure(self):
        a=dict(category='setup_error',infrastructure_stop=True,events=[dict(category='setup_error',details="recursive dependency involving fixture 'httpbin' detected")])
        self.assertEqual(decide(a,evidence_ok=True)[0],'REJECT')
        a['events'].append(dict(category='setup_error',details='Unrelated unclassified environment crash'))
        self.assertEqual(decide(a,evidence_ok=True)[0],'STOP')

    def test_stdout_error_words_cannot_create_environment_rejection(self):
        a=dict(category='assertion_failure',infrastructure_stop=False,stdout='ERROR ModuleNotFoundError Found 4 errors in 2 files')
        self.assertEqual(decide(a,evidence_ok=True)[0],'ELIGIBLE')
        self.assertEqual(decide(dict(category='unknown_unparsed',infrastructure_stop=True),evidence_ok=True)[0],'STOP')

    def test_gpu_guard_stops_before_any_import_or_launch(self):
        p=subprocess.run([sys.executable,str(HERE/'gpu_execution_stub.py')],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0)
        self.assertIn('NOT_AUTHORIZED',p.stderr)
        self.assertNotIn('import', (HERE/'gpu_execution_stub.py').read_text().splitlines()[-1])

    def test_same_frozen_candidate_bytes(self):
        root=HERE.parents[1]
        for arm,h in [('noegv','2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608'),('full','887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821')]:
            self.assertEqual(hashlib.sha256((root/f'submission_{arm}.zip').read_bytes()).hexdigest(),h)


if __name__=='__main__':unittest.main()
