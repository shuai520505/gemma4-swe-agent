"""Versioned passive HTTP observer: durable IDs, terminal states, no timeout policy."""
import asyncio
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import time
import uuid
from unittest.mock import patch

from harness_v2.evidence import Journal,read_events


@contextmanager
def observe_http(directory):
    import httpx
    journal=Journal(directory)
    original=httpx.AsyncClient.send
    persistence_errors=[]

    def record(event,filename):
        try:journal.append(event,filename=filename)
        except Exception as exc:
            # Logging failure must never replace or swallow cancellation.
            # The missing durable terminal will fail the evidence gate.
            persistence_errors.append(repr(exc))

    async def send(client,request,**kwargs):
        if not request.url.path.endswith('/chat/completions'):
            return await original(client,request,**kwargs)
        identity=uuid.uuid4().hex
        started=time.monotonic()
        status='unknown';response=None;usage=None
        try:body=json.loads(request.content)
        except ValueError:body=None
        digest=hashlib.sha256(request.content).hexdigest()
        record(dict(kind='http_request',request_id=identity,body=body,
            raw_body_utf8=request.content.decode(errors='replace'),body_sha256=digest),'http_wire.jsonl')
        record(dict(kind='request_sent',request_id=identity,url=str(request.url),
            body_sha256=digest,meaning='transport dispatch attempt, not a server acceptance acknowledgement'),
            'http_lifecycle.jsonl')
        try:
            if not isinstance(body,dict):raise ValueError('Model payload must be JSON object')
            if request.url.host not in ('127.0.0.1','localhost') or body.get('stream'):
                raise ValueError('Require local nonstreaming model route')
            response=await original(client,request,**kwargs)
            raw=await response.aread()
            try:value=json.loads(raw)
            except ValueError:value=dict(non_json=raw.decode(errors='replace'))
            usage=value.get('usage')
            record(dict(kind='http_response',request_id=identity,status=response.status_code,
                elapsed_seconds=time.monotonic()-started,body=value,raw_body_utf8=raw.decode(errors='replace')),
                'http_wire.jsonl')
            status='response_received'
            record(dict(kind=status,request_id=identity,http_status=response.status_code,
                usage=usage),'http_lifecycle.jsonl')
            return response
        except asyncio.CancelledError:
            status='cancelled'
            record(dict(kind=status,request_id=identity,error_type='CancelledError',
                response_object_received=response is not None),'http_lifecycle.jsonl')
            raise
        except (TimeoutError,httpx.TimeoutException) as exc:
            status='timeout'
            record(dict(kind=status,request_id=identity,error_type=type(exc).__name__,
                error=str(exc)),'http_lifecycle.jsonl')
            raise
        except BaseException as exc:
            status='transport_error'
            record(dict(kind=status,request_id=identity,error_type=type(exc).__name__,
                error=str(exc)),'http_lifecycle.jsonl')
            raise
        finally:
            valid_usage=isinstance(usage,dict) and all(type(usage.get(k)) is int and usage[k]>=0
                for k in ('prompt_tokens','completion_tokens','total_tokens'))
            record(dict(kind='terminal_status',request_id=identity,status=status,
                elapsed_seconds=time.monotonic()-started,usage=usage,
                usage_observed=usage is not None,partial_usage=status!='response_received' or not valid_usage),
                'http_lifecycle.jsonl')
            if persistence_errors and status=='response_received':
                raise OSError('HTTP evidence persistence failed: '+persistence_errors[-1])

    with patch('httpx.AsyncClient.send',send):
        yield


def audit_requests(directory,*,deadline_evidence=None):
    """A cancel is explainable only with independently recorded official cutoff."""
    directory=Path(directory)
    raw=read_events(directory/'http_wire.jsonl')
    life=read_events(directory/'http_lifecycle.jsonl')
    requests=[r for r in raw if r['kind']=='http_request']
    responses=[r for r in raw if r['kind']=='http_response']
    ids=[r.get('request_id') for r in requests]
    reasons=[];rows=[]
    if not requests:reasons.append('no_model_requests')
    if None in ids or len(ids)!=len(set(ids)):reasons.append('missing_or_duplicate_request_id')
    known=set(ids)
    if any(r.get('request_id') not in known for r in life+responses):reasons.append('orphan_event')
    total=dict(prompt_tokens=0,completion_tokens=0,total_tokens=0)
    valid_usage_count=0
    complete=True
    for request in requests:
        identity=request.get('request_id')
        events=[e for e in life if e.get('request_id')==identity]
        starts=[e for e in events if e['kind']=='request_sent']
        terms=[e for e in events if e['kind']=='terminal_status']
        reply=[e for e in responses if e.get('request_id')==identity]
        state=terms[0]['status'] if len(terms)==1 else 'unknown'
        explained=False
        if len(starts)!=1 or len(terms)!=1:reasons.append('missing_or_duplicate_terminal')
        if len([e for e in events if e['kind']==state])!=1:reasons.append('missing_or_duplicate_state_event')
        if terms and starts and terms[0]['recorded_monotonic']<starts[0]['recorded_monotonic']:
            reasons.append('invalid_event_order')
        if len(starts)==1 and starts[0].get('body_sha256')!=request.get('body_sha256'):
            reasons.append('request_identity_drift')
        if state=='cancelled':
            evidence=deadline_evidence or {}
            cancels=[e for e in events if e['kind']=='cancelled' and e.get('error_type')=='CancelledError']
            cutoff=evidence.get('cutoff_monotonic')
            near_cutoff=cutoff is None or bool(len(cancels)==1 and abs(cancels[0]['recorded_monotonic']-cutoff)<=2)
            explained=bool(evidence.get('official_agent_deadline') and evidence.get('cleanup_verified')
                and len(cancels)==1 and near_cutoff
                and not reply and (not terms or terms[0].get('usage') is None))
            if not explained:reasons.append('unexplained_cancellation')
        elif state=='response_received':
            if len(reply)!=1 or reply[0]['status']!=200:reasons.append('missing_or_error_response')
        else:reasons.append('unknown_or_failed_transport')
        usage=reply[0]['body'].get('usage') if len(reply)==1 else None
        valid=bool(isinstance(usage,dict) and all(type(usage.get(k)) is int and usage[k]>=0 for k in total))
        if state=='response_received' and not valid:reasons.append('missing_response_usage')
        if valid:
            valid_usage_count+=1
            for key in total:total[key]+=usage[key]
        else:complete=False
        if state!='response_received':complete=False
        rows.append(dict(request_id=identity,terminal_status=state,
            explained_cancellation=explained,usage=usage,usage_complete=valid and state=='response_received'))
    return dict(passed=not reasons,reasons=sorted(set(reasons)),requests=len(requests),
        responses=len(responses),rows=rows,observed_response_usage=total if valid_usage_count else None,
        usage_complete=complete,partial_token_usage=not complete,
        scope='Received response usage only. Cancelled/unknown usage is absent, never zero imputed.')
