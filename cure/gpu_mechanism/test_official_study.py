"""CPU integration: scripted Phase1 only; fresh official Phase2 for each new scenario."""
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from cure.runtime_config import ResearchConfig
from cure import MODEL


class OfficialStudyTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_official_phase2_accepts_all_four_independent_tests(self):
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
                spec['_cpu_reference_patch']=refs[row['task_id']]
                base=Path(os.environ.get('CURE_STUDY_CPU_EVIDENCE_DIR',temp))/row['task_id']
                base.mkdir(parents=True,exist_ok=False)
                spec_path=base/'spec.json';spec_path.write_text(json.dumps(spec))
                output=base/'run'
                proc=subprocess.run([sys.executable,'-m','cure.gpu_mechanism.cpu_phase2',str(spec_path),str(output)],
                    cwd=root,capture_output=True,text=True,timeout=180)
                (base/'worker.log').write_text(proc.stdout+proc.stderr)
                self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
                result=json.loads((output/'official_result.json').read_text())
                self.assertTrue(result['resolved'],result)
                self.assertEqual(result['test_exit_code'],0)
                self.assertTrue((output/'phase2_execution.json').is_file())
                self.assertTrue(json.loads((output/'worker_done.json').read_text())['cleanup_complete'])


if __name__=='__main__': unittest.main()
