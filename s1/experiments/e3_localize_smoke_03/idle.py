"""Read-only server scheduler evidence; client cancellation alone is insufficient."""
import asyncio
from pathlib import Path
import re
import time
from harness_v2.evidence import Journal,atomic_json


def parse_metrics(raw):
    values={}
    for line in raw.splitlines():
        if not line or line.startswith('#'):continue
        match=re.fullmatch(r'(vllm:num_requests_(?:running|waiting))(?:\{[^\n]*\})?\s+([0-9.eE+\-]+)(?:\s+\d+)?',line)
        if match:values.setdefault(match[1],[]).append(float(match[2]))
    if set(values)!={'vllm:num_requests_running','vllm:num_requests_waiting'}:
        return dict(known=False,idle=False,values=values)
    return dict(known=True,idle=all(v==0 for rows in values.values() for v in rows),values=values)


async def require_idle(base_url,directory,*,seconds=60):
    import httpx
    directory=Path(directory);journal=Journal(directory)
    deadline=time.monotonic()+seconds;consecutive=0;index=0
    try:
        async with httpx.AsyncClient(trust_env=False,timeout=10) as client:
            while time.monotonic()<deadline:
                result=await client.get(base_url.rstrip('/').removesuffix('/v1')+'/metrics')
                result.raise_for_status();raw=result.text
                (directory/f'metrics-{index:03d}.txt').write_text(raw)
                parsed=parse_metrics(raw);journal.append(dict(kind='server_scheduler_snapshot',index=index,**parsed))
                if not parsed['known']:raise RuntimeError('Server scheduler gauges unavailable; reclamation unknown')
                consecutive=consecutive+1 if parsed['idle'] else 0
                if consecutive>=3:
                    gate=dict(passed=True,consecutive_idle_snapshots=consecutive,
                        scope='Server-reported zero running/waiting requests; no other clients permitted')
                    atomic_json(directory/'idle_gate.json',gate);return gate
                index+=1;await asyncio.sleep(1)
        raise TimeoutError('Server requests not proven reclaimed before deadline')
    except BaseException as exc:
        atomic_json(directory/'idle_gate.json',dict(passed=False,error=repr(exc)))
        raise
