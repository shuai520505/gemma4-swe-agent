"""CPU integration: scripted Phase1 only; fresh official Phase2 for each new scenario."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from cure.runtime_config import ResearchConfig
from cure import MODEL


class OfficialStudyTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_official_phase2_accepts_all_four_independent_tests(self):
        from cure.worker import evaluate
        from harness_v2.official import DurableEvaluator
        root=Path(__file__).resolve().parents[2]
        plan=json.loads((root/'study/protocol.json').read_text())
        refs=json.loads((root/'study/evaluation-references.json').read_text())
        for row in plan['tasks']:
            with self.subTest(case=row['task_id']), tempfile.TemporaryDirectory() as temp:
                spec=dict(research_config=ResearchConfig().snapshot(),model_alias=MODEL,model_path=MODEL,
                    base_url='http://127.0.0.1:8000/v1',agent_dir=str(root/'cure/candidates/checklist'),
                    candidate_hashes=plan['candidates']['checklist']['members'],
                    tasks_path=str(root/'study/data/tasks.jsonl'),snapshots_dir=str(root/'study/data/snapshots'),
                    wheels_dir=str(root/'study/data/wheels'),graph_dir=str(root/'study/data/graphs'),
                    embeddings_dir=str(root/'study/data/embeddings'),instance_id=row['task_id'],
                    base_commit=row['base_commit'],problem_sha256=row['problem_sha256'])
                async def scripted(_self,*args,**kwargs): return refs[row['task_id']],None,None
                with patch.object(DurableEvaluator,'_run_agent_sandbox',scripted):
                    await evaluate(spec,Path(temp))
                result=json.loads((Path(temp)/'official_result.json').read_text())
                self.assertTrue(result['resolved'],result)
                self.assertEqual(result['test_exit_code'],0)
                self.assertTrue((Path(temp)/'phase2_execution.json').is_file())
                self.assertTrue(json.loads((Path(temp)/'worker_done.json').read_text())['cleanup_complete'])


if __name__=='__main__': unittest.main()
