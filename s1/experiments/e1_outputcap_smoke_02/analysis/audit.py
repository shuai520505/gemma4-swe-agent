"""Post-execution evidence extraction, never imported by GPU/Agent runtime."""
import csv
import io
import json
from pathlib import Path
import re
import zipfile

from experiments.prepare import write_new
from harness_v2.evidence import read_events
from s1.collect import verify_zip
from s1.util import save, sha

HERE=Path(__file__).resolve().parents[1]


def main():
    directory=HERE/'results/gpu'
    output=HERE/'analysis/final'
    archive=(directory/'raw.zip').read_bytes()
    integrity=verify_zip(archive)
    protocol=json.loads((HERE/'protocol.json').read_text())
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for name,digest in protocol['source_hashes'].items():
            assert sha(z.read('source/'+name))==digest,name
        assert sha(z.read('source/s1/gpu_protocol.json'))==sha((HERE/'protocol.json').read_bytes())
        assert sha(z.read('source/s1/cpu_gate.json'))==protocol['cpu_gate_sha256']
        assert json.loads(z.read('wheel_hashes.json'))==protocol['wheel_hashes']
        if 'model_identity.json' in z.namelist():
            assert json.loads(z.read('model_identity.json'))['files']==protocol['model_files']
    save(output/'integrity.json',dict(**integrity,source_files_checked=len(protocol['source_hashes']),
        registered_protocol_unchanged=True,CPU_gate_unchanged=True))
    records=json.loads((directory/'records.json').read_text()) if (directory/'records.json').exists() else []
    rows=[]
    for scheduled in protocol['batches']['smoke']:
        existing=next((r for r in records if r['index']==scheduled['index']),None)
        if existing is None:
            rows.append(dict(**scheduled,status='not_run',metrics=None));continue
        assert all(existing[k]==scheduled[k] for k in ('arm','instance_id'))
        d=directory/'runs'/f"{scheduled['index']:02d}-{scheduled['instance_id']}-{scheduled['arm']}"
        events=read_events(d/'events.jsonl')
        adk=read_events(d/'adk_events.jsonl')
        calls=[];responses=[]
        origin=next((e['recorded_monotonic'] for e in events if e['kind']=='stage' and e.get('agent_started')),None)
        for e in adk:
            for part in ((e.get('event') or {}).get('content') or {}).get('parts',[]):
                if part.get('function_call'):
                    calls.append(dict(index=len(calls)+1,time=e['recorded_monotonic'],**part['function_call']))
                if part.get('function_response'):
                    responses.append(dict(time=e['recorded_monotonic'],**part['function_response']))
        unmatched=list(responses);timeline=[]
        for call in calls:
            match=next((r for r in unmatched if r.get('id') and r.get('id')==call.get('id')),None)
            if match is None:
                match=next((r for r in unmatched if r.get('name')==call.get('name') and r['time']>=call['time']),None)
            if match is not None:unmatched.remove(match)
            timeline.append(dict(**call,seconds_since_agent=call['time']-origin if origin else None,
                response_seconds_since_agent=match['time']-origin if origin and match else None,
                response=match.get('response') if match else None,
                effective_edit='manual content review required' if call['name'] in ('edit_file','write_file') else None))
        save(output/(scheduled['arm']+'-tools.json'),timeline)
        csv_out=io.StringIO(newline='')
        writer=csv.writer(csv_out)
        writer.writerow(['index','call_seconds','result_seconds','tool','args','response'])
        for t in timeline:
            writer.writerow([t['index'],t['seconds_since_agent'],t['response_seconds_since_agent'],
                t['name'],json.dumps(t.get('args'),ensure_ascii=False),json.dumps(t.get('response'),ensure_ascii=False)])
        write_new(output/(scheduled['arm']+'-tools.csv'),csv_out.getvalue().encode())
        wire=read_events(d/'http_wire.jsonl')
        reqs=[e for e in wire if e['kind']=='http_request']
        resps=[e for e in wire if e['kind']=='http_response']
        generation=[]
        for i,req in enumerate(reqs,1):
            res=resps[i-1] if i<=len(resps) else None
            b=req['body'];r=res['body'] if res else {}
            generation.append(dict(index=i,input_tokens=r.get('usage',{}).get('prompt_tokens'),
                output_tokens=r.get('usage',{}).get('completion_tokens'),total_tokens=r.get('usage',{}).get('total_tokens'),
                elapsed_seconds=res['elapsed_seconds'] if res else None,
                response_observed=res is not None,
                finish_reasons=[c.get('finish_reason') for c in r.get('choices',[])],
                max_output_tokens=b.get('max_completion_tokens',b.get('max_tokens')),
                seed=b.get('seed'),thinking=b.get('thinking_token_budget'),
                chat_template_kwargs=b.get('chat_template_kwargs'),
                message_roles=[m['role'] for m in b.get('messages',[])],
                reasoning_messages=sum(bool(m.get('reasoning_content')) for m in b.get('messages',[])),
                tool_messages=sum(m.get('role')=='tool' for m in b.get('messages',[]))))
        save(output/(scheduled['arm']+'-requests.json'),generation)
        audit=existing['audit']
        patch=(d/'latest.patch').read_text(encoding='utf-8') if (d/'latest.patch').exists() else ''
        changed=re.findall(r'^diff --git a/(.*?) b/(.*?)$',patch,re.M)
        admissions=[e for e in events if e['kind']=='context_admission']
        summaries=[e for e in events if e['kind']=='research_parameters' and e.get('uncapped_summary')]
        raw=json.loads((d/'official_result.json').read_text())
        fixture_errors=len(re.findall('ERROR at setup',raw.get('test_output') or ''))
        fixture_environment=bool(fixture_errors and 'recursive dependency involving fixture' in raw.get('test_output',''))
        outcome=dict(audit['outcome'])
        if fixture_environment:
            outcome=dict(status='unknown',failure_stage='verifier_environment',
                reason='Recursive httpbin fixtures prevent attributable repair verdict; raw fields retained')
        effective=[]
        new_files=set(re.findall(r'^\+\+\+ b/(.*?)$',patch,re.M))
        for t in timeline:
            response=t.get('response') or {}
            if t['name']=='edit_file' and response.get('status')=='ok' and response.get('diff'):
                effective.append(t)
            elif t['name']=='write_file' and response.get('status')=='ok' and response.get('size',0)>0 and response.get('filepath') in new_files:
                effective.append(t)
        production=[t for t in effective if (t.get('args') or {}).get('filepath','').startswith('src/')]
        metrics=dict(HTTP_requests=audit['HTTP_requests'],HTTP_responses=len(resps),
            unmatched_requests=len(reqs)-len(resps),official_LLM_calls=audit['official_LLM_calls'],
            observed_response_usage=audit['usage'],usage_complete=len(reqs)==len(resps),
            usage_scope='Only received responses; cancellation output unknown. Do not treat as complete total.',
            agent_seconds=audit['agent_seconds'],worker_seconds=audit['worker_seconds'],
            tools=audit['native_tool_events'],
            first_effective_edit_seconds=effective[0]['response_seconds_since_agent'] if effective else None,
            first_production_edit_seconds=production[0]['response_seconds_since_agent'] if production else None,
            first_effective_edit_status='Successful result plus nonempty edit diff or final Patch file; manually audited calls 9 and 20',
            edit_attempts=sum(t['name'] in ('edit_file','write_file') for t in calls),
            changed_files=sorted(set(b for a,b in changed)),patch_bytes=audit['patch_bytes'],
            explicit_submits=audit['explicit_submits'],exact_repeated_reads=audit['exact_repeated_reads'],
            testing_commands=audit['testing_commands'],finish_length=audit['finish_length'],
            uncapped_summary_requests=len(summaries),
            max_input_tokens=max((e.get('input_tokens',0) for e in admissions),default=0),
            min_context_slack=min((e['max_model_len']-e['total_reserved'] for e in admissions if 'total_reserved' in e),default=None),
            context_rejects=sum(e.get('decision')!='allow' for e in admissions),
            phase2_exit=audit['official_test_exit_code'],phase2_completed=audit['phase2'] is not None,
            official_resolved=audit['official_resolved'],infrastructure_passed=audit['infrastructure_passed'],
            fixture_setup_errors=fixture_errors)
        rows.append(dict(**scheduled,status=outcome['status'],outcome=outcome,
            r04_runtime_outcome=audit['outcome'],metrics=metrics,reasons=audit['reasons']))
    save(output/'comparison.json',dict(experiment_id=protocol['experiment_id'],scope='One smoke pair; no rate estimate',rows=rows))
    print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
