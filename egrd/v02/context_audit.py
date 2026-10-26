"""Reconstruct PR33's archived requests without a model/tokenizer/network call.

Public outputs contain counts, hashes, event references and derived labels only.
No request, Issue, source excerpt, reasoning, test or patch text is exported.
Component token counts stay unknown: the exact tokenizer/template files are not
available locally. Canonical JSON character counts are deliberately not tokens.
"""
import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ARCHIVE_REL='meer_v01_authorized02/batch02/read-03/evidence_confirmed/output/meer-v01-gpu-batch2.zip'
EXPECTED_ARCHIVE='90226b7ce83979a40890434b8a0c626be440e84a00da927b16d88e4d70b811d3'
POLICIES=(16384,12288,8192)


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()


def sha(raw):return hashlib.sha256(raw).hexdigest()


def admission(tokens,output,context=32768,safety=1024):
    if type(tokens) is not int or tokens<0 or type(output) is not int or output<=0:
        raise ValueError('Invalid token observation')
    cap=context-output-safety
    return dict(output_reservation=output,input_allowance=cap,admitted=tokens<=cap,
                input_headroom=cap-tokens,total_reserved=tokens+output+safety)


def rows(raw):
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def common_prefix(left,right):
    count=0
    for a,b in zip(left,right):
        if a!=b:break
        count+=1
    return count


def message_sizes(messages):
    out={}
    for role in ('system','developer','user','assistant','tool'):
        selected=[m for m in messages if m.get('role')==role]
        out[role]=dict(messages=len(selected),canonical_JSON_chars=sum(len(canonical(m).decode()) for m in selected),
                       canonical_JSON_bytes=sum(len(canonical(m)) for m in selected),tokens=None)
    return out


def actions(events):
    calls=[];responses={}
    for i,row in enumerate(events):
        for part in row.get('event',{}).get('content',{}).get('parts',[]):
            if part.get('function_call'):
                calls.append(dict(part['function_call'],event_index=i,monotonic=row['recorded_monotonic']))
            if part.get('function_response'):
                response=part['function_response']
                responses[response.get('id')]=dict(response,event_index=i,monotonic=row['recorded_monotonic'])
    return [(c,responses.get(c.get('id'))) for c in calls]


def analyze(archive):
    archive=Path(archive);raw=archive.read_bytes();assert sha(raw)==EXPECTED_ARCHIVE
    requests_out=[];rejects_out=[];sessions=[];shadow=[];action_out=[];source_members={}
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        prefixes=sorted(n.removesuffix('agent/http_wire.jsonl') for n in z.namelist()
                        if n.startswith('execution/runs/') and n.endswith('agent/http_wire.jsonl'))
        assert len(prefixes)==3
        for prefix in prefixes:
            session=prefix.rstrip('/').rsplit('/',1)[-1];arm=session[-1]
            wire=rows(z.read(prefix+'agent/http_wire.jsonl'))
            events=rows(z.read(prefix+'agent/adk_events.jsonl'))
            journal=rows(z.read(prefix+'events.jsonl'));agent_journal=rows(z.read(prefix+'agent/events.jsonl'))
            admissions=[(i,r) for i,r in enumerate(journal) if r.get('kind')=='context_admission']
            parameters=[r for r in journal if r.get('kind')=='research_parameters']
            assert len(parameters)==len(admissions)
            assert all(r.get('uncapped_summary') is False and r.get('output_tokens')==16384
                       and r.get('thinking_budget')==4096 and r.get('seed')==17 for r in parameters)
            allowed=[r for _,r in admissions if r.get('decision')=='allow']
            rejected=[(i,r) for i,r in admissions if r.get('decision')=='reject']
            requests=[(i,r) for i,r in enumerate(wire) if r.get('kind')=='http_request']
            responses={r['request_id']:(i,r) for i,r in enumerate(wire) if r.get('kind')=='http_response'}
            assert len(allowed)==len(requests) and len(rejected)==1
            start=next(r['recorded_monotonic'] for r in agent_journal if r.get('agent_started'))
            source=[r for r in agent_journal if r.get('kind')=='source_boundary_observation'
                    and r.get('before') and r.get('start_monotonic',-1)>=start]
            assert source and not any(r.get('production_changed') for r in source)
            source_identity=sha(canonical(source[0]['before']))
            paired=actions(events);covered=defaultdict(set);read_summaries=[];scratch={};versions=[]
            for call,response in paired:
                args=call.get('args',{});result=(response or {}).get('response',{})
                path=args.get('filepath');before=scratch.get(path)
                if call['name']=='write_file' and result.get('status')=='ok':scratch[path]=args['content']
                if call['name']=='edit_file' and result.get('status')=='ok' and before is not None:
                    old=args['old_string'];new=args['new_string']
                    assert before.count(old)==result.get('occurrences',1)
                    scratch[path]=before.replace(old,new)
                classification='source_read' if call['name']=='read_file' else 'search_or_command'
                diagnostic_asserts=None;scratch_sha=None
                if call['name']=='run_command' and 'python3 reproduce_issue.py'==args.get('command'):
                    text=scratch['reproduce_issue.py'];scratch_sha=sha(text.encode())
                    diagnostic_asserts=sum(isinstance(n,ast.Assert) for n in ast.walk(ast.parse(text)))
                    classification='scratch_diagnostic_execution'
                if call['name'] in ('write_file','edit_file'):
                    classification='scratch_edit_attempt' if path=='reproduce_issue.py' else 'other_edit_attempt'
                if call['name']=='read_file' and result.get('status')=='ok':
                    first=result.get('start_line',1);line_count=len(result.get('content','').splitlines())
                    current=set(range(first,first+line_count));overlap=current&covered[path]
                    covered[path]|=current
                    read_summaries.append(dict(event_index=call['event_index'],path=path,
                        returned_start_line=first,returned_content_lines=line_count,
                        previously_returned_same_path_lines=len(overlap),
                        source_version_basis='Unchanged production hashes; scratch reads separately identified',
                        returned_content_sha256=sha(result.get('content','').encode())))
                action_out.append(dict(session=session,arm=arm,event_index=call['event_index'],
                    call_seconds=call['monotonic']-start,response_event_index=(response or {}).get('event_index'),
                    response_seconds=response['monotonic']-start if response else None,
                    tool=call['name'],classification=classification,path=path,
                    argument_sha256=sha(canonical(args)),result_status=result.get('status'),
                    result_exit_code=result.get('exit_code'),diagnostic_static_assertions=diagnostic_asserts,
                    scratch_sha256=scratch_sha,production_source_sha256=source_identity))
                if response:versions.append((response['monotonic'],dict(scratch)))
            compactions=[i for i,r in enumerate(events) if r.get('event',{}).get('actions',{}).get('compaction')]
            prev=[];previous_input=None;growth_by_tool=Counter()
            issue_sha='204aee6b1a8978fc1b0ce5777b3b116c45cea82d4b6822c5667724ccb6d62960'
            first_user=requests[0][1]['body']['messages'][1]['content']
            issue=first_user.split('Problem Statement:\n',1)[1].split('\n\n## Task Budget',1)[0]
            assert sha(issue.encode())==issue_sha
            for seq,((wire_i,request),guard) in enumerate(zip(requests,allowed),1):
                response_i,response=responses[request['request_id']];body=request['body'];messages=body['messages']
                usage=response['body']['usage'];assert usage['prompt_tokens']==guard['input_tokens']
                assert body['max_completion_tokens']==16384 and response['status']==200
                prefix_count=common_prefix(prev,messages);new=messages[prefix_count:]
                prior=[(c,r) for c,r in paired if r and r['monotonic']<=request['recorded_monotonic']]
                latest=prior[-1] if prior else None
                sizes=message_sizes(messages);new_sizes=message_sizes(new)
                marginal=guard['input_tokens']-previous_input if previous_input is not None else None
                if latest and marginal is not None:growth_by_tool[latest[0]['name']]+=marginal
                fingerprints=[sha(canonical(m)) for m in messages]
                duplicated=sum(n-1 for n in Counter(fingerprints).values() if n>1)
                record=dict(session=session,arm=arm,request_sequence=seq,
                    request_wire_line=wire_i+1,response_wire_line=response_i+1,
                    request_body_sha256=sha(canonical(body)),input_tokens=guard['input_tokens'],
                    original_wire_body_sha256=request.get('body_sha256'),
                    prompt_tokens=usage['prompt_tokens'],completion_tokens=usage['completion_tokens'],
                    total_received_tokens=usage['total_tokens'],output_reservation=body['max_completion_tokens'],
                    guard_decision='allow',actually_sent=True,response_status=response['status'],
                    finish_reasons=[c.get('finish_reason') for c in response['body'].get('choices',[])],
                    seconds_since_Agent_start=request['recorded_monotonic']-start,
                    HTTP_elapsed_seconds=response.get('elapsed_seconds'),message_count=len(messages),
                    tool_schema_names=[t['function']['name'] for t in body.get('tools',[])],
                    tool_schema_canonical_JSON_chars=len(canonical(body.get('tools',[])).decode()),
                    stable_prefix_messages=prefix_count,previous_message_count=len(prev),
                    new_message_roles=[m['role'] for m in new],duplicate_exact_messages_in_request=duplicated,
                    component_sizes=sizes,new_component_sizes=new_sizes,
                    previous_tool_event_index=latest[0]['event_index'] if latest else None,
                    previous_tool=latest[0]['name'] if latest else None,
                    previous_tool_result_source='Actual new tool message; combined marginal also includes assistant/tool/template overhead',
                    marginal_input_tokens=marginal,component_token_counts=None,
                    compaction_event_observed=False,Issue_restored=guard.get('core_restored'),
                    exact_Issue_sha256=issue_sha,
                    original_Issue_chars=len(issue),
                    normal_task_other_content_chars=len(first_user)-len(issue),
                    exact_Issue_occurrences=sum(m.get('content','').count(issue) for m in messages if isinstance(m.get('content'),str)),
                    assistant_reasoning_content_chars=sum(len(m.get('reasoning_content') or '') for m in messages if m.get('role')=='assistant'),
                    assistant_reasoning_field_canonical_chars=sum(len(canonical(m.get('reasoning'))) for m in messages if m.get('role')=='assistant' and m.get('reasoning') is not None),
                    reasoning_rendered_token_contribution=None,
                    production_source_sha256=source_identity,production_edits_before_request=0,
                    reconstructed_scratch_hashes_from_structured_operations={p:sha(text.encode()) for p,text in (next((v for t,v in reversed(versions) if t<=request['recorded_monotonic']),{})).items()},
                    scratch_identity_limit='Reconstructed from successful structured tool operations, not a full filesystem attestation',
                    native_patch_correctness_at_request=None)
                requests_out.append(record)
                for cap in POLICIES:shadow.append(dict(session=session,request_sequence=seq,actually_sent=True,
                    observed_input_tokens=guard['input_tokens'],actual_decision='allow',**admission(guard['input_tokens'],cap)))
                prev=messages;previous_input=guard['input_tokens']
            for line,r in rejected:
                latest=paired[-1][0];growth_by_tool[latest['name']]+=r['input_tokens']-previous_input
                rejection=dict(session=session,arm=arm,guard_journal_line=line+1,
                    input_tokens=r['input_tokens'],output_reservation=r['output_reserved'],safety=r['safety_tokens'],
                    total_reserved=r['total_reserved'],decision='reject',actually_sent=False,
                    seconds_since_Agent_start=r['recorded_monotonic']-start,
                    time_remaining_upper_budget_seconds=300-(r['recorded_monotonic']-start),
                    tool_calls_before_stop=len(paired),tools_remaining=60-len(paired),
                    previous_tool=latest['name'],previous_tool_event_index=latest['event_index'],
                    marginal_input_tokens=r['input_tokens']-previous_input,
                    message_count=None,request_body_sha256=None,component_token_counts=None,
                    Issue_restored=r.get('core_restored'),production_edits=0,
                    unknown='Rejected final request body was not recorded by passive HTTP observer; no future trajectory exists')
                rejects_out.append(rejection)
                for cap in POLICIES:shadow.append(dict(session=session,request_sequence=len(requests)+1,
                    actually_sent=False,observed_input_tokens=r['input_tokens'],actual_decision='reject',**admission(r['input_tokens'],cap)))
            member_hashes={n:sha(z.read(prefix+n)) for n in ('agent/http_wire.jsonl','agent/adk_events.jsonl','events.jsonl','agent/events.jsonl')}
            source_members[session]=dict(prefix=prefix,members=member_hashes)
            sessions.append(dict(session=session,arm=arm,requests=len(requests),compaction_events=compactions,
                Issue_restorations=sum(bool(r.get('core_restored')) for _,r in admissions),
                first_input_tokens=allowed[0]['input_tokens'],last_sent_input_tokens=allowed[-1]['input_tokens'],
                rejected_input_tokens=rejected[0][1]['input_tokens'],initial_to_rejection_growth_tokens=rejected[0][1]['input_tokens']-allowed[0]['input_tokens'],
                marginal_growth_by_previous_tool_turn=dict(growth_by_tool),
                marginal_attribution_warning='Each increment includes assistant generation, tool result and rendering overhead, not isolated tool-result tokens',
                final_sent_message_sizes=message_sizes(prev),read_windows=read_summaries,
                total_returned_read_lines=sum(r['returned_content_lines'] for r in read_summaries),
                repeated_same_path_lines=sum(r['previously_returned_same_path_lines'] for r in read_summaries),
                observed_production_edits=0,Skill_calls=sum(c['name']=='run_skill_script' for c,_ in paired),
                maximum_completion=max(responses[r['request_id']][1]['body']['usage']['completion_tokens'] for _,r in requests),
                role_prefix_history_monotone=all(r['stable_prefix_messages']==r['previous_message_count'] for r in requests_out if r['session']==session)))
    assert len(requests_out)==40 and len(rejects_out)==3
    return dict(schema='EGRD_V02_OFFLINE_CONTEXT_AUDIT',archive_sha256=sha(raw),source_members=source_members,
        unit_warning='Component sizes are canonical JSON characters/bytes, NOT rendered model tokens',
        component_tokenizer_replay='NOT_RUN_EXACT_TOKENIZER_AND_TEMPLATE_UNAVAILABLE',
        completed_requests=requests_out,guard_rejections=rejects_out,sessions=sessions,
        observed_missing_sessions=[dict(run=i,instance_id='fastapi_14297',arm=a,status='NOT_RUN',native_resolved=None) for i,a in enumerate(('A','B','C'),1)],
        actions=action_out,shadow_admissions=shadow,
        shadow_limits='Only archived final token counts are replayed. Lower output caps do not reconstruct new outputs, later requests, edits or Native Resolved.')


def prior_context_comparison():
    """Verify four old native/cost records, not a fresh held-out experiment."""
    spec=json.loads((ROOT/'u_re/v03/experiments/context_budget_01/RAW_ARCHIVES.json').read_bytes())['GPU'][0]
    path=Path(spec['path']);assert sha(path.read_bytes())==spec['sha256']
    result=[]
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        for name in sorted(n for n in z.namelist() if n.endswith('agent/agent_result.json')):
            prefix=name.removesuffix('agent/agent_result.json');agent=json.loads(z.read(name))
            wire=rows(z.read(prefix+'agent/http_wire.jsonl'))
            req=[r for r in wire if r.get('kind')=='http_request']
            resp=[r for r in wire if r.get('kind')=='http_response']
            caps={r['body']['max_completion_tokens'] for r in req};assert len(caps)==1
            guard=[r for r in rows(z.read(prefix+'events.jsonl')) if r.get('kind')=='context_admission' and r.get('decision')=='reject']
            native=z.read(prefix+'official_result.json');usages=[r['body']['usage'] for r in resp if r.get('status')==200]
            result.append(dict(session=prefix.rstrip('/').rsplit('/',1)[-1],
                output_reservation=next(iter(caps)),native_resolved=json.loads(native)['resolved'],
                TaskResult_sha256=sha(native),Agent_seconds=agent['agent_seconds'],charged_tools=agent['charged_tools'],
                requests=len(req),responses=len(resp),observed_received_tokens=sum(u['total_tokens'] for u in usages),
                usage_complete=len(req)==len(resp),guard_rejections=len(guard)))
    return dict(archive_sha256=spec['sha256'],archive_bytes=path.stat().st_size,CRC_valid=True,
        scope='Four original V03 outcome/config/usage summaries rechecked; not new inference or a second full action autopsy',
        cases=result,confounding='Action-First Prompt/exposed development tasks differ from current EGR/MEER case; do not pool treatment effects')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,default=ROOT.parent/'private-evidence'/ARCHIVE_REL)
    ap.add_argument('--output',type=Path,default=HERE);args=ap.parse_args()
    result=analyze(args.archive);args.output.mkdir(parents=True,exist_ok=True)
    outputs={'REQUEST_TIMELINE.json':{k:v for k,v in result.items() if k not in ('actions','shadow_admissions')},
             'ACTION_OBSERVATIONS.json':dict(archive_sha256=result['archive_sha256'],actions=result['actions']),
             'SHADOW_ADMISSIONS.json':dict(archive_sha256=result['archive_sha256'],limits=result['shadow_limits'],scenarios=result['shadow_admissions']),
             'HISTORICAL_CONTEXT_COMPARISON.json':prior_context_comparison()}
    for name,value in outputs.items():
        path=args.output/name;raw=(json.dumps(value,indent=2,ensure_ascii=False,sort_keys=True)+'\n').encode()
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Derived output differs; preserve prior evidence and investigate: '+name)
        if not path.exists():path.write_bytes(raw)
    print(json.dumps(dict(completed_requests=40,guard_rejections=3,
        sessions=[{k:s[k] for k in ('arm','requests','rejected_input_tokens','total_returned_read_lines','repeated_same_path_lines')} for s in result['sessions']])))


if __name__=='__main__':main()
