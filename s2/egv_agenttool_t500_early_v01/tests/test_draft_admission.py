"""Local-only scheduling checks, not official Runner or GPU results."""
import json
import unittest
from s1.util import sha
from s1.window import SessionWindow
from s2.egv_agenttool_t500_early_v01.gpu_session import require_authorization


class DraftAdmissionTests(unittest.TestCase):
    def test_draft_cannot_start_gpu(self):
        with self.assertRaises(AssertionError):require_authorization(dict(status='DRAFT_NOT_AUTHORIZED'),dict(authorized=False),1)

    def test_insufficient_quota_approval_cannot_start_gpu(self):
        plan=dict(status='AUTHORIZED_FROZEN',GPU_authorized=True,runs=[dict(arm=a,instance_id=t) for a,t in
            [('A','rich_3676'),('B','rich_3676'),('B','fastapi_14492'),('A','fastapi_14492')]],reserved_tasks=['rich_3043'])
        auth=dict(authorized=True,max_runs=4,experiment_id='S2-T500-EARLYEGV-MECHANISM-01',
            protocol_sha256=sha((json.dumps(plan,indent=2)+'\n').encode()),fresh_quota_and_machine_admission_verified=False)
        with self.assertRaises(AssertionError):require_authorization(plan,auth,1)

    def test_full_four_run_window_reserved(self):
        w=SessionWindow(0,limit_seconds=10000,finalization_seconds=900,clock=lambda:1460)
        self.assertTrue(w.admission(1200+4*(1550+60))['allow'])
        w.clock=lambda:1460.01
        self.assertFalse(w.admission(1200+4*(1550+60))['allow'])


if __name__=='__main__':unittest.main()
