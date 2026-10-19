"""Evidence accounting only; never choose actions or infer success from prose."""
from pathlib import Path
from harness_v2.evidence import read_events


def inspect_nested(directory):
    directory=Path(directory);rows=read_events(directory/'nested_audit.jsonl')
    pending={};delegations=[];effects=[];overlap=False;active=0
    for e in rows:
        if e['kind']=='tool_start':
            key=(e['actor'],e['call_id'])
            if key in pending:overlap=True
            pending[key]=e
            if e['actor']=='main_coding_agent' and e['tool']=='egv_verifier':
                active+=1;overlap=overlap or active>1
        if e['kind']=='tool_end':
            key=(e['actor'],e['call_id']);start=pending.pop(key,None)
            if not start:continue
            changes={name:dict(before=start['files'].get(name),after=e['files'].get(name))
                     for name in set(start['files'])|set(e['files']) if start['files'].get(name)!=e['files'].get(name)}
            if e['actor']=='egv_verifier' and changes:
                effects.append(dict(call_id=e['call_id'],tool=e['tool'],changes=changes))
            if e['actor']=='main_coding_agent' and e['tool']=='egv_verifier':
                active-=1
                delegation=dict(call_id=e['call_id'],caller=e['actor'],callee='egv_verifier',
                    arguments=e['args'],returned_result=e['result'],start=start['monotonic'],end=e['monotonic'],
                    seconds=e['monotonic']-start['monotonic'],counted_tools_delta=e['counted_tools']-start['counted_tools'],
                    child_model_calls=sum(x['kind']=='model_start' and x['actor']=='egv_verifier'
                        and start['monotonic']<=x['monotonic']<=e['monotonic'] for x in rows),
                    child_tool_calls=sum(x['kind']=='tool_start' and x['actor']=='egv_verifier'
                        and start['monotonic']<=x['monotonic']<=e['monotonic'] for x in rows),
                    workspace_changes=changes)
                delegations.append(delegation)
    wire=read_events(directory/'http_wire.jsonl')
    life=read_events(directory/'http_lifecycle.jsonl')
    for d in delegations:
        requests=[r for r in wire if r['kind']=='http_request' and d['start']<=r['recorded_monotonic']<=d['end']]
        ids={r['request_id'] for r in requests};terminal=[r for r in life if r['kind']=='terminal_status' and r['request_id'] in ids]
        usage=[r['usage'] for r in terminal if isinstance(r.get('usage'),dict)]
        d.update(HTTP_dispatches=len(requests),request_ids=sorted(ids),
            observed_usage={k:sum(u[k] for u in usage if type(u.get(k)) is int)
                if any(type(u.get(k)) is int for u in usage) else None
                for k in ('prompt_tokens','completion_tokens','total_tokens')},
            usage_complete=bool(requests) and len(usage)==len(requests)
                and all(not r['partial_usage'] for r in terminal))
    return dict(observed=bool(rows),delegations=delegations,child_workspace_side_effects=effects,
        concurrent_or_ambiguous_delegation=overlap,
        incomplete_tools=[dict(actor=e['actor'],tool=e['tool'],call_id=e['call_id']) for e in pending.values()],
        actual_tool_start_events=sum(e['kind']=='tool_start' for e in rows),
        model_start_events_by_role={a:sum(e['kind']=='model_start' and e['actor']==a for e in rows)
                                    for a in sorted({e.get('actor') for e in rows if e.get('actor')})},
        scope='Usage is received-only; no success or counterevidence validity inferred from report text. Non-overlap required for request-to-delegation time joins.')
