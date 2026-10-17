"""Durable passive startup observation around the exact CPU-tested r04 probe."""
import json
from pathlib import Path
import time
from unittest.mock import patch

from harness_v2.context_budget import VllmCounter
from harness_v2.evidence import Journal, atomic_json
from s1.preflight import check_model as R04_PROBE


async def observe_probe(base_url, model_path, key, *, directory, counter=None):
    import httpx
    journal = Journal(directory)
    native_count = counter or VllmCounter(base_url, key)
    original_send = httpx.AsyncClient.send
    requests, responses = [], []

    async def count(body):
        journal.append(dict(kind='tokenize_request', body=body), 'startup.jsonl')
        try:
            value = await native_count(body)
        except BaseException as exc:
            journal.append(dict(kind='tokenize_error', error=repr(exc)), 'startup.jsonl')
            raise
        journal.append(dict(kind='tokenize_response', body=value), 'startup.jsonl')
        return value

    async def send(client, request, **kwargs):
        # Local startup only; no headers or credentials are recorded.
        if request.url.host not in ('localhost', '127.0.0.1'):
            raise ValueError('Startup request routed outside local vLLM')
        body = json.loads(request.content) if request.content else None
        event = dict(kind='http_request', method=request.method,
                     url=str(request.url), body=body)
        journal.append(event, 'startup.jsonl')
        if request.url.path.endswith('/chat/completions'):
            requests.append(body)
        started = time.monotonic()
        try:
            response = await original_send(client, request, **kwargs)
            raw = await response.aread()
            try:
                value = json.loads(raw)
            except ValueError:
                value = dict(text=raw.decode(errors='replace'))
            journal.append(dict(kind='http_response', url=str(request.url),
                status=response.status_code, body=value,
                elapsed_seconds=time.monotonic()-started), 'startup.jsonl')
            if request.url.path.endswith('/chat/completions'):
                responses.append(value)
            response.raise_for_status()
            return response
        except BaseException as exc:
            journal.append(dict(kind='http_error', url=str(request.url), error=repr(exc)), 'startup.jsonl')
            raise

    started = time.monotonic()
    try:
        with patch('httpx.AsyncClient.send', send):
            async with httpx.AsyncClient(trust_env=False) as client:
                root = base_url.rstrip('/').removesuffix('/v1')
                await client.get(root+'/health')
                served = (await client.get(base_url.rstrip('/')+'/models')).json()
                assert any(row['id'] == str(model_path) for row in served['data'])
            # This is the unmodified r04 function (including explicit tools=None).
            result = await R04_PROBE(base_url, model_path, key, counter=count)
        content = result['response']['choices'][0]['message'].get('content')
        assert isinstance(content, str) and content.strip(), 'Startup generated no text'
        assert len(requests) == len(responses) == 1, 'Startup generation count drift'
        assert requests[0]['model'] == str(model_path)
        assert requests[0]['max_completion_tokens'] == 16
        assert requests[0]['chat_template_kwargs']['enable_thinking'] is False
        assert responses[0]['usage']['prompt_tokens'] == result['admission'][-1]['input_tokens']
        assert result['oversize'][-1]['decision'] == 'reject'
        for row in result['admission'] + result['oversize']:
            journal.append(row, 'startup.jsonl')
        result.update(startup_seconds=time.monotonic()-started,
                      actual_generation_requests=len(requests), valid_text=True,
                      original_probe='s1.preflight.check_model (r04, unchanged)')
        atomic_json(Path(directory)/'startup_gate.json', dict(passed=True, **result))
        return result
    except BaseException as exc:
        atomic_json(Path(directory)/'startup_gate.json', dict(passed=False,
            error=repr(exc), startup_seconds=time.monotonic()-started,
            actual_generation_requests=len(requests)))
        raise


async def run(source, output, batch, *, session_started):
    from . import EXPERIMENT_ID
    from s1 import preflight, session
    plan = json.loads((Path(source)/'s1/gpu_protocol.json').read_text())
    assert plan['experiment_id'] == EXPERIMENT_ID
    assert batch == 'smoke' and set(plan['batches']) == {'smoke'}
    assert [(r['instance_id'], r['arm']) for r in plan['batches']['smoke']] == [
        ('requests_7328', 'control'), ('requests_7328', 'e1_output8192')]

    async def observed(base_url, model_path, key):
        return await observe_probe(base_url, model_path, key, directory=Path(output)/'startup')

    # Instrumentation scope ends before any successor Notebook can run. The
    # controller, worker, context guard, tools and generation settings are r04.
    with patch.object(preflight, 'check_model', observed):
        return await session.run(source, output, batch, session_started=session_started)
