"""Full official Runner + empty session + mocked HTTP; no Gemma inference."""
import hashlib
import json
import os
from pathlib import Path
import re
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]


class RunnerCompatibilityTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self, arm, *, double_braces=False, expect_error=False):
        import httpx
        from adk_submission import ModelRegistry, compile_submission
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.adk.models.lite_llm import LiteLlm, LiteLLMClient
        from google.genai import types
        from swegemma.config import build_submission_limits
        from swegemma.context import SwegemmaContext
        from harness_v2.official import GuardedClient
        from cure.request_guard import ConfiguredGuard
        from cure.runtime_config import ResearchConfig, validate_compiled
        from cure import MODEL
        prompt=(ROOT/'cure/candidates'/arm/'prompts/system.md').read_text(encoding='utf-8')
        seen=[]; admission=[]; counts=[]
        async def counter(body):
            counts.append(body)
            return dict(count=100,max_model_len=32768)
        async def send(_client,request,**kwargs):
            self.assertEqual(request.url.host,'127.0.0.1')
            body=json.loads(request.content); seen.append(body)
            return httpx.Response(200,request=request,json=dict(id='full-runner-cpu-mock',object='chat.completion',
                created=1,model=MODEL,choices=[dict(index=0,finish_reason='stop',
                    message=dict(role='assistant',content='CPU mock completion'))],
                usage=dict(prompt_tokens=100,completion_tokens=3,total_tokens=103)))
        model=LiteLlm(model='openai/'+MODEL,api_base='http://127.0.0.1:8000/v1',api_key='EMPTY')
        guard=ConfiguredGuard(counter,LiteLLMClient().acompletion,core_issue='CPU Runner compatibility probe.',
            config=ResearchConfig(),emit=admission.append)
        model.llm_client=GuardedClient(guard)
        models=ModelRegistry();models.register(MODEL,model)
        limits,constraints=build_submission_limits()
        agent=compile_submission(ROOT/'cure/candidates'/arm,SwegemmaContext().create_tools(),models,
            limits=limits,generation_constraints=constraints)
        validate_compiled(agent,ResearchConfig())
        self.assertEqual(agent.instruction,prompt)
        if double_braces: agent.instruction=prompt.replace('{JSON}','{{JSON}}')
        sessions=InMemorySessionService()
        session=await sessions.create_session(app_name='cure_compat_cpu',user_id='cpu',state={})
        self.assertEqual(session.state,{})
        runner=Runner(agent=agent,app_name='cure_compat_cpu',session_service=sessions)
        events=[]; failure=None
        try:
            with patch('httpx.AsyncClient.send',send):
                try:
                    async for event in runner.run_async(user_id='cpu',session_id=session.id,
                        new_message=types.Content(role='user',parts=[types.Part(text='CPU Runner compatibility probe.')])):
                        events.append(event.model_dump(mode='json',exclude_none=True))
                except KeyError as exc:
                    if not expect_error: raise
                    failure=str(exc)
            if expect_error:
                self.assertIsNotNone(failure)
                self.assertIn('Context variable not found',failure)
                self.assertIn('JSON',failure)
                self.assertEqual(seen,[])
                self.assertEqual(counts,[])
            else:
                self.assertIsNone(failure)
                self.assertEqual(len(seen),1)
                self.assertEqual(len(counts),1)
                system='\n'.join(m['content'] for m in seen[0]['messages'] if m['role']=='system')
                self.assertIn(prompt.strip(),system)
                self.assertEqual(seen[0].get('max_completion_tokens',seen[0].get('max_tokens')),8192)
                self.assertEqual(seen[0]['thinking_token_budget'],4096)
                self.assertEqual(seen[0]['seed'],17)
                self.assertEqual(len(seen[0]['tools']),6)
                if arm=='cure_v01_c1':
                    example=prompt[prompt.index('{"contracts"'):prompt.index('"decision_changed":true}')+len('"decision_changed":true}')]
                    self.assertIn(example,system)
                    json.loads(example)
                    for term in ('Prompt-only CURE','uncertainty','proposed_probe','contradictory result',
                                 'estimated_cost','Compare expected uncertainty reduction'):
                        self.assertIn(term,system)
            evidence=os.environ.get('CURE_COMPAT_CPU_DIR')
            if evidence:
                dest=Path(evidence)/(arm+('-double-braces' if double_braces else ''));dest.mkdir(parents=True,exist_ok=False)
                data=dict(arm=arm,empty_initial_session_state=True,real_official_runner=True,mocked_HTTP=True,
                    mocked_counter=True,expected_failure=expect_error,observed_error=failure,
                    HTTP_requests=len(seen),prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                    wire=seen,admission=admission,events=events,assertions_passed=True)
                (dest/'result.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
                if seen:
                    (dest/'rendered-system.txt').write_text(system,encoding='utf-8')
        finally:
            await runner.close()

    async def test_B_full_runner(self): await self.exercise('checklist')
    async def test_frozen_C_known_failure(self): await self.exercise('cure_v01',expect_error=True)
    async def test_C1_full_runner_JSON_preserved(self): await self.exercise('cure_v01_c1')
    async def test_double_braces_are_not_escape(self):
        await self.exercise('cure_v01',double_braces=True,expect_error=True)

    async def test_exact_change_and_complete_ADK_pattern_scan(self):
        from google.adk.utils.instructions_utils import _is_valid_state_name
        old=ROOT/'cure/candidates/cure_v01';new=ROOT/'cure/candidates/cure_v01_c1'
        for name in ('agent.yaml','eval_config.yaml','sampling.yaml'):
            self.assertEqual((old/name).read_bytes(),(new/name).read_bytes())
        original=(old/'prompts/system.md').read_text(encoding='utf-8')
        candidate=(new/'prompts/system.md').read_text(encoding='utf-8')
        self.assertEqual(original.count('<cure>{JSON}</cure>'),1)
        self.assertEqual(candidate,original.replace('<cure>{JSON}</cure>','<cure>JSON object</cure>'))
        findings={}
        for arm in ('checklist','cure_v01','cure_v01_c1'):
            prompt=(ROOT/'cure/candidates'/arm/'prompts/system.md').read_text(encoding='utf-8')
            matches=[]
            for m in re.finditer(r'{+[^{}]*}+',prompt):
                var=m.group().lstrip('{').rstrip('}').strip()
                name=var.removesuffix('?')
                matches.append(dict(literal=m.group(),line=prompt[:m.start()].count('\n')+1,
                    interpreted_as_state=_is_valid_state_name(name) or name.startswith('artifact.')))
            findings[arm]=matches
        self.assertEqual([x['literal'] for x in findings['cure_v01'] if x['interpreted_as_state']],['{JSON}'])
        self.assertFalse(any(x['interpreted_as_state'] for x in findings['cure_v01_c1']))
        self.assertFalse(any(x['interpreted_as_state'] for x in findings['checklist']))
        out=os.environ.get('CURE_COMPAT_CPU_DIR')
        if out:
            Path(out).mkdir(parents=True,exist_ok=True)
            (Path(out)/'complete-prompt-pattern-scan.json').write_text(json.dumps(findings,indent=2),encoding='utf-8')


if __name__=='__main__': unittest.main()
