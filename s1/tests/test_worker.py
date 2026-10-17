"""Real EvalConfig/compiler construction through the new worker; no model response."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from s1.config import Config
from s1 import MODEL

ROOT=Path(__file__).resolve().parents[2]


class WorkerConfigTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self,arm):
        from swegemma.models import TaskResult
        from s1.worker import evaluate
        from harness_v2.evidence import Journal
        from s1.util import sha
        manifest=json.loads((ROOT/'s1/candidates.json').read_text())[arm]
        seen=[]
        class FakeEvaluator:
            def __init__(self,config,*,journal):seen.append(config)
            async def evaluate_task(self,task,context):
                # Explicitly a CPU fixture; no actual Phase1/Phase2 inference.
                return TaskResult(instance_id=task.instance_id,resolved=False,test_exit_code=-1,agent_patch='CPU fixture patch')
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);tasks=d/'tasks.jsonl'
            tasks.write_text(json.dumps(dict(instance_id='s1_cpu_fixture',repo='test/mock_repo',
                base_commit='a'*40,problem_statement='CPU fixture Issue'))+'\n')
            spec=dict(research_config=manifest['config'],agent_dir=str(ROOT/'s1/candidates'/arm),
                candidate_hashes=manifest['members'],tasks_path=str(tasks),snapshots_dir=str(d),wheels_dir=str(d),
                graph_dir=str(d),embeddings_dir=str(d),instance_id='s1_cpu_fixture',base_commit='a'*40,
                problem_sha256=sha(b'CPU fixture Issue'),model_path=MODEL,model_alias=MODEL,base_url='http://127.0.0.1:8000/v1')
            with patch('harness_v2.official.DurableEvaluator',FakeEvaluator):await evaluate(spec,d/'output')
            self.assertEqual(len(seen),1)
            self.assertEqual(seen[0].budget.time_minutes,5)
            self.assertEqual(seen[0].budget.tool_calls,60)
            self.assertEqual(seen[0].harness.verification_timeout_seconds,300)
            self.assertEqual((d/'output/latest.patch').read_text(),'CPU fixture patch')
            runtime=json.loads((d/'output/runtime_config.json').read_text())
            self.assertEqual(runtime['output_reserved'],manifest['config']['output_tokens'])
            self.assertTrue(json.loads((d/'output/worker_done.json').read_text())['cleanup_complete'])

    async def test_16384_actual_worker_configuration(self):await self.exercise('control')
    async def test_8192_actual_worker_configuration(self):await self.exercise('e1_output8192')
