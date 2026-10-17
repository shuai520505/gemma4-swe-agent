"""Official LiteLLM transport tests; no Gemma inference is claimed."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, AsyncMock

from harness_v2.evidence import read_events
from s1 import MODEL
from .startup import observe_probe, R04_PROBE, run


class StartupTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self, *, content='READY', usage=50, failure=False):
        import httpx
        seen = []
        async def count(body):
            return dict(count=30050 if len(str(body)) > 10000 else 50, max_model_len=32768)
        async def transport(client, request, **kwargs):
            if request.url.path.endswith('/health'):
                return httpx.Response(200, request=request, content=b'')
            if request.url.path.endswith('/models'):
                return httpx.Response(200, request=request, json={'data':[{'id':MODEL}]})
            seen.append(json.loads(request.content))
            if failure:
                return httpx.Response(400, request=request, json={'error':'mock failure'})
            return httpx.Response(200, request=request, json=dict(id='mock', object='chat.completion',
                created=1, model=MODEL, choices=[dict(index=0, finish_reason='stop',
                message=dict(role='assistant', content=content))],
                usage=dict(prompt_tokens=usage, completion_tokens=1, total_tokens=usage+1)))
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(__import__('shutil').rmtree, directory)
        with patch('httpx.AsyncClient.send', transport):
            try:
                result = await observe_probe('http://127.0.0.1:8000/v1', MODEL, 'EMPTY',
                    directory=directory, counter=count)
            except BaseException:
                self.events = read_events(directory/'startup.jsonl')
                self.gate = json.loads((directory/'startup_gate.json').read_text())
                raise
        self.events = read_events(directory/'startup.jsonl')
        self.gate = json.loads((directory/'startup_gate.json').read_text())
        return result, seen

    async def test_same_r04_probe_and_real_client_success(self):
        from s1.preflight import check_model
        self.assertIs(R04_PROBE, check_model)
        result, seen = await self.exercise()
        self.assertTrue(self.gate['passed'])
        self.assertEqual(len(seen), 1)
        self.assertEqual(result['oversize'][-1]['decision'], 'reject')
        self.assertEqual(len([e for e in self.events if e['kind']=='tokenize_request']), 2)
        self.assertEqual(len([e for e in self.events if e['kind']=='tokenize_response']), 2)
        self.assertEqual(len([e for e in self.events if e['kind']=='http_response']), 3)

    async def test_empty_generation_stops_and_preserves(self):
        with self.assertRaisesRegex(AssertionError, 'no text'):
            await self.exercise(content='')
        self.assertFalse(self.gate['passed'])
        self.assertTrue(any(e['kind']=='http_response' for e in self.events))

    async def test_count_disagreement_stops_and_preserves(self):
        with self.assertRaises(AssertionError):
            await self.exercise(usage=49)
        self.assertFalse(self.gate['passed'])
        self.assertEqual(self.gate['actual_generation_requests'], 1)

    async def test_transport_failure_preserves_request_and_response(self):
        with self.assertRaises(Exception):
            await self.exercise(failure=True)
        self.assertFalse(self.gate['passed'])
        self.assertTrue(any(e['kind']=='http_error' for e in self.events))
        self.assertTrue(any(e['kind']=='http_response' and e['status']==400 for e in self.events))

    async def test_run_reuses_r04_controller_and_original_clock(self):
        from . import EXPERIMENT_ID
        from s1 import preflight
        directory=Path(tempfile.mkdtemp()); self.addCleanup(__import__('shutil').rmtree,directory)
        (directory/'s1').mkdir()
        plan=dict(experiment_id=EXPERIMENT_ID,batches={'smoke':[
            dict(instance_id='requests_7328',arm='control'),
            dict(instance_id='requests_7328',arm='e1_output8192')]})
        (directory/'s1/gpu_protocol.json').write_text(json.dumps(plan))
        async def controller(source, output, batch, *, session_started):
            self.assertEqual(session_started, 1234.5)
            await preflight.check_model('url','path','key')
        with patch('s1.session.run',controller), patch(
                's1.experiments.e1_outputcap_smoke_02.startup.observe_probe',new_callable=AsyncMock) as probe:
            await run(directory,directory,'smoke',session_started=1234.5)
            probe.assert_awaited_once_with('url','path','key',directory=directory/'startup')
        self.assertIs(preflight.check_model,R04_PROBE)

    async def test_old_experiment_is_rejected(self):
        directory=Path(tempfile.mkdtemp()); self.addCleanup(__import__('shutil').rmtree,directory)
        (directory/'s1').mkdir()
        (directory/'s1/gpu_protocol.json').write_text(json.dumps({'experiment_id':'s1-e1-public-01'}))
        with self.assertRaises(AssertionError):
            await run(directory,directory,'smoke',session_started=0)
