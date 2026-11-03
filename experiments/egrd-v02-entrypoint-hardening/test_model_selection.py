import unittest
from pathlib import Path
D=Path(__file__).resolve().parent
class ModelSelectionTests(unittest.TestCase):
 def select(self,rows,model='12b'):
  self.assertTrue((D/'model_selection.py').exists(),'Bounded model fallback decision missing')
  from model_selection import decide;return decide(rows,model)
 def rows(self,active):return [dict(task_id=str(i),infrastructure_ok=True,tools_available=True,activation=active,evidence_records=1 if active else 0,model_failure='MODEL_DID_NOT_CALL' if not active else None,native_resolved=False) for i in [1,2]]
 def test_qualified_12b_stays_primary(self):self.assertEqual(self.select(self.rows(True)),'KEEP_12B')
 def test_one_failed_repair_not_model_disqualification(self):self.assertEqual(self.select(self.rows(True)[:1]),'KEEP_12B_REPAIR_FAILURE_NOT_DISQUALIFICATION')
 def test_repeated_model_failure_allows_fallback_confirmation(self):self.assertEqual(self.select(self.rows(False)),'REQUEST_31B_FALLBACK_CONFIRMATION')
 def test_infrastructure_failure_never_blames_model(self):
  rows=self.rows(False);rows[0]['infrastructure_ok']=False;self.assertEqual(self.select(rows),'STOP_INFRASTRUCTURE')
 def test_single_activation_failure_does_not_switch(self):self.assertEqual(self.select(self.rows(False)[:1]),'INCONCLUSIVE_STOP_AT_BOUNDED_SMOKE')
 def test_both_models_missing_calls_stops_architecture(self):self.assertEqual(self.select(self.rows(False),'31b'),'STOP_ENTRYPOINT_OR_ARCHITECTURE')
if __name__=='__main__':unittest.main()
