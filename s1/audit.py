"""Conservative evidence gate; failure to verify infrastructure stops the series."""
import json
from pathlib import Path
import re
from harness_v2.evidence import read_events
from harness_v2.outcomes import normalize


def inspect_run(directory,config,model_path):
    d=Path(directory)
    def load(n,default=None):
        p=d/n
        return json.loads(p.read_text()) if p.is_file() else default
    raw=load('official_result.json')
    result=load('audit_result.json',{})
    wire=read_events(d/'http_wire.jsonl')
    requests=[e for e in wire if e['kind']=='http_request']
    responses=[e for e in wire if e['kind']=='http_response']
    admits=[e for e in read_events(d/'events.jsonl') if e['kind']=='context_admission']
    allowed=[e for e in admits if e.get('decision')=='allow']
    reasons=[]
    def need(value,reason):
        if not value:reasons.append(reason)
    need(bool(requests) and len(requests)==len(responses),'missing/unmatched HTTP')
    need(len(allowed)==len(requests),'tokenizer/request count mismatch')
    need(all(e.get('decision')=='allow' for e in admits),'context admission failure')
    for i,(req,res) in enumerate(zip(requests,responses)):
        b=req['body'];r=res['body']
        need(res['status']==200,'HTTP error')
        need(b.get('model')==model_path and r.get('model')==model_path,'model routing drift')
        need(b.get('max_completion_tokens',b.get('max_tokens'))==config['output_tokens'],'output cap drift')
        need(b.get('seed')==config['seed'],'seed drift')
        need(b.get('chat_template_kwargs',{}).get('enable_thinking')==(config['thinking_budget']>0),'thinking drift')
        need(b.get('thinking_token_budget',0)==config['thinking_budget'],'thinking budget drift')
        if i<len(allowed):
            need(r.get('usage',{}).get('prompt_tokens')==allowed[i]['input_tokens'],'tokenizer/usage mismatch')
        # No sampling defaults were deliberately introduced into either arm.
        need(b.get('temperature') is None and b.get('top_p') is None and b.get('top_k') is None,'sampling default drift')
    tools=[]
    for e in read_events(d/'adk_events.jsonl'):
        event=e.get('event',{})
        for p in (event.get('content') or {}).get('parts',[]):
            if p.get('function_call'):
                tools.append(dict(time=e['recorded_monotonic'],**p['function_call']))
    leakage=[]
    for t in tools:
        args=json.dumps(t.get('args') or {})
        if re.search(r'/kaggle/input|tasks\.jsonl|/source/|test_patch|gold.patch|evaluation-references',args,re.I):
            leakage.append(t)
    need(not leakage,'possible host/evaluation data access')
    need(raw is not None,'official result missing')
    need(result.get('allow_next_run') and result.get('process_tree_stopped') and result.get('cleanup_complete'),'cleanup/controller failure')
    need((d/'agent_boundary_trace.json').is_file() and (d/'official_trace.json').is_file(),'native Trace missing')
    need((d/'latest.patch').is_file(),'Patch checkpoint missing')
    phase2=load('phase2_execution.json')
    need(phase2 is not None,'Phase2 not completed')
    need(bool(raw and raw.get('agent_patch')),'empty Patch; no complete infrastructure gate')
    outcome=normalize(raw,started=True)
    # Collection may reflect external dependencies, not a code repair verdict.
    # Preserve raw exit2; require separate audit rather than attributing it here.
    if outcome.get('failure_stage')=='test_collection':
        outcome=dict(status='unknown',failure_stage='test_collection',reason='collection_requires_environment_audit')
    need(outcome['status'] in ('resolved','failed'),'unconfirmed repair verdict')
    total=dict(prompt_tokens=0,completion_tokens=0,total_tokens=0)
    usage_complete=True
    for e in responses:
        u=e['body'].get('usage') or {}
        for k in total:
            if type(u.get(k)) is not int:usage_complete=False
            else:total[k]+=u[k]
    starts=[e for e in read_events(d/'events.jsonl') if e['kind']=='stage' and e.get('agent_started')]
    edits=[t for t in tools if t['name'] in ('edit_file','write_file')]
    testing=[t for t in tools if t['name']=='run_command' and re.search(r'pytest|unittest|python.*-c|python.*\.py',str(t.get('args')))]
    # Exact repeats only; semantic redundancy needs manual review.
    reads=[json.dumps(t.get('args'),sort_keys=True) for t in tools if t['name']=='read_file']
    return dict(infrastructure_passed=not reasons,reasons=sorted(set(reasons)),outcome=outcome,
        official_resolved=(raw or {}).get('resolved'),official_test_exit_code=(raw or {}).get('test_exit_code'),
        HTTP_requests=len(requests),official_LLM_calls=(raw or {}).get('total_llm_calls'),
        official_tool_calls=(raw or {}).get('tool_calls'),native_tool_events=len(tools),
        usage=total if usage_complete else None,usage_scope='all observed HTTP responses including compaction',
        finish_length=sum(c.get('finish_reason')=='length' for e in responses for c in e['body'].get('choices',[])),
        agent_seconds=load('progress.json',{}).get('agent_elapsed_seconds'),worker_seconds=result.get('duration_seconds'),
        first_edit_action_seconds=(edits[0]['time']-starts[0]['recorded_monotonic']) if edits and starts else None,
        first_effective_edit_seconds=None,first_effective_edit_scope='Not inferred from a tool name; requires content review',
        exact_repeated_reads=len(reads)-len(set(reads)),testing_commands=len(testing),
        explicit_submits=sum(t['name']=='submit_patch' for t in tools),
        leakage_findings=leakage,tools=tools,patch_bytes=(d/'latest.patch').stat().st_size if (d/'latest.patch').exists() else None,
        phase2=phase2,raw_fields_preserved=True)
