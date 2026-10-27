"""Passive existing HTTP observer plus the required first-input identity gate.

No request rewriting, summarization, output override, safety reserve or repeated
context admission policy. This host research gate is not an Agent controller.
"""
from contextlib import contextmanager
import json
from pathlib import Path
from unittest.mock import patch

from harness_v2.evidence import atomic_bytes,atomic_json
from s1.infrastructure_recovery.wire import observe_http


class InitialInputMismatch(RuntimeError):pass


def check_initial(actual,expected):
    if actual!=expected:raise InitialInputMismatch('Initial complete model request differs from frozen CPU-derived input')
    if 'seed' in actual:raise InitialInputMismatch('S0 request must not gain an explicit seed')
    if actual.get('max_completion_tokens')!=16384 or actual.get('thinking_token_budget')!=4096:
        raise InitialInputMismatch('Frozen generation parameters differ')
    if actual.get('chat_template_kwargs')!={'enable_thinking':True}:
        raise InitialInputMismatch('Unexpected thinking/template parameter')


@contextmanager
def capture(directory,expected):
    import httpx
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    seen=False
    with observe_http(directory):
        send=httpx.AsyncClient.send
        async def checked(client,request,**kwargs):
            nonlocal seen
            if request.url.path.endswith('/chat/completions') and not seen:
                seen=True
                atomic_bytes(directory/'initial_request.json',request.content)
                body=json.loads(request.content)
                try:check_initial(body,expected)
                except Exception as exc:
                    atomic_json(directory/'INITIAL_INPUT_GATE.json',dict(passed=False,error_type=type(exc).__name__,forwarded=False))
                    raise
                atomic_json(directory/'INITIAL_INPUT_GATE.json',dict(passed=True,forwarded=True,
                    no_request_mutation=True,scope='first request identity only; no research Context Guard'))
            return await send(client,request,**kwargs)
        with patch('httpx.AsyncClient.send',checked):yield
