"""Passive evidence validation; unknown usage is never zero-imputed."""
import hashlib,json
from pathlib import Path

def finalize(directory):
    root=Path(directory);missing=[]
    def read(name,lines=False):
        try:
            raw=(root/name).read_bytes()
            return [json.loads(l) for l in raw.splitlines()] if lines else json.loads(raw)
        except (OSError,ValueError):missing.append(name);return [] if lines else {}
    row=read('SESSION_RESULT.json');config=read('CONFIGURATION.json');agent=read('AGENT_RESULT.json');cleanup=read('AGENT_CLEANUP.json');done=read('worker_done.json')
    trace=read('native_trace.json');events=read('events.jsonl',True)
    wire=read('model_transport/http_wire.jsonl',True);life=read('model_transport/http_lifecycle.jsonl',True)
    if row.get('charged_tools',0)>0:read('adk_events.jsonl',True)
    requests=[r for r in wire if r['kind']=='http_request'];terminals=[r for r in life if r['kind']=='terminal_status']
    ids=[r['request_id'] for r in requests]
    if not ids or len(ids)!=len(set(ids)) or len(ids)!=len(terminals) or set(ids)!={r['request_id'] for r in terminals}:missing.append('HTTP_REQUEST_TERMINAL_PAIRING')
    calls=[];invalid=[]
    for request in requests:
        schemas={t['function']['name']:t['function'].get('parameters',{}) for t in request['body'].get('tools',[])}
        for response in [r for r in wire if r['kind']=='http_response' and r['request_id']==request['request_id']]:
            for choice in response['body'].get('choices',[]):
                for call in choice.get('message',{}).get('tool_calls',[]):
                    f=call['function'];calls.append(f['name'])
                    try:args=json.loads(f['arguments']);absent=sorted(set(schemas.get(f['name'],{}).get('required',[]))-set(args))
                    except (ValueError,TypeError):absent=['INVALID_JSON_ARGUMENTS']
                    if absent:invalid.append(dict(tool=f['name'],missing=absent))
    edit=next((r for r in events if r['kind']=='first_production_edit_observed'),None)
    start=next((r['recorded_monotonic'] for r in events if r.get('agent_started')),None)
    interval=None if edit is None or start is None else dict(lower_seconds=edit['lower_bound_monotonic']-start,upper_seconds=edit['observed_monotonic']-start,files=edit['changed_files'])
    if interval is not None and (interval['lower_seconds']<0 or interval['upper_seconds']<interval['lower_seconds']):missing.append('INVALID_FIRST_EDIT_INTERVAL')
    patch=root/('submitted.patch' if row.get('patch_submitted') else 'fallback.patch')
    if not patch.is_file():missing.append('RETAINED_PATCH_FILE')
    else:
        raw=patch.read_bytes()
        if len(raw)!=row.get('patch_bytes') or (hashlib.sha256(raw).hexdigest() if raw else None)!=row.get('patch_sha256'):missing.append('PATCH_IDENTITY')
    if not cleanup.get('complete') or not cleanup.get('leases_removed') or not done.get('cleanup_complete'):missing.append('CLEANUP_RECEIPTS')
    valid_usage=[r['usage'] for r in terminals if isinstance(r.get('usage'),dict) and all(type(r['usage'].get(k)) is int for k in ('prompt_tokens','completion_tokens','total_tokens'))]
    observed=None if not valid_usage else {k:sum(r[k] for r in valid_usage) for k in ('prompt_tokens','completion_tokens','total_tokens')}
    metrics=dict(evidence_complete=not missing,missing=missing,attempted_calls=len(calls),charged_calls=row.get('charged_tools'),invalid_calls=invalid,first_production_edit=interval,first_edit_missing_reason=None if interval else 'NO_PRODUCTION_EDIT_OBSERVED',observed_usage=observed,usage_complete=len(valid_usage)==len(terminals) and bool(terminals),usage_missing_is_zero=False)
    (root/'R12_METRICS.json').write_text(json.dumps(metrics,indent=2)+'\n')
    row.update(evidence_complete=not missing,metrics=metrics)
    (root/'SESSION_RESULT.json').write_text(json.dumps(row,indent=2)+'\n')
    return metrics
