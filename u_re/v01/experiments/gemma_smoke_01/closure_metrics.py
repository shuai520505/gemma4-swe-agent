"""Read real event evidence; no intervention in submit_patch or model stopping."""
import json
from pathlib import Path

def rows(path):
    if not Path(path).is_file():return []
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]

def summarize(directory):
    d=Path(directory);native=rows(d/'events.jsonl');events=[]
    for row in rows(d/'adk_events.jsonl'):
        for part in row.get('event',{}).get('content',{}).get('parts',[]):
            for key in ('function_call','function_response'):
                if part.get(key):events.append(dict(kind=key,time=row.get('recorded_monotonic'),**part[key]))
    responses=[e for e in events if e['kind']=='function_response' and e.get('name')=='submit_patch']
    successful=[e for e in responses if e.get('response',{}).get('status')=='ok']
    starts=[e['recorded_monotonic'] for e in native if e.get('stage')=='agent' and e.get('agent_started')]
    ends=[e['recorded_monotonic'] for e in native if e.get('stage')=='save_patch' and 'agent_elapsed_seconds' in e]
    first=successful[0] if successful else None
    after=[e for e in events[events.index(first)+1:] if e['kind']=='function_call'] if first else []
    patches=[e for e in native if e.get('kind')=='patch' and (not ends or e['recorded_monotonic']<=ends[0])]
    boundary=json.loads((d/'agent_boundary.json').read_text(encoding='utf-8')) if (d/'agent_boundary.json').is_file() else {}
    return dict(successful_submit_calls=len(successful),submit_attempts=len(responses),
        successful_resubmissions=max(0,len(successful)-1),tools_after_first_successful_submit=len(after),
        first_successful_submit_seconds=first['time']-starts[0] if first and starts and first['time'] is not None else None,
        continued_seconds_after_submit=ends[0]-first['time'] if first and ends and first['time'] is not None else None,
        last_checkpoint_before_agent_end=patches[-1] if patches else None,raw_agent_boundary=boundary,
        caveat='A successful submit is not termination or proof of correctness. Multiple success calls are not automatically byte-identical patches.')
