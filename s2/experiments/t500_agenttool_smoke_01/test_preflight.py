"""Local admission tests; never substitutes for official Linux CPU/GPU gates."""
import json
from pathlib import Path
import unittest
from s1.util import sha
from s1.window import SessionWindow
from .session import require_authorization


class PreflightTests(unittest.TestCase):
    def plan(self):
        return dict(status='AUTHORIZED_ONE_SMOKE_CPU_GATE_PENDING',
            selected=[dict(instance_id='rich_3471')], reserved_tasks=['rich_3043'],
            runs=[dict(arm='B')])

    def auth(self,p):
        return dict(authorized=True,max_runs=1,experiment_id='S2-T500-AGENTTOOL-SMOKE-01',
            protocol_sha256=sha((json.dumps(p,indent=2)+'\n').encode()))

    def test_only_single_authorized_arm(self):
        p=self.plan();require_authorization(p,self.auth(p),1)
        for key,value in [('authorized',False),('max_runs',16),('protocol_sha256','wrong')]:
            a=self.auth(p);a[key]=value
            with self.assertRaises(AssertionError):require_authorization(p,a,1)
        p['runs'].append(dict(arm='B'))
        with self.assertRaises(AssertionError):require_authorization(p,self.auth(p),1)

    def test_reserved_task_cannot_be_consumed(self):
        p=self.plan();p['reserved_tasks'].append('rich_3471')
        with self.assertRaises(AssertionError):require_authorization(p,self.auth(p),1)

    def test_insufficient_time_reserves_complete_worker(self):
        w=SessionWindow(0,limit_seconds=2700,finalization_seconds=180,clock=lambda:310)
        self.assertTrue(w.admission(600+1550+60)['allow'])
        w.clock=lambda:310.01
        self.assertFalse(w.admission(600+1550+60)['allow'])


if __name__=='__main__':unittest.main()
