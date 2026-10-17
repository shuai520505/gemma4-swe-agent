"""The exact startup probe through official LiteLLMClient -> mocked HTTP."""
import json
import unittest
from unittest.mock import patch
from s1 import MODEL


class PreflightTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_client_requires_explicit_tools_even_without_tool_use(self):
        from google.adk.models.lite_llm import LiteLLMClient
        with self.assertRaisesRegex(TypeError,'tools'):
            await LiteLLMClient().acompletion(model='openai/'+MODEL,messages=[])

    async def test_exact_shared_probe_hits_HTTP_once_and_rejects_oversize(self):
        import httpx
        from s1.preflight import check_model
        seen=[];counted=[]
        async def count(body):
            counted.append(body)
            return dict(count=30050 if any(len(m.get('content',''))>10000 for m in body['messages']) else 50,max_model_len=32768)
        async def send(_client,request,**kwargs):
            seen.append(json.loads(request.content))
            return httpx.Response(200,request=request,json=dict(id='preflight-cpu-mock',object='chat.completion',
                created=1,model=MODEL,choices=[dict(index=0,finish_reason='stop',message=dict(role='assistant',content='READY'))],
                usage=dict(prompt_tokens=50,completion_tokens=1,total_tokens=51)))
        with patch('httpx.AsyncClient.send',send):
            result=await check_model('http://127.0.0.1:8000/v1',MODEL,'EMPTY',counter=count)
        self.assertEqual(len(seen),1)
        self.assertEqual(len(counted),2)
        self.assertEqual(seen[0]['max_completion_tokens'],16)
        self.assertFalse(seen[0]['chat_template_kwargs']['enable_thinking'])
        self.assertEqual(result['oversize'][0]['decision'],'reject')
        self.assertEqual(result['admission'][0]['input_tokens'],50)

    async def test_stopped_experiment_cannot_build_another_GPU_notebook(self):
        from s1.prepare import gpu
        with self.assertRaisesRegex(RuntimeError,'globally stopped'):
            gpu('smoke','r03',None,None)
