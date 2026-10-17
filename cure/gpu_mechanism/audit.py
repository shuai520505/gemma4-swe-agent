"""Infrastructure admission is independent of resolved and CURE self-report."""
import json
from pathlib import Path
from harness_v2.evidence import read_events


def inspect_run(directory, model_path):
    d = Path(directory)
    load = lambda n: json.loads((d/n).read_text()) if (d/n).exists() else None
    official, controller = load('official_result.json'), load('audit_result.json')
    events = read_events(d/'events.jsonl')
    admission = [e for e in events if e.get('kind') == 'context_admission']
    wire = read_events(d/'http_wire.jsonl')
    requests = [e['body'] for e in wire if e['kind'] == 'http_request']
    responses = [e for e in wire if e['kind'] == 'http_response']
    checks = dict(controller_ok=bool(controller and controller.get('allow_next_run')),
        official_result=official is not None, requests_present=bool(requests),
        native_trace=(d/'official_trace.json').is_file(),
        agent_boundary_trace=(d/'agent_boundary_trace.json').is_file(),
        patch_checkpoint=(d/'latest.patch').is_file(),
        phase2=(d/'phase2_execution.json').is_file(),
        context_allowed=bool(admission) and all(e['decision']=='allow' and e['total_reserved']<=32768 for e in admission),
        request_count_matches=len(requests)==len(responses)==len(admission),
        requests_registered=bool(requests) and all(
            r['model']==model_path and r.get('max_completion_tokens',r.get('max_tokens'))==8192
            and r.get('seed')==17 and r.get('thinking_token_budget')==4096
            and r.get('chat_template_kwargs',{}).get('enable_thinking') is True
            and r.get('temperature')==.2 and r.get('top_p')==.95 and r.get('top_k')==40
            for r in requests),
        responses_ok=bool(responses) and all(r['status']==200 and r['body'].get('model')==model_path for r in responses))
    checks['tokenizer_matches_inference'] = bool(responses) and len(responses)==len(admission) and all(
        r['body'].get('usage',{}).get('prompt_tokens')==a['input_tokens'] for r,a in zip(responses,admission))
    phase2 = load('phase2_execution.json')
    checks['real_phase2_tests'] = bool(phase2 and phase2['exit_code'] in (0,1) and
        any(s in phase2['stdout'] for s in (' passed',' failed')))
    # Actual action records; do not infer success from a CURE decision_changed field.
    sequence = []
    seen = set()
    for row in read_events(d/'adk_events.jsonl'):
        e = row['event']
        if e.get('partial'): continue
        for part in (e.get('content') or {}).get('parts',[]):
            for kind in ('function_call','function_response'):
                if kind in part:
                    item = part[kind]
                    key = (e.get('id'), kind, json.dumps(item,sort_keys=True))
                    if key in seen: continue
                    seen.add(key)
                    sequence.append(dict(index=len(sequence)+1,monotonic=row['recorded_monotonic'],
                        event_id=e.get('id'),kind=kind,**item))
    usage = [r['body'].get('usage',{}) for r in responses]
    result = dict(infrastructure_passed=all(checks.values()), checks=checks,
        official=official, controller=controller,
        model_requests=len(requests), http_responses=len(responses),
        usage=dict(prompt_tokens=sum(u.get('prompt_tokens',0) for u in usage),
            completion_tokens=sum(u.get('completion_tokens',0) for u in usage),
            total_tokens=sum(u.get('total_tokens',0) for u in usage)),
        tool_sequence=sequence, tool_calls=sum(x['kind']=='function_call' for x in sequence),
        caveat='HTTP usage is actual server usage; no estimated token substitution. CURE declarations are not causal evidence.')
    return result
