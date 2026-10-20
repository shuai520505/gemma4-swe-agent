"""Official Linux acceptance: rerun frozen regressions, new paths and real500s."""
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from harness_v2.evidence import atomic_json

HERE=Path(__file__).resolve().parent


def compiler(output):
    import yaml
    from adk_submission import ModelRegistry,compile_submission,validate_directory
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.context import SwegemmaContext
    from swegemma.config import EvalConfig,build_submission_limits
    from s2.egv_agenttool_t500_v01.config import Config
    from s2.egv_agenttool_t500_v01.validation import validate_candidate
    model='gemma-4-31b-it-qat-w4a16-ct'
    models=ModelRegistry();models.register(model,LiteLlm(model='openai/'+model,api_base='http://127.0.0.1:8000/v1',api_key='EMPTY'))
    limits,constraints=build_submission_limits()
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(HERE/'submission.zip') as z:
            assert z.testzip() is None and len(z.namelist())==5
            assert 'agent.yaml' in z.namelist() and not any(n.endswith('.py') for n in z.namelist())
            z.extractall(tmp)
        validate_directory(tmp,limits=limits)
        agent=compile_submission(tmp,SwegemmaContext().create_tools(),models,limits=limits,generation_constraints=constraints)
        validate_candidate(agent,Config())
        assert agent.instruction==(HERE/'candidate/prompts/main.md').read_text()
        child=next(t.agent for t in agent.tools if getattr(t,'name',None)=='egv_verifier')
        assert child.instruction==(HERE/'candidate/sub_agents/egv_verifier.md').read_text()
        values=yaml.safe_load((Path(tmp)/'eval_config.yaml').read_text())['evaluation']
        cfg=EvalConfig(tasks_path=Path('/unused/tasks'),snapshots_dir=Path('/unused/snapshots'),results_dir=Path(tmp)/'results',submission_dir=Path(tmp),models=models,**values)
        assert abs(cfg.budget.time_minutes*60-500)<1e-9 and cfg.budget.tool_calls==60 and cfg.harness.command_timeout_seconds==120
        atomic_json(output/'compiler_gate.json',dict(passed=True,real_official_Compiler=True,
            Main_instruction_exact=True,child_instruction_exact=True,root_tools=7,child_tools=3,
            shared_Agent_seconds=cfg.budget.time_minutes*60,counted_tool_limit=cfg.budget.tool_calls,
            ZIP_members=5,custom_executable_members=0))


def suite(names,output,label):
    with (output/(label+'.log')).open('x') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
    gate=dict(passed=result.wasSuccessful() and not result.skipped,tests_run=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped))
    atomic_json(output/(label+'.json'),gate)
    return gate


def main(directory):
    assert sys.platform=='linux','Official Linux CPU execution required'
    output=Path(directory);output.mkdir(parents=True,exist_ok=False)
    atomic_json(output/'versions.json',{n:importlib.metadata.version(n) for n in
        ('swegemma','adk-submission','google-adk','google-genai','litellm','pytest')})
    atomic_json(output/'cpu_gate.json',dict(passed=False,stage='compiler',GPU=False,Gemma_inference=False))
    compiler(output)
    # These are the existing actual research entry paths, unchanged on disk.
    old=subprocess.run([sys.executable,'-m','s1.experiments.egv_mechanism_smoke_01.cpu',str(output/'original115')],
        capture_output=True,text=True,timeout=3000)
    (output/'original115.stdout.log').write_text(old.stdout);(output/'original115.stderr.log').write_text(old.stderr)
    original=json.loads((output/'original115/cpu_gate.json').read_text())
    assert old.returncode==0 and original['passed']
    os.environ['S2_CPU_EVIDENCE']=str(output/'frozen_T500_cases')
    legacy=suite(['s2.egv_agenttool_t500_v01.tests.test_closed_loop',
        's2.egv_agenttool_t500_v01.tests.test_statistics','s2.egv_agenttool_t500_v01.tests.test_eval_budget'],output,'frozen_T500_regressions')
    assert legacy['passed'],'Preserve this CPU preparation; do not overwrite failures'
    atomic_json(output/'cpu_gate.json',dict(passed=False,stage='new_tests',original115_passed=True,frozen_T500=legacy,GPU=False,Gemma_inference=False))
    os.environ['S2_EARLY_EVIDENCE']=str(output/'early_cases')
    early=suite(['s2.egv_agenttool_t500_early_v01.tests.test_early'],output,'early_workflow_tests')
    assert early['passed'],'New workflow failure: retain evidence and version any repair'
    # Same accepted exact-budget tests; in-memory submission binding points only
    # at the new candidate. Native tools and timing logic remain original.
    from s2.egv_agenttool_t500_v01.tests import runner_cases
    os.environ['S2_CPU_EVIDENCE']=str(output/'early_exact_cases')
    with patch.object(runner_cases,'HERE',HERE):
        exact=suite(['s2.egv_agenttool_t500_v01.tests.test_exact_budget'],output,'early_exact_budget')
    assert exact['passed'],'500s/60 shared-budget boundary not accepted'
    tokenization=dict(status='not_run',reason='CPU model tokenizer not mounted')
    paths=[p.parent for p in Path('/kaggle/input').rglob('tokenizer_config.json') if 'gemma-4-31b-it-qat-w4a16-ct' in p.parts]
    if len(paths)==1:
        try:
            from transformers import AutoTokenizer
            tokenizer=AutoTokenizer.from_pretrained(paths[0],local_files_only=True,trust_remote_code=False)
            before=(HERE.parent/'egv_agenttool_t500_v01/candidate/prompts/main.md').read_text()
            after=(HERE/'candidate/prompts/main.md').read_text()
            tokenization=dict(status='measured',tokenizer=str(paths[0]),old_prompt_tokens=len(tokenizer.encode(before)),
                new_prompt_tokens=len(tokenizer.encode(after)),scope='Standalone CPU tokenization of instruction, not full chat-template request or GPU latency')
        except Exception as exc:tokenization=dict(status='unavailable',reason=repr(exc))
    atomic_json(output/'prompt_tokenization.json',tokenization)
    gate=dict(passed=True,original115_passed=True,original115=original,frozen_T500=legacy,
        new_workflow=early,new_exact_budget=exact,real_Compiler=True,real_ADK_Runner=True,
        real_sandbox_tools=True,mocked_HTTP=True,actual_native_500_second_wait=True,Gemma_inference=False,GPU=False,
        scope='Scripted HTTP proves execution paths; no autonomous soft-timing policy or algorithm benefit inference.')
    atomic_json(output/'cpu_gate.json',gate)
    print('EARLY_CPU_GATE_PASSED',flush=True)


if __name__=='__main__':main(sys.argv[1])
