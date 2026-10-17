"""Actual Compiler -> empty-state ADK Runner -> mocked HTTP, two model turns."""
import json
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
from s1 import MODEL
from s1.config import Config,validate_compiled
from s1.guard import Guard

ROOT=Path(__file__).resolve().parents[1]


class FullRunnerTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self,arm='control',*,thinking=None,include=None,seed=17):
        import httpx
        from adk_submission import ModelRegistry,compile_submission,validate_directory
        from google.adk.models.lite_llm import LiteLlm,LiteLLMClient
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
        from google.adk.utils.instructions_utils import _is_valid_state_name
        from swegemma.config import build_submission_limits
        from swegemma.context import SwegemmaContext
        from harness_v2.official import GuardedClient
        manifest=json.loads((ROOT/'candidates.json').read_text())
        settings=dict(manifest[arm]['config'])
        if thinking is not None: settings['thinking_budget']=thinking
        settings.update(include_thoughts=include,seed=seed)
        config=Config(**settings)
        seen=[];counted=[];admissions=[]
        async def counter(body): counted.append(body);return dict(count=100,max_model_len=32768)
        async def send(_client,request,**kwargs):
            self.assertEqual(request.url.host,'127.0.0.1')
            body=json.loads(request.content);seen.append(body)
            if len(seen)==1:
                message=dict(role='assistant',content=None,reasoning='CPU reasoning before tool.',
                    tool_calls=[dict(id='call_status',type='function',function=dict(name='get_status',arguments='{}'))])
                finish='tool_calls'
            else:
                message=dict(role='assistant',content='CPU mock complete',reasoning='CPU final reasoning.')
                finish='stop'
            return httpx.Response(200,request=request,json=dict(id='s1-runner-mock-'+str(len(seen)),
                object='chat.completion',created=1,model=MODEL,
                choices=[dict(index=0,message=message,finish_reason=finish)],
                usage=dict(prompt_tokens=100,completion_tokens=9,total_tokens=109)))
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)
            for p in (ROOT/'candidates'/arm).rglob('*'):
                if p.is_file():
                    d=dest/p.relative_to(ROOT/'candidates'/arm);d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(p.read_bytes())
            agent_yaml=(dest/'agent.yaml').read_text()
            if thinking is not None: agent_yaml=agent_yaml.replace('thinking_budget: 4096',f'thinking_budget: {thinking}')
            if include is not None: agent_yaml+=f'    include_thoughts: {str(include).lower()}\n'
            if seed is None: agent_yaml=agent_yaml.replace('  seed: 17\n','')
            (dest/'agent.yaml').write_text(agent_yaml)
            prompt=(dest/'prompts/system.md').read_text()
            for m in re.finditer(r'{+[^{}]*}+',prompt):
                self.assertFalse(_is_valid_state_name(m.group().strip('{}').strip().removesuffix('?')))
            model=LiteLlm(model='openai/'+MODEL,api_base='http://127.0.0.1:8000/v1',api_key='EMPTY')
            model.llm_client=GuardedClient(Guard(counter,LiteLLMClient().acompletion,
                config=config,core_issue='S1 CPU Issue with JSON {"x": [1, 2]}.',emit=admissions.append))
            models=ModelRegistry();models.register(MODEL,model)
            limits,constraints=build_submission_limits();validate_directory(dest,limits=limits)
            agent=compile_submission(dest,SwegemmaContext().create_tools(),models,
                limits=limits,generation_constraints=constraints)
            validate_compiled(agent,config)
            # Do not change the organizer's temperature/top-p/top-k defaults.
            self.assertIsNone(agent.generate_content_config.temperature)
            self.assertIsNone(agent.generate_content_config.top_p)
            self.assertIsNone(agent.generate_content_config.top_k)
            sessions=InMemorySessionService()
            session=await sessions.create_session(app_name='s1_cpu',user_id='cpu',state={})
            self.assertEqual(session.state,{})
            runner=Runner(agent=agent,app_name='s1_cpu',session_service=sessions)
            events=[]
            try:
                with patch('httpx.AsyncClient.send',send):
                    async for e in runner.run_async(user_id='cpu',session_id=session.id,
                        new_message=types.Content(role='user',parts=[types.Part(text='S1 CPU Issue with JSON {"x": [1, 2]}.')])):
                        events.append(e.model_dump(mode='json',exclude_none=True))
                self.assertEqual(len(seen),2)
                system='\n'.join(m['content'] for m in seen[0]['messages'] if m['role']=='system')
                self.assertIn(prompt.strip(),system)
                for b in seen:
                    self.assertEqual(b.get('max_completion_tokens',b.get('max_tokens')),config.output_tokens)
                    self.assertEqual(b['chat_template_kwargs']['enable_thinking'],config.thinking_budget>0)
                    if config.thinking_budget:
                        self.assertEqual(b['thinking_token_budget'],config.thinking_budget)
                    else: self.assertNotIn('thinking_token_budget',b)
                    if config.seed is not None: self.assertEqual(b['seed'],config.seed)
                    else: self.assertNotIn('seed',b)
                    self.assertEqual(len(b['tools']),6)
                history=[m for m in seen[1]['messages'] if m['role']=='assistant' and m.get('tool_calls')]
                self.assertEqual(len(history),1)
                reasoning=history[0].get('reasoning') or history[0].get('reasoning_content')
                if include is False: self.assertFalse(reasoning)
                else: self.assertEqual(reasoning,'CPU reasoning before tool.')
                tool=[m for m in seen[1]['messages'] if m['role']=='tool']
                self.assertEqual(len(tool),1)
                self.assertIsInstance(json.loads(tool[0]['content']),dict)
                # LiteLLM omits only assistant content=None at HTTP serialization.
                # Keep every other key/value exact; GPU gate separately verifies
                # actual tokenizer counts against the serving response usage.
                counted_messages=json.loads(json.dumps(counted[1]['messages']))
                for m in counted_messages:
                    if m.get('role')=='assistant' and 'content' in m and m['content'] is None:
                        del m['content']
                self.assertEqual(counted_messages,seen[1]['messages'])
                out=os.environ.get('S1_RUNNER_EVIDENCE')
                if out:
                    case=f'{arm}-t{config.thinking_budget}-i{include}-s{seed}'
                    d=Path(out)/case;d.mkdir(parents=True,exist_ok=False)
                    (d/'result.json').write_text(json.dumps(dict(config=config.snapshot(),
                        real_runner=True,mocked_HTTP=True,real_inference=False,empty_session_state=True,
                        wire=seen,tokenizer_requests=counted,admission=admissions,events=events,
                        rendered_system=system,passed=True),indent=2))
            finally: await runner.close()

    async def test_control(self): await self.exercise()
    async def test_e1(self): await self.exercise('e1_output8192')
    async def test_e2(self): await self.exercise('e2_thinking0')
    async def test_e3(self): await self.exercise('e3_locate')
    async def test_e4(self): await self.exercise('e4_verify')
    async def test_positive_thinking_false_include_is_not_off(self): await self.exercise(include=False)
    async def test_explicit_true(self): await self.exercise(include=True)
    async def test_zero_true(self): await self.exercise(thinking=0,include=True)
    async def test_512(self): await self.exercise(thinking=512)
    async def test_seed_omitted(self): await self.exercise(seed=None)


if __name__=='__main__': unittest.main()
