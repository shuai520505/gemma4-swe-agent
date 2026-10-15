"""Real organizer API checks on CPU. No Gemma response is generated here."""
import asyncio
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


class OfficialApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_compiler_defaults_and_guard_survive_model_clone(self):
        from adk_submission import ModelRegistry,compile_submission
        from google.adk.models.lite_llm import LiteLlm
        from swegemma.config import build_submission_limits
        from swegemma.context import SwegemmaContext
        from harness_v2.official import GuardedClient
        from harness_v2.context_budget import RequestGuard
        async def count(body): return {'count':100,'max_model_len':32768}
        async def generate(**args): return args
        models=ModelRegistry()
        client=GuardedClient(RequestGuard(count,generate,core_issue='original issue'))
        model=LiteLlm(model='openai/gemma-4-31b-it-qat-w4a16-ct',api_base='http://127.0.0.1:8000/v1',api_key='EMPTY')
        model.llm_client=client
        models.register('gemma-4-31b-it-qat-w4a16-ct',model)
        limits,constraints=build_submission_limits()
        self.assertEqual(constraints.defaults['max_output_tokens'],16384)
        for arm in ('v0','v1'):
            agent=compile_submission(ROOT/'candidates'/arm/'submission',SwegemmaContext().create_tools(),models,
                limits=limits,generation_constraints=constraints)
            self.assertEqual(agent.generate_content_config.max_output_tokens,16384)
            self.assertEqual(len(agent.tools),6)
            self.assertFalse(agent.sub_agents)
            self.assertIs(agent.model.llm_client,client)

    async def test_actual_adk_request_serialization_is_guarded(self):
        from google.adk.models.lite_llm import LiteLlm
        from google.adk.models.llm_request import LlmRequest
        from google.genai import types
        from harness_v2.official import GuardedClient
        from harness_v2.context_budget import RequestGuard,ContextBudgetExceeded
        counted=[]
        async def counter(body):
            counted.append(body)
            return {'count':16385,'max_model_len':32768}
        async def generate(**args): self.fail('Oversize generation must not reach LiteLLM')
        model=LiteLlm(model='openai/gemma-4-31b-it-qat-w4a16-ct')
        model.llm_client=GuardedClient(RequestGuard(counter,generate,core_issue='original issue'))
        req=LlmRequest(model=model.model,contents=[types.Content(role='user',parts=[types.Part(text='original issue')])],
            config=types.GenerateContentConfig(max_output_tokens=16384,system_instruction='frozen prompt',
                tools=[types.Tool(function_declarations=[types.FunctionDeclaration(name='read_file',
                    parameters=types.Schema(type='OBJECT',properties={'filepath':types.Schema(type='STRING')}))])]))
        with self.assertRaises(ContextBudgetExceeded):
            async for _ in model.generate_content_async(req): pass
        self.assertEqual(counted[0]['tools'][0]['function']['name'],'read_file')
        self.assertEqual(counted[0]['messages'][0]['content'],'frozen prompt')

    async def test_real_adk_event_persists_before_task_returns(self):
        from google.adk.events import Event
        from google.genai import types
        from harness_v2.official import DurableContext
        from harness_v2.evidence import Journal
        with tempfile.TemporaryDirectory() as tmp:
            j=Journal(tmp)
            c=DurableContext(journal=j)
            event=Event(author='v0_coding_agent',content=types.Content(role='model',parts=[
                types.Part(function_call=types.FunctionCall(name='read_file',args={'filepath':'x.py'}))]))
            c.handle_adk_event(event,agent_name='v0_coding_agent')
            c.handle_adk_event(event,agent_name='v0_coding_agent')
            lines=(Path(tmp)/'adk_events.jsonl').read_text().splitlines()
            self.assertEqual(len(lines),1)
            self.assertIn('read_file',lines[0])
            self.assertTrue((Path(tmp)/'incremental_trace_legacy.json').exists())
            self.assertFalse((Path(tmp)/'official_result.json').exists())

    async def test_native_patch_and_trace_saved_at_agent_boundary(self):
        from adk_eval_core.tracing import SessionTrace
        from adk_submission import ModelRegistry
        from swegemma.evaluate import Evaluator
        from swegemma.config import EvalConfig
        from harness_v2.evidence import Journal
        from harness_v2.official import DurableEvaluator
        with tempfile.TemporaryDirectory() as tmp:
            j=Journal(tmp)
            evaluator=DurableEvaluator(EvalConfig(tasks_path=Path(tmp)/'tasks.jsonl',
                snapshots_dir=Path(tmp),results_dir=Path(tmp)/'harness',submission_dir=ROOT/'candidates/v0/submission',
                models=ModelRegistry(),sandbox='subprocess'),journal=j)
            trace=SessionTrace(); trace.start(); trace.record_custom('task_prompt','original issue')
            async def native_boundary(*args,**kwargs): return 'native patch',None,trace
            with patch.object(Evaluator,'_run_agent_sandbox',native_boundary):
                await evaluator._run_agent_sandbox(None,None,1,1)
            self.assertEqual((Path(tmp)/'latest.patch').read_text(),'native patch')
            self.assertTrue((Path(tmp)/'agent_boundary_trace.json').is_file())
            self.assertFalse((Path(tmp)/'official_result.json').exists())

    async def test_official_result_fields_and_timeout_classification(self):
        from swegemma.models import TaskResult
        from harness_v2.outcomes import normalize
        raw=TaskResult(instance_id='cpu_scripted',resolved=False,test_exit_code=-1,error='Agent timed out')
        dumped=raw.model_dump(exclude={'trace'},mode='json')
        before=json.dumps(dumped,sort_keys=True)
        self.assertEqual(normalize(dumped,started=True)['status'],'unknown')
        self.assertEqual(before,json.dumps(dumped,sort_keys=True))
        self.assertIn('error_message',dumped)


if __name__=='__main__': unittest.main()
