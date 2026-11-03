import json,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
class EntrypointTests(unittest.TestCase):
 def test_initialization_precedes_repository_work(self):
  prompt=(D/'packages/B/prompts/system.md').read_text(encoding='utf8')
  self.assertTrue(prompt.startswith('FIRST ACTION — EGRD INITIALIZATION'))
  self.assertLess(prompt.index('load_skill'),prompt.index('run_skill_script'))
 def test_both_model_pairs_share_prompt(self):
  self.assertEqual(len({(D/'packages'/a/'prompts/system.md').read_bytes() for a in 'ABCD'}),1)
 def test_existing_structure_fields_are_required(self):
  prompt=(D/'packages/B/prompts/system.md').read_text(encoding='utf8')
  for field in ['expected_behavior','actual_behavior','inputs_outputs','boundaries','acceptance_criteria','unresolved_questions']:
   self.assertIn(field,prompt)
 def test_load_and_script_are_not_invented_tools(self):
  m=json.loads((D/'PACKAGE_MANIFEST.json').read_bytes());self.assertIn('load_skill',m['official_skill_accessors']);self.assertIn('run_skill_script',m['official_skill_accessors']);self.assertFalse(m['extra_custom_tools'])
if __name__=='__main__':unittest.main()
