"""Passive local HTTP recording. This module is host research code, not an Agent tool."""
import json
from pathlib import Path
import sys
import time
from harness_v2.evidence import Journal


def main():
    import httpx
    journal=Journal(Path(sys.argv[2]))
    original=httpx.AsyncClient.send
    async def observe(client,request,**kwargs):
        relevant=request.url.path.endswith('/chat/completions')
        if relevant:
            body=json.loads(request.content)
            journal.append(dict(kind='http_request',body=body),filename='http_wire.jsonl')
            if request.url.host not in ('127.0.0.1','localhost') or body.get('stream'):
                raise ValueError('Require local nonstreaming model route')
            started=time.monotonic()
        response=await original(client,request,**kwargs)
        if relevant:
            raw=await response.aread()
            try: data=json.loads(raw)
            except ValueError: data=dict(non_json=raw.decode(errors='replace'))
            journal.append(dict(kind='http_response',status=response.status_code,
                elapsed_seconds=time.monotonic()-started,body=data),filename='http_wire.jsonl')
        return response
    httpx.AsyncClient.send=observe
    try:
        from .worker import main as run
        run()
    finally:
        httpx.AsyncClient.send=original


if __name__=='__main__': main()
