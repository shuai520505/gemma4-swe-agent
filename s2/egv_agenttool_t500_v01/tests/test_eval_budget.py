import json,math,os,tempfile,unittest,zipfile
from pathlib import Path
import yaml
from harness_v2.evidence import atomic_json
from .runner_cases import HERE,MODEL

class EvaluationBudgetTests(unittest.TestCase):
 def test_public_eval_config_float_and_both_candidates(self):
  from swegemma.config import EvalConfig,build_submission_limits
  from adk_submission import ModelRegistry,compile_submission
  from google.adk.models.lite_llm import LiteLlm
  from swegemma.context import SwegemmaContext
  from s2.egv_agenttool_t500_v01.validation import validate_candidate
  from s2.egv_agenttool_t500_v01.config import Config
  models=ModelRegistry();models.register(MODEL,LiteLlm(model='openai/'+MODEL,api_base='http://127.0.0.1:8000/v1',api_key='EMPTY'))
  limits,constraints=build_submission_limits();rows=[]
  for folder in (HERE,HERE/'control_single_t500'):
   with tempfile.TemporaryDirectory() as tmp:
    with zipfile.ZipFile(folder/'submission.zip') as z:self.assertIsNone(z.testzip());z.extractall(tmp)
    data=yaml.safe_load((Path(tmp)/'eval_config.yaml').read_text())['evaluation']
    self.assertEqual(set(data),{'max_time_minutes','max_tool_calls','timeout_seconds'})
    cfg=EvalConfig(tasks_path=Path('/unused/tasks'),snapshots_dir=Path('/unused/snapshots'),results_dir=Path(tmp)/'results',submission_dir=Path(tmp),models=models,**data)
    self.assertTrue(math.isclose(cfg.budget.time_minutes*60,500,abs_tol=1e-10))
    self.assertEqual(cfg.budget.tool_calls,60);self.assertEqual(cfg.harness.command_timeout_seconds,120)
    agent=compile_submission(tmp,SwegemmaContext().create_tools(),models,limits=limits,generation_constraints=constraints)
    validate_candidate(agent,Config())
    rows.append(dict(candidate=str(folder.name),parsed=data,effective_seconds=cfg.budget.time_minutes*60,official_EvalConfig=True))
  atomic_json(Path(os.environ['S2_CPU_EVIDENCE']).parent/'eval_config_public_API.json',dict(passed=True,candidates=rows,
   scope='Official public EvalConfig and actual native Runner validated; private scripts/inference.py loader not distributed in public524-file inventory or official wheels.'))
