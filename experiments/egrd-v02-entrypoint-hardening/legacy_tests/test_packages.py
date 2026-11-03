"""Offline package and experiment boundary checks; no model requests."""
import hashlib,json,unittest,zipfile
from pathlib import Path
D=Path(__file__).resolve().parent
class PackageTests(unittest.TestCase):
 def setUp(self):self.manifest=json.loads((D/'PACKAGE_MANIFEST.json').read_bytes())
 def test_artifacts_match_frozen_manifest(self):
  for arm,row in self.manifest['arms'].items():
   raw=(D/'packages'/f'{arm}.zip').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
   with zipfile.ZipFile(D/'packages'/f'{arm}.zip') as z:
    self.assertIsNone(z.testzip());self.assertEqual(set(z.namelist()),set(row['members']))
    for n,h in row['members'].items():self.assertEqual(hashlib.sha256(z.read(n)).hexdigest(),h)
 def test_single_factor_matched_pairs(self):
  for x,y in [('A','B'),('C','D')]:
   a=self.manifest['arms'][x]['members'];b=self.manifest['arms'][y]['members']
   self.assertEqual([n for n in a if a[n]!=b[n]],['skills/egrd-repair/scripts/egrd.py'])
 def test_tools_no_extra_agent(self):
  self.assertEqual(len(self.manifest['base_tools']),6);self.assertEqual(len(self.manifest['official_skill_accessors']),4)
  self.assertFalse(self.manifest['extra_custom_tools']);self.assertFalse(self.manifest['global_control'])
  for arm in 'ABCD':
   text=(D/'packages'/arm/'agent.yaml').read_text()
   self.assertEqual(text.count('agent_class: LlmAgent'),1);self.assertNotIn('sub_agents',text)
 def test_model_identity_and_budget(self):
  configs=json.loads((D/'MODEL_CONFIGURATIONS.json').read_bytes())
  for size,alias in [('12b','gemma-4-12b-it-qat-w4a16-ct'),('31b','gemma-4-31b-it-qat-w4a16-ct')]:
   c=configs[size];self.assertEqual(c['alias'],alias);self.assertEqual(c['session_seconds'],300);self.assertEqual(c['context_limit'],32768)
   self.assertIn('model.safetensors',c['expected_files']);self.assertTrue(all(len(v)==64 for v in c['expected_files'].values()))
 def test_task_identity_no_test_answers(self):
  plan=json.loads((D/'TASK_IDENTITY_MANIFEST.json').read_bytes())
  self.assertEqual(len(plan['tasks']),3);self.assertEqual(len(plan['sessions']),12)
  for r in plan['tasks']:
   self.assertEqual(len(r['issue_sha256']),64);self.assertEqual(len(r['SDK_snapshot_sha256']),64)
   self.assertNotIn('patch',r)
if __name__=='__main__':unittest.main()
