"""CPU-only native Compiler/Runner acceptance. No model inference service."""
import asyncio
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
from harness_v2.evidence import atomic_json

HERE=Path(__file__).resolve().parent


async def compiler_empty_state(output):
    from adk_submission import ModelRegistry,compile_submission,validate_directory
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.config import build_submission_limits,EvalConfig
    from swegemma.context import SwegemmaContext
    from swegemma.harness.agent_runner import run_agent_sandbox
    from s1.config import Config,validate_compiled
    from s1.tests import test_runner
    from . import MODEL
    models=ModelRegistry();models.register(MODEL,LiteLlm(model='openai/'+MODEL,api_base='http://127.0.0.1:8000/v1',api_key='EMPTY'))
    limits,constraints=build_submission_limits();results={}
    for arm in ('noegv','full'):
        path=HERE/('candidate_'+arm);validate_directory(path,limits=limits)
        agent=compile_submission(path,SwegemmaContext().create_tools(),models,limits=limits,generation_constraints=constraints)
        validate_compiled(agent,Config())
        assert agent.instruction==(path/'prompts/system.md').read_text()
        assert not agent.sub_agents
        cfg=EvalConfig(tasks_path=Path('/unused'),snapshots_dir=Path('/unused'),results_dir=output/'unused',
            submission_dir=path,models=models,max_time_minutes=5.0,max_tool_calls=60,timeout_seconds=120)
        assert cfg.budget.time_minutes*60==300 and cfg.budget.tool_calls==60 and cfg.harness.command_timeout_seconds==120
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for f in path.rglob('*'):
                if f.is_file():
                    dest=root/'candidates/control'/f.relative_to(path);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes())
            (root/'candidates.json').write_text(json.dumps({'control':{'config':Config().snapshot()}}))
            helper=test_runner.FullRunnerTests(methodName='runTest')
            with patch.object(test_runner,'ROOT',root),patch.dict(os.environ,S1_RUNNER_EVIDENCE=str(output/arm)):
                await helper.exercise('control')
        results[arm]=dict(passed=True,actual_official_Compiler=True,actual_empty_state_ADK_Runner=True,
            tool_count=len(agent.tools),agent_count=1,agent_seconds=300,counted_tools=60,command_seconds=120,
            generation=agent.generate_content_config.model_dump(mode='json',exclude_none=True))
    atomic_json(output/'compiler_empty_state_gate.json',results)
    api=output/'official_api_sources';api.mkdir()
    for name,obj in [('SwegemmaContext',SwegemmaContext),('run_agent_sandbox',run_agent_sandbox),
                     ('compile_submission',compile_submission),('EvalConfig',EvalConfig)]:
        (api/(name+'.py')).write_text(inspect.getsource(obj))
    return results


def tokenize(output):
    from transformers import AutoTokenizer
    matches=[p.parent for p in Path('/kaggle/input').rglob('tokenizer_config.json') if 'gemma-4-31b-it-qat-w4a16-ct' in p.parts]
    assert len(matches)==1,'Exact frozen31Bv2 tokenizer mount required; no external download fallback'
    model=matches[0];tokenizer=AutoTokenizer.from_pretrained(model,local_files_only=True,trust_remote_code=False)
    import hashlib
    results={}
    for name,path in [('s0',HERE/'reference_prompts/s0.txt'),('s1',HERE/'reference_prompts/s1.txt'),
                      ('noegv',HERE/'candidate_noegv/prompts/system.md'),('full',HERE/'candidate_full/prompts/system.md')]:
        raw=path.read_bytes();text=raw.decode().replace('\r\n','\n')
        results[name]=dict(standalone_instruction_tokens=len(tokenizer.encode(text,add_special_tokens=False)),
            raw_packaged_tokens=len(tokenizer.encode(raw.decode(),add_special_tokens=False)),
            words=len(text.split()),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    result=dict(status='MEASURED_CPU_TOKENIZER',model_source='google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2',
        add_special_tokens=False,scope='Standalone instruction after official CRLF-to-LF include loading; excludes chat template, tool schemas, Issue and history. Not GPU Token cost.',
        tokenizer_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in model.glob('tokenizer*') if p.is_file()},prompts=results)
    atomic_json(output/'prompt_tokens.json',result)
    return result


def main(output,stage):
    assert sys.platform=='linux','Official Linux CPU execution required'
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    import torch
    assert torch.cuda.device_count()==0,'CPU-only execution guard: stop if GPU unexpectedly allocated'
    atomic_json(output/'cpu_gate.json',dict(passed=False,stage='start',GPU=False,Gemma_inference=False))
    atomic_json(output/'versions.json',{p:importlib.metadata.version(p) for p in ('swegemma','adk-submission','adk-eval-core','google-adk','google-genai','litellm','pytest','transformers')})
    compiled=asyncio.run(compiler_empty_state(output))
    tokens=tokenize(output)
    original=None
    if stage=='full':
        old=subprocess.run([sys.executable,'-m','s1.cpu',str(output/'legacy77')],capture_output=True,text=True,timeout=1200)
        (output/'legacy77.stdout.log').write_text(old.stdout);(output/'legacy77.stderr.log').write_text(old.stderr)
        original=json.loads((output/'legacy77/cpu_gate.json').read_text());assert old.returncode==0 and original['passed']
    os.environ['URE_EVIDENCE']=str(output/'cases')
    from .tests.test_runner import RunnerTests
    all_tests=unittest.defaultTestLoader.loadTestsFromTestCase(RunnerTests)
    expensive=('test_F_real_300_second_boundary_each_candidate','test_F_actual_120_second_command_limit_and_no_late_write')
    selected=[t for t in all_tests if stage=='full' or t._testMethodName not in expensive]
    suite=unittest.TestSuite(selected)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromName('u_re.v01.tests.test_static'))
    if stage=='full':
        suite.addTests(unittest.defaultTestLoader.loadTestsFromNames(['s1.infrastructure_recovery.tests.test_wire','s1.verifier_v3.tests']))
    with (output/'tests.log').open('x') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    passed=result.wasSuccessful() and not result.skipped
    gate=dict(passed=passed,stage=stage,tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        skipped=len(result.skipped),compiler=compiled,legacy=original,actual_300_second_boundaries=stage=='full',
        actual_120_second_command_test=stage=='full',full_budget_gate='TESTED' if stage=='full' else 'NOT_RUN',
        CPU_ACCEPTANCE='CPU_PASS' if passed and stage=='full' else ('SMOKE_ONLY' if passed else 'FAILED'),
        GPU_status='GPU_NOT_TESTED',scripted_HTTP=True,real_official_Runner=True,real_sandbox_tools=True,
        hard_post_submit_termination=False,no_progress_hard_enforcement=False,
        scope='Test success proves tool paths and documents expected negative controls. It does not prove autonomous Gemma strategy compliance.')
    atomic_json(output/'cpu_gate.json',gate)
    print(json.dumps({k:v for k,v in gate.items() if k not in ('compiler','legacy')},indent=2),flush=True)
    return 0 if passed else 1


if __name__=='__main__':
    sys.exit(main(sys.argv[1],sys.argv[2]))
