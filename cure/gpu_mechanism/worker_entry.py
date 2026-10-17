"""Passively record real HTTP around the unchanged, CPU-gated CURE worker."""
import asyncio
import json
from pathlib import Path
import sys
import time
import httpx
from harness_v2.evidence import Journal


def main():
    directory = Path(sys.argv[2])
    journal = Journal(directory)
    original = httpx.AsyncClient.send
    async def observed(client, request, **kwargs):
        relevant = request.url.path.endswith('/chat/completions')
        if relevant:
            body = json.loads(request.content)
            journal.append(dict(kind='http_request', body=body), filename='http_wire.jsonl')
            if request.url.host not in ('127.0.0.1', 'localhost'):
                raise ValueError('Nonlocal model routing')
            if body.get('stream'):
                raise ValueError('Unregistered streaming path')
            started = time.monotonic()
        response = await original(client, request, **kwargs)
        if relevant:
            raw = await response.aread()
            try: payload = json.loads(raw)
            except ValueError: payload = dict(non_json_response=raw.decode(errors='replace'))
            journal.append(dict(kind='http_response', status=response.status_code,
                elapsed_seconds=time.monotonic()-started, body=payload), filename='http_wire.jsonl')
        return response
    httpx.AsyncClient.send = observed
    try:
        from cure.worker import main as native_main
        native_main()
    finally:
        httpx.AsyncClient.send = original


if __name__ == '__main__': main()
