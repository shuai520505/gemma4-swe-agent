"""Postprocess actual study02 evidence; declarations alone are never mechanism proof."""
import hashlib
import json
from pathlib import Path
import re
import zipfile
from cure.build import write_new
from harness_v2.evidence import read_events
from cure.gpu_mechanism.timeline import export

def analyze():
    repo=Path(__file__).resolve().parents[2];study=repo/'cure/gpu-study-02-c1'
    plan=json.loads((study/'protocol.json').read_text(encoding='utf-8'))
    base=study/'results/smoke'
    gate=json.loads((base/'batch_gate.json').read_text(encoding='utf-8'))
    output=[]
    for row in plan['batches']['smoke']:
        d=base/'runs'/f"{row['index']:02d}-{row['task_id']}-{row['arm']}"
        if not d.exists():
            output.append(dict(**row,status='not_run',reason=gate['stop_reason']));continue
        audit=json.loads((d/'mechanism_audit.json').read_text(encoding='utf-8'))
        official=audit['official'] or {};controller=audit['controller'] or {}
        stages=read_events(d/'events.jsonl')
        agent_seconds=next((e['agent_elapsed_seconds'] for e in stages if 'agent_elapsed_seconds' in e),None)
        wire=read_events(d/'http_wire.jsonl')
        requests=[x['body'] for x in wire if x['kind']=='http_request']
        responses=[x['body'] for x in wire if x['kind']=='http_response']
        prompt=(repo/'cure/candidates'/row['arm']/'prompts/system.md').read_text(encoding='utf-8')
        task=json.loads((study/'data/tasks.jsonl').read_text(encoding='utf-8'))
        claims=[]
        for i,r in enumerate(responses):
            for choice in r.get('choices',[]):
                text=choice.get('message',{}).get('content') or ''
                for match in re.finditer(r'<cure>(.*?)</cure>',text,re.S):
                    raw=match.group(1)
                    try: parsed=json.loads(raw);valid=isinstance(parsed,dict)
                    except ValueError: parsed=None;valid=False
                    claims.append(dict(request=i+1,valid_JSON_object=valid,parsed=parsed,raw=raw,
                        provenance='server_visible_content_model_self_report_not_verdict'))
        def contains(r,needle,role):
            return any(isinstance(m.get('content'),str) and needle in m['content'] for m in r['messages'] if m['role']==role)
        assert all(contains(r,task['problem_statement'],'user') for r in requests)
        assert not any('def test_new_entry' in str(r) or 'def test_preserved_entry' in str(r) for r in requests)
        first_prompt=requests and contains(requests[0],prompt.strip(),'system')
        observations=read_events(d/'contract_observations.jsonl')
        phase2=json.loads((d/'phase2_execution.json').read_text()) if (d/'phase2_execution.json').is_file() else None
        result=dict(index=row['index'],arm=row['arm'],status=controller.get('status','unknown'),official_resolved=official.get('resolved'),
            official_error=official.get('error_message'),test_exit_code=official.get('test_exit_code'),
            official_llm_calls=official.get('total_llm_calls'),actual_http_calls=audit['model_requests'],
            official_tool_calls=official.get('tool_calls'),observed_tool_calls_including_submit=audit['tool_calls'],
            official_total_tokens=official.get('total_tokens'),actual_server_usage=audit['usage'],
            agent_seconds=agent_seconds,official_seconds=official.get('duration_seconds'),worker_seconds=controller.get('duration_seconds'),
            patch_bytes=(d/'latest.patch').stat().st_size if (d/'latest.patch').exists() else None,
            phase2=phase2,process_tree_stopped=controller.get('process_tree_stopped'),cleanup_complete=controller.get('cleanup_complete'),
            infrastructure_passed=audit['infrastructure_passed'],full_Prompt_in_first_system=bool(first_prompt),
            observer_claims=[x for x in observations if x['kind']=='model_contract_claim'],visible_claims=claims,
            reasoning_responses=sum(bool(c.get('message',{}).get('reasoning')) for r in responses for c in r.get('choices',[])),
            retained_reasoning_requests=sum(any(m.get('reasoning_content') for m in r['messages'] if m.get('role')=='assistant') for r in requests),
            finish_reasons=[c['finish_reason'] for r in responses for c in r.get('choices',[])])
        output.append(result)
    delta=None
    if len(output)==2 and all('actual_server_usage' in x and x['actual_http_calls']>0 for x in output):
        b,c=output
        delta={key:c[key]-b[key] for key in ('actual_http_calls','official_tool_calls','observed_tool_calls_including_submit','agent_seconds','worker_seconds')}
        delta['tokens']={k:c['actual_server_usage'][k]-b['actual_server_usage'][k] for k in b['actual_server_usage']}
        delta['complete_infrastructure_pair']=gate['infrastructure_passed']
    result=dict(experiment_id=plan['experiment_id'],exploratory_prior_exposure=True,infrastructure_pair_passed=gate['infrastructure_passed'],
        stop_reason=gate['stop_reason'],runs=output,C1_minus_B=delta,
        A_compatibility='real_GPU_requests_observed' if len(output)>1 and output[1].get('actual_http_calls',0)>0 else 'not_confirmed',
        B_mechanism='requires_independent_native_tool_and_claim_audit_not_self_report',
        C_repair_rate='not_supported_by_one_exposed_synthetic_pair',kaggle_resolution_rate=None,formal_submission=False)
    write_new(study/'summary.json',(json.dumps(result,indent=2)+'\n').encode())
    export(study)
    print(json.dumps(result,indent=2))

if __name__=='__main__':analyze()
