import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import httpx

from harness_v2.evidence import read_events
from s1.infrastructure_recovery.wire import observe_http,audit_requests


class WireTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.directory=Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.accepted=asyncio.Event();self.release=asyncio.Event();self.handlers=[]
        async def handler(reader,writer):
            self.handlers.append(asyncio.current_task())
            try:
                headers=await reader.readuntil(b'\r\n\r\n')
                length=int(next(line.split(b':',1)[1] for line in headers.splitlines() if line.lower().startswith(b'content-length:')))
                self.server_body=json.loads(await reader.readexactly(length))
                self.accepted.set();await self.release.wait()
                data=json.dumps(dict(usage=dict(prompt_tokens=5,completion_tokens=2,total_tokens=7))).encode()
                writer.write(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: '+str(len(data)).encode()+b'\r\nConnection: close\r\n\r\n'+data)
                await writer.drain()
            except (ConnectionError,asyncio.CancelledError,asyncio.IncompleteReadError):pass
            finally:
                writer.close()
                try:await writer.wait_closed()
                except ConnectionError:pass
        self.server=await asyncio.start_server(handler,'127.0.0.1',0)
        self.url=f'http://127.0.0.1:{self.server.sockets[0].getsockname()[1]}/v1/chat/completions'

    async def asyncTearDown(self):
        self.release.set();self.server.close();await self.server.wait_closed()
        for task in self.handlers:
            if not task.done():task.cancel()
        await asyncio.gather(*self.handlers,return_exceptions=True)

    async def request(self):
        async with httpx.AsyncClient(trust_env=False,timeout=5) as client:
            return await client.post(self.url,json=dict(model='cpu',messages=[],stream=False))

    async def test_real_socket_cancel_after_server_received_request(self):
        with observe_http(self.directory):
            task=asyncio.create_task(self.request())
            await asyncio.wait_for(self.accepted.wait(),2)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):await task
        self.assertEqual(self.server_body['model'],'cpu')
        rows=read_events(self.directory/'http_lifecycle.jsonl')
        self.assertEqual([r['kind'] for r in rows],['request_sent','cancelled','terminal_status'])
        self.assertEqual(len({r['request_id'] for r in rows}),1)
        self.assertIsNone(rows[-1]['usage'])
        self.assertFalse(audit_requests(self.directory)['passed'])
        gate=audit_requests(self.directory,deadline_evidence=dict(official_agent_deadline=True,cleanup_verified=True))
        self.assertTrue(gate['passed']);self.assertTrue(gate['partial_token_usage'])
        self.assertIsNone(gate['rows'][0]['usage'])

    async def test_outer_deadline_cancel_propagates_without_changing_semantics(self):
        with observe_http(self.directory):
            task=asyncio.create_task(self.request())
            await asyncio.wait_for(self.accepted.wait(),2)
            with self.assertRaises(TimeoutError):await asyncio.wait_for(task,.05)
        self.assertEqual(read_events(self.directory/'http_lifecycle.jsonl')[-1]['status'],'cancelled')

    async def test_success_records_original_payload_and_usage(self):
        with observe_http(self.directory):
            task=asyncio.create_task(self.request())
            await asyncio.wait_for(self.accepted.wait(),2);self.release.set()
            self.assertEqual((await task).status_code,200)
        result=audit_requests(self.directory)
        self.assertTrue(result['passed']);self.assertTrue(result['usage_complete'])
        self.assertEqual(result['observed_response_usage']['total_tokens'],7)
        self.assertIn('raw_body_utf8',read_events(self.directory/'http_wire.jsonl')[0])

    async def test_transport_timeout_is_distinct(self):
        async def fail(*args,**kwargs):raise httpx.ReadTimeout('CPU mock transport timeout')
        with patch('httpx.AsyncClient.send',fail),observe_http(self.directory):
            with self.assertRaises(httpx.ReadTimeout):await self.request()
        result=audit_requests(self.directory)
        self.assertFalse(result['passed']);self.assertEqual(result['rows'][0]['terminal_status'],'timeout')

    async def test_transport_error_is_not_cancel(self):
        async def fail(*args,**kwargs):raise httpx.ConnectError('CPU mock refusal')
        with patch('httpx.AsyncClient.send',fail),observe_http(self.directory):
            with self.assertRaises(httpx.ConnectError):await self.request()
        self.assertEqual(audit_requests(self.directory)['rows'][0]['terminal_status'],'transport_error')

    async def test_missing_terminal_is_never_ignored(self):
        with observe_http(self.directory):
            task=asyncio.create_task(self.request())
            await asyncio.wait_for(self.accepted.wait(),2)
            incomplete=audit_requests(self.directory,deadline_evidence=dict(official_agent_deadline=True,cleanup_verified=True))
            self.assertFalse(incomplete['passed'])
            self.assertEqual(incomplete['rows'][0]['terminal_status'],'unknown')
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):await task

    async def test_logging_failure_does_not_swallow_CancelledError(self):
        async def fail(*args,**kwargs):raise asyncio.CancelledError()
        with patch('httpx.AsyncClient.send',fail),patch('harness_v2.evidence.Journal.append',side_effect=OSError('disk full')),observe_http(self.directory):
            with self.assertRaises(asyncio.CancelledError):await self.request()

    async def test_received_response_without_usage_is_not_a_complete_gate(self):
        async def response(client,request,**kwargs):
            return httpx.Response(200,request=request,json={'choices':[]})
        with patch('httpx.AsyncClient.send',response),observe_http(self.directory):
            await self.request()
        result=audit_requests(self.directory)
        self.assertFalse(result['passed'])
        self.assertIn('missing_response_usage',result['reasons'])
        self.assertIsNone(result['observed_response_usage'])

    async def test_cancel_during_response_body_read_has_a_terminal(self):
        reading=asyncio.Event()
        class SlowBody(httpx.AsyncByteStream):
            async def __aiter__(self):
                reading.set();await asyncio.Event().wait()
                yield b'never returned'
        async def response(client,request,**kwargs):
            return httpx.Response(200,request=request,stream=SlowBody())
        with patch('httpx.AsyncClient.send',response),observe_http(self.directory):
            task=asyncio.create_task(self.request())
            await asyncio.wait_for(reading.wait(),2)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):await task
        events=read_events(self.directory/'http_lifecycle.jsonl')
        self.assertTrue(events[-2]['response_object_received'])
        self.assertEqual(events[-1]['status'],'cancelled')
        self.assertIsNone(events[-1]['usage'])

    async def test_malformed_usage_stays_partial_in_terminal_and_aggregate(self):
        async def response(client,request,**kwargs):
            return httpx.Response(200,request=request,json={'usage':{'prompt_tokens':5}})
        with patch('httpx.AsyncClient.send',response),observe_http(self.directory):
            await self.request()
        self.assertTrue(read_events(self.directory/'http_lifecycle.jsonl')[-1]['partial_usage'])
        result=audit_requests(self.directory)
        self.assertFalse(result['passed']);self.assertIsNone(result['observed_response_usage'])
