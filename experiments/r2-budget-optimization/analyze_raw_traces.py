"""Read-only reconstruction of nine frozen real sessions. No model/SDK execution."""
import collections,hashlib,json,re,statistics,zipfile
from pathlib import Path

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
ARCHIVE=ROOT/'work/gemma-r12-01/gpu-run02-output/gemma-r12-authorized-gpu-02.zip'
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(name,x):(OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def union(intervals):
    merged=[]
    for a,b in sorted(intervals):
        if b<a:raise ValueError('Reversed interval')
        if merged and a<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],b)
        else:merged.append([a,b])
    return sum(b-a for a,b in merged)
def clipped(intervals,lo,hi):return [(max(a,lo),min(b,hi)) for a,b in intervals if min(b,hi)>max(a,lo)]

CATEGORIES=['有效源码读取','无效源码读取','有效编辑','参数错误编辑','重复编辑','有效测试','无效测试','环境排障','Diff 检查','状态查询','Patch 提交','其他工具调用']
VALID_TEST={1:{4,14},2:{4,5,6,7,9,10,13},3:{4,6,9,11,14,15,16,18,20},4:set(),5:set(),6:set(),7:{5,7,10,12},8:{4,5,6,8,9,10},9:{5,6,7,10}}
INVALID_TEST={1:set(),2:{3,15},3:{3,10,13},4:set(),5:{24,28},6:set(),7:{15},8:set(),9:{4}}
ENV={1:{1,2,3,19},2:{16,18},3:set(),4:set(),5:set(),6:set(),7:set(),8:set(),9:set()}
INVALID_READ={1:{5,6,7,10},2:set(),3:set(),4:set(),5:{18},6:{1,24},7:{1,13},8:{1},9:{1}}
# Each proxy is a directly observed model event, not a claimed internal formation time.
HYPOTHESIS_LINE={1:29,2:9,3:9,4:1,5:1,6:1,7:1,8:1,9:1}
HYPOTHESIS_SUMMARY={1:'Enum string conversion overrides primitive representation; agent additionally considers changing DeferredAttribute assignment, which is not yet a validated repair hypothesis.',2:'Enum.__str__ produces the member name rather than primitive value; overriding conversion is proposed.',3:'Enum.__str__ rather than primitive conversion explains name-valued strings; override Choices is considered alongside field-conversion alternatives.',4:'Inspecting v.data invokes materialization through Variable.values and backend indexing; avoid that accessor for metadata.',5:'Inspecting v.data invokes Variable.values/backend materialization; this is a source-testable causal claim, not yet a verified patch.',6:'The metadata check traverses v.data into values/np.asarray and reads Zarr data.',7:'Membership comparison with a NumPy replacement can produce an array truth-value error; identity is a later candidate fix.',8:'Membership on sentinels invokes overloaded equality and ambiguous array truth conversion.',9:'Membership on sentinels invokes overloaded equality and ambiguous array truth conversion.'}
LOCATION_CALL={1:11,2:1,3:1,4:1,5:1,6:2,7:2,8:2,9:2}
# Valid means a real production-path target observation, even if it exhibits the pre-fix bug.
# Strict passing assertions and weak printed observations are always separated.
TARGET_CALLS={1:[4,14],2:[9,13],3:[14,20],4:[],5:[],6:[],7:[12],8:[8,9,10],9:[10]}
PASS_ASSERTIONS={1:[],2:[13],3:[14,20],4:[],5:[],6:[],7:[],8:[],9:[]}
TEST_SCOPE={1:'Django actual ORM/Enum printed behavior, pre-fix counterexample; no successful repair verification.',2:'Actual Django created/retrieved TextChoices assertions; not a full IntegerChoices or migration suite.',3:'Actual TextChoices and IntegerChoices string assertions; DB smoke fixture failed before exercising target, so complete ORM/regression closure is not established in-loop.',4:'No executed target test.',5:'Both custom post-edit array probes fail in fixture construction/assumptions; no effective real target verification.',6:'No executed target test.',7:'Real num_mock_patch_args smoke prints expected array/default counts but catches errors and has no assertions; weak observation only. The broad compat command has six passes and two setup errors.',8:'Real production helper prints expected array/default/attribute_name results; no strict assertions or native collection test in-loop.',9:'Real production helper prints array/default/mixed/attribute_name results; no strict assertions or native collection test in-loop.'}
NOTES={
 (1,4):('NEW_TARGET_COUNTEREXAMPLE','Valid actual ORM contrast: fresh value displays enum name, retrieved value displays primitive. This provides new evidence.'),
 (1,6):('LOW_NOVELTY_EQUIVALENT_QUERY','Second empty lookup for the same nonexistent fields.py path; the changed grep separator does not address the missing file.'),
 (1,10):('TOOL_SHELL_CONFUSION','Calls the tool name read_file as a shell executable; no source read occurs.'),
 (2,5):('LOW_NOVELTY_MECHANISM_REPEAT','Standalone Enum string demonstration overlaps the prior standalone result; possible comprehension value is not observable.'),
 (2,9):('NEW_TARGET_COUNTEREXAMPLE','A legitimate failing assertion before production edit; expected bug failure is not an invalid tool call.'),
 (2,13):('NEW_PRODUCTION_VERIFICATION','Actual created/readback assertions pass on edited production source.'),
 (2,24):('PREMATURE_MIXED_SCOPE_SUBMISSION','First submit returns 2496 bytes/two files, including the temporary diagnostic script. Do not treat the later cleanup/re-submit as pointless.'),
 (2,26):('NECESSARY_DIAGNOSTIC_CLEANUP','Removing reproduce_issue.py changes patch scope; subsequent diff and submit have real information value.'),
 (2,28):('NECESSARY_SCOPE_CORRECTION','Final submit returns 390 bytes/one production file after diagnostic cleanup.'),
 (3,10):('INVALID_STANDALONE_FIXTURE','Handwritten empty ChoicesMeta does not strip label tuples; failure is a synthetic fixture issue rather than Django repair evidence.'),
 (3,14):('NEW_PRODUCTION_VERIFICATION','Both actual Enum string assertions pass, but DB control remains unverified in-loop.'),
 (3,15):('NEW_INHERITANCE_CONTROL','Production MRO output adds compatibility evidence; do not classify every post-edit check as waste.'),
 (3,16):('PRODUCTION_TYPE_CONTROL','isinstance on actual production Enum is a compatibility check; limited incremental value is uncertain.'),
 (3,17):('COSTLY_COUNTERFACTUAL_REVERSAL','Temporarily removes the working change to show pre-fix behavior. Adds causal evidence, but invalidates the prior passing production version.'),
 (3,18):('COUNTERFACTUAL_BASELINE_OBSERVATION','Prints original Enum-name behavior after deliberate revert. Not a passing fixed-source validation.'),
 (3,19):('NECESSARY_RESTORE_AFTER_REVERSAL','Restores the fix after call 17. Cannot remove this call alone without losing the repair.'),
 (3,20):('NECESSARY_NEW_VERSION_VERIFICATION','Same test as call 14, but production changed twice; revalidation is necessary if the reversal is retained.'),
 (4,21):('LOW_NOVELTY_RELOCATION','Searches already-known get_chunksizes location without production edits in between; no new path evidence.'),
 (4,22):('LOW_NOVELTY_SOURCE_SUBSET','Revisits the same unchanged get_chunksizes body; decision/comprehension effect UNKNOWN.'),
 (5,15):('LOW_NOVELTY_SOURCE_SUBSET','Same get_chunksizes body read earlier; no production edit yet. May refresh context, but no new source bytes.'),
 (5,18):('INVALID_READ_BOUNDS','Requests lines 3100–3200 from a file with 3063 lines; returns a range error.'),
 (5,24):('INVALID_LAZY_TEST_FIXTURE','Variable construction already materializes the fake object; later .loaded lookup addresses ndarray. This cannot validate the production patch.'),
 (5,28):('INVALID_LAZY_TEST_FIXTURE','Attempted fastpath fixture lacks the necessary shape interface; fails before checking metadata behavior.'),
 (6,24):('WRONG_SOURCE_WINDOW','Reads common.py import region rather than implicated helper; no demonstrated target-path information.'),
 (6,30):('BUDGET_REJECTED_EDIT','A schema-valid edit is rejected because 28 charged calls are exhausted; not a missing-parameter edit.'),
 (6,31):('EMPTY_SUBMISSION','Successful submit API response has zero bytes/files; not a valid production repair.'),
 (6,32):('BUDGET_REJECTED_EDIT','Another edit after exhausted charged calls; no production effect.'),
 (6,33):('EMPTY_RESUBMISSION','Second zero-byte submit; tool success must not be counted as a successful repair.'),
 (7,3):('OVERWRITTEN_BEFORE_EXECUTION','Initial repro.py is overwritten at call 4 before it is ever run.'),
 (7,5):('MECHANISM_NOT_PRODUCTION','Copied membership logic demonstrates the failure, but does not invoke the production helper.'),
 (7,7):('MECHANISM_NOT_PRODUCTION','Copied fixed helper prints expected output; useful mechanism check, not verification of production source.'),
 (7,10):('MISBOUND_TEST_REPEAT','Reruns the unchanged copied old repro after production edit; its old failure cannot evaluate the real fix.'),
 (7,12):('WEAK_PRODUCTION_SMOKE','Actual helper prints 0/1, but error catching and no assertions limit strength.'),
 (7,15):('PARTIAL_SUITE_ENVIRONMENT_ERRORS','Six native compat tests pass and two fixtures error. Neither full passing suite nor proof of patch regression.'),
 (7,16):('INFORMATIVE_NEGATIVE_LOOKUP','No matching direct helper test found in one file; this narrows coverage search and is not automatically waste.'),
 (7,17):('INFORMATIVE_NEGATIVE_LOOKUP','Searches a different caller symbol; no match is new negative evidence.'),
 (7,18):('INFORMATIVE_NEGATIVE_LOOKUP','Broadens search to testing/; no direct helper test found. Its value must be weighed against remaining time, not assumed zero.'),
 (7,19):('NECESSARY_DIAGNOSTIC_CLEANUP','Removes three diagnostic scripts before first submit; preserves production-only patch scope.'),
 (8,4):('EXPECTED_PRE_FIX_COUNTEREXAMPLE','ValueError on the membership microcase confirms mechanism; a nonzero exit is expected evidence.'),
 (9,4):('INVALID_DEFAULT_ACCESS','unittest.mock.patch is a function, not a module exposing DEFAULT; wrong fixture attribute.'),
 (9,5):('EXPECTED_PRE_FIX_COUNTEREXAMPLE','Corrected membership microcase reproduces the NumPy ambiguity.'),
}

def category(i,c):
    n=c['ordinal'];tool=c['tool'];r=c.get('response') or {};args=c['args'];cmd=args.get('command','')
    if tool=='get_status':return '状态查询'
    if tool=='submit_patch':return 'Patch 提交'
    if tool=='edit_file':
        if 'mandatory input parameters' in str(r) or 'old_string' not in args:return '参数错误编辑'
        if r.get('status')!='ok':return '其他工具调用'
        return '重复编辑' if i==3 and n in (17,19) else '有效编辑'
    if n in INVALID_TEST[i]:return '无效测试'
    if n in VALID_TEST[i]:return '有效测试'
    if n in ENV[i]:return '环境排障'
    if n in INVALID_READ[i]:return '无效源码读取'
    if re.search(r'\bgit\s+diff\b',cmd):return 'Diff 检查'
    if tool=='read_file':return '有效源码读取' if r.get('status')=='ok' else '无效源码读取'
    if tool=='run_command' and re.match(r'\s*(?:git\s+grep|grep|find|ls)\b',cmd):return '有效源码读取'
    return '其他工具调用'

all_sessions=[];time_rows=[];raw_index=[]
with zipfile.ZipFile(ARCHIVE) as z:
    assert z.testzip() is None
    pairs=json.loads(z.read('execution/PAIR_RESULTS.json'))
    coordinator=[json.loads(l) for l in z.read('execution/events.jsonl').splitlines()]
    coord={e['stage']:e['recorded_monotonic'] for e in coordinator if e.get('kind')=='stage'}
    for record in pairs['records']:
        i=record['index'];candidate=record['candidate'];task=record['task'];p=f'execution/sessions/{i:02d}_{candidate}_{task}/'
        def read(name):
            raw=z.read(p+name);raw_index.append(dict(session=i,member=p+name,bytes=len(raw),sha256=sha(raw)))
            return [json.loads(l) for l in raw.splitlines()] if name.endswith('.jsonl') else json.loads(raw)
        ev=read('events.jsonl');adk=read('adk_events.jsonl');wire=read('model_transport/http_wire.jsonl');life=read('model_transport/http_lifecycle.jsonl');row=read('SESSION_RESULT.json');metrics=read('R12_METRICS.json');cfg=read('CONFIGURATION.json')
        start=next(e['recorded_monotonic'] for e in ev if e.get('agent_started'));end=start+row['agent_seconds']
        end_event=next(e for e in ev if e.get('agent_elapsed_seconds') is not None)
        assert abs(end-end_event['recorded_monotonic'])<.02
        calls={};ordered=[];thoughts=[]
        for ln,e in enumerate(adk,1):
            at=e['recorded_monotonic']
            for part in (e.get('event',{}).get('content') or {}).get('parts',[]):
                c=part.get('function_call');resp=part.get('function_response')
                if c and c['id'] not in calls:
                    x=dict(id=c['id'],ordinal=len(ordered)+1,tool=c['name'],args=c.get('args',{}),start=at-start,adk_call_line=ln);calls[c['id']]=x;ordered.append(x)
                if resp:
                    assert resp['id'] in calls
                    calls[resp['id']].update(response=resp.get('response'),end=at-start,adk_response_line=ln)
                if part.get('text'):thoughts.append(dict(line=ln,seconds=at-start,text=part['text'],thought=part.get('thought',False)))
        requests={e['request_id']:(ln,e) for ln,e in enumerate(wire,1) if e['kind']=='http_request'}
        responses={e['request_id']:(ln,e) for ln,e in enumerate(wire,1) if e['kind']=='http_response'}
        terminals={e['request_id']:(ln,e) for ln,e in enumerate(life,1) if e['kind']=='terminal_status'}
        assert len(requests)==len(terminals) and requests.keys()==terminals.keys()
        http_spans=[];http_records=[];http_tool_map={};usage=[];schema_missing=[]
        for rid,(ln,req) in requests.items():
            tln,terminal=terminals[rid];a=req['recorded_monotonic'];b=terminal['recorded_monotonic'];assert b>=a
            http_spans.append((a,b));body=req['body'];schemas={t['function']['name']:t['function'].get('parameters',{}) for t in body.get('tools',[])}
            tool_ids=[]
            if rid in responses:
                rln,response=responses[rid]
                for choice in response['body'].get('choices',[]):
                    for call in choice.get('message',{}).get('tool_calls',[]):
                        tool_ids.append(call['id']);f=call['function']
                        try:args=json.loads(f['arguments']);missing=sorted(set(schemas.get(f['name'],{}).get('required',[]))-set(args))
                        except (ValueError,TypeError):missing=['INVALID_JSON_ARGUMENTS']
                        http_tool_map[call['id']]=dict(request_id=rid,request_line=ln,response_line=rln,terminal_line=tln,roundtrip_seconds=b-a,request_start_seconds=a-start,response_end_seconds=b-start,tool_ids=tool_ids,required_fields=schemas.get(f['name'],{}).get('required',[]),emitted_argument_keys=sorted(args) if isinstance(args,dict) else None,missing_fields=missing,finish_reason=choice.get('finish_reason'))
                        if missing:schema_missing.append(dict(id=call['id'],tool=f['name'],missing=missing))
            u=terminal.get('usage')
            if isinstance(u,dict) and all(type(u.get(k)) is int for k in ('prompt_tokens','completion_tokens','total_tokens')):usage.append(u)
            is_summary=not body.get('tools') and any(str(m.get('content','')).startswith('The following is a conversation history between a user and an AI agent. Please summarize') for m in body.get('messages',[]))
            purpose='SDK_COMPACTION_SUMMARY' if is_summary else 'TOOL_ACTION_RESPONSE' if tool_ids else 'NON_TOOL_RESPONSE_OR_ABORT'
            http_records.append(dict(request_id=rid,wire_request_line=ln,wire_response_line=responses.get(rid,(None,None))[0],lifecycle_terminal_line=tln,start_seconds=a-start,end_seconds=b-start,roundtrip_seconds=b-a,status=terminal.get('status'),usage=u,tool_call_ids=tool_ids,purpose=purpose))
        assert len(ordered)==metrics['attempted_calls']
        assert sum(bool(v['missing_fields']) for v in http_tool_map.values())==len(metrics['invalid_calls'])
        warnings=[];same=[];coverage={};statehash={};tool_spans=[]
        for c in ordered:
            assert c['id'] in http_tool_map,'Generated tool call absent from raw HTTP response'
            n=c['ordinal'];resp=c.get('response') or {};cls=category(i,c)
            c['category']=cls;c['evidence_class']='REAL_GPU_OBSERVATION';c['classification_basis']='Static adjudication of actual arguments, tool results and next action; usefulness is not a causal inference.'
            c['raw_evidence']=dict(archive_member=p+'adk_events.jsonl',call_line=c['adk_call_line'],response_line=c.get('adk_response_line'),call_id=c['id'],response_sha256=sha(json.dumps(resp,sort_keys=True).encode()),http=http_tool_map[c['id']])
            c['http_roundtrip_seconds']=http_tool_map[c['id']]['roundtrip_seconds'];c['observed_tool_envelope_seconds']=c.get('end',c['start'])-c['start'] if 'end' in c else None
            if 'end' in c:tool_spans.append((start+c['start'],start+c['end']))
            c['server_queue_seconds']=None;c['pure_model_generation_seconds']=None;c['internal_thinking_seconds']=None;c['pure_sandbox_execution_seconds']=None
            if resp.get('budget_warning'):warnings.append(dict(ordinal=n,seconds=c.get('end'),text=resp['budget_warning']))
            c['information_contribution']=dict(status='NEW_QUERY_OR_OBSERVATION',decision_change='UNKNOWN',observed_next_action=ordered[n]['tool'] if n<len(ordered) else None,explanation='New source or diagnostic information may inform a decision; next-action association alone cannot establish causality.')
            if c['tool']=='read_file' and resp.get('status')=='ok':
                file=c['args']['filepath'];a=resp.get('start_line');b=resp.get('end_line');ranges=coverage.setdefault(file,[])
                if a is not None and b is not None:
                    prior=next((q for q in ranges if q[0]<=a and b<=q[1]),None)
                    if prior:
                        c['information_contribution'].update(status='PRIOR_SOURCE_WINDOW_SUBSET',prior_ordinal=prior[2],explanation='No production edit on this file intervened; source bytes were already returned. Reconsideration/compaction refresh may still have decision value; not automatically waste.')
                    ranges.append((a,b,n))
            if c['tool']=='edit_file' and resp.get('status')=='ok':coverage.pop(c['args']['filepath'],None)
            if (i,n) in NOTES:
                status,note=NOTES[i,n];c['information_contribution'].update(status=status,explanation=note)
            if cls=='参数错误编辑':c['information_contribution'].update(status='SCHEMA_REJECTED',explanation='Required old_string is absent in the actual model arguments. No edit executes; subsequent equivalent retry does not repair the schema defect.')
            c['successful_tool_result']=resp.get('status')=='ok'
            c['tool_error']=resp.get('status')=='error' or bool(resp.get('error'))
            c['explicit_remaining_time_observation']=resp.get('time_seconds_remaining')
            c['edit_tool_returned_diff']=bool(resp.get('diff'))
            c['token_and_latency_savings_if_removed']=None
            nxt=ordered[n] if n<len(ordered) else None
            if nxt:
                next_file=nxt['args'].get('filepath','')
                if next_file and next_file in str(resp.get('stdout','')):
                    c['information_contribution']['observed_transition']='Lookup result names the file read/edited next; location evidence is used in the next action.'
                elif c['tool']=='read_file' and nxt['tool']=='edit_file' and next_file==c['args'].get('filepath'):
                    c['information_contribution']['observed_transition']='The next action edits the same file; whether the read caused the decision is UNKNOWN.'
                elif c['category']=='参数错误编辑' and nxt['tool']=='edit_file':
                    c['information_contribution']['observed_transition']='The next edit repeats the same missing-parameter error rather than correcting it.'
                elif c['tool_error']:
                    c['information_contribution']['observed_transition']='The next action is retained by ID; a different search/reproduction may be a legitimate recovery, not zero-value repetition.'
                else:c['information_contribution']['observed_transition']='Next action linked by ID; no independently identifiable change in internal decision state.'
            key=(c['tool'],json.dumps(c['args'],sort_keys=True))
            if key in statehash:same.append(dict(previous_ordinal=statehash[key],ordinal=n,meaning='Same arguments only; source/environment may differ. Not itself a waste label.'))
            statehash[key]=n
        explicit_diff=[c for c in ordered if c['category']=='Diff 检查'];submits=[c for c in ordered if c['tool']=='submit_patch'];edits=[c for c in ordered if c['tool']=='edit_file' and (c.get('response') or {}).get('status')=='ok']
        def mark(n):
            if n is None:return None
            c=ordered[n-1];return dict(ordinal=n,call_id=c['id'],start_seconds=c['start'],observed_completion_seconds=c.get('end'),adk_call_line=c['adk_call_line'],adk_response_line=c.get('adk_response_line'))
        hyp=next(t for t in thoughts if t['line']==HYPOTHESIS_LINE[i] and t['thought'])
        first=next((e for e in ev if e.get('kind')=='first_production_edit_observed'),None)
        interval=dict(lower_seconds=first['lower_bound_monotonic']-start,upper_seconds=first['observed_monotonic']-start,source_event_line=ev.index(first)+1) if first else None
        assert interval==None or abs(interval['upper_seconds']-metrics['first_production_edit']['upper_seconds'])<1e-9
        total_http=union(clipped(http_spans,start,end));total_tools=union(clipped(tool_spans,start,end));combined=union(clipped(http_spans+tool_spans,start,end));overlap=total_http+total_tools-combined
        verify=next(e['recorded_monotonic'] for e in ev if e.get('stage')=='verification');persist=next(e['recorded_monotonic'] for e in ev if e.get('stage')=='persist')
        last_submit=submits[-1] if submits else None;lastedit=edits[-1] if edits else None;testcalls=TARGET_CALLS[i];passing=PASS_ASSERTIONS[i]
        target_after_last=[n for n in testcalls if lastedit and ordered[n-1]['start']>lastedit['end']]
        category_stats={c:dict(count=sum(a['category']==c for a in ordered),observed_tool_envelope_seconds=sum(a['observed_tool_envelope_seconds'] or 0 for a in ordered if a['category']==c),associated_http_roundtrip_seconds=sum(a['http_roundtrip_seconds'] for a in ordered if a['category']==c)) for c in CATEGORIES}
        # All observed responses here produce at most one tool action; guard against
        # double-counting HTTP if a future input contains parallel tool calls.
        assert all(len(r['tool_call_ids'])<=1 for r in http_records)
        T=dict(T0=dict(seconds=0.0,definition='Recorded start_agent_session monotonic origin'),T1_first_relevant_source_location=mark(LOCATION_CALL[i]),
            T2_internal_hypothesis_formation_seconds=None,T2_observable_hypothesis_proxy=dict(seconds=hyp['seconds'],adk_event_line=hyp['line'],text_sha256=sha(hyp['text'].encode()),summary=HYPOTHESIS_SUMMARY[i],status='Observable causal explanation, not proof or an internal thinking timestamp'),
            T3_first_production_edit_interval=interval,T4_first_effective_production_target_observation=mark(testcalls[0]) if testcalls else None,
            T4_first_passing_production_assertions=mark(passing[0]) if passing else None,T5_last_successful_production_edit_tool=mark(lastedit['ordinal']) if lastedit else None,
            T5_exact_last_write_seconds=None,T6_last_effective_production_target_or_control_observation=mark(testcalls[-1]) if testcalls else None,
            T6_last_passing_production_assertions=mark(passing[-1]) if passing else None,T7_first_explicit_diff=mark(explicit_diff[0]['ordinal']) if explicit_diff else None,
            T7_latest_edit_diff_available=mark(lastedit['ordinal']) if lastedit and (lastedit.get('response') or {}).get('diff') else None,
            T8_submit_patch=[mark(c['ordinal'])|dict(patch_size=(c.get('response') or {}).get('patch_size'),files_changed=(c.get('response') or {}).get('files_changed')) for c in submits],
            T9=dict(seconds=row['agent_seconds'],source_event_line=ev.index(end_event)+1,meaning='Agent session end; worker/evaluator continue afterwards'))
        for req in http_records:req['after_last_submit']=bool(last_submit and req['start_seconds']>=last_submit['end'])
        time_row=dict(index=i,candidate=candidate,task=task,evidence='REAL_GPU_OBSERVATION',session_prefix=p,monotonic_origin=start,events=T,
            task_test_scope=TEST_SCOPE[i],agent_execution_seconds=row['agent_seconds'],official_charged_seconds=None,
            official_time_status='UNKNOWN: no private scorer charging timestamps; R12 is a development runner',
            phase1_generation_cost_proxy_seconds=verify-coord['session_'+str(i)],
            worker_import_initialization_and_sandbox_setup_proxy_seconds=start-coord['session_'+str(i)],
            post_agent_cleanup_and_patch_save_proxy_seconds=verify-end,
            excluded_independent_evaluation_seconds=persist-verify,
            worker_reported_complete_cost_seconds=row['worker_seconds'],worker_supervisor_wall_seconds=record['worker']['duration_seconds'],
            coordinator_next_boundary_wall_proxy_seconds=coord.get('session_'+str(i+1),coord['cleanup'])-coord['session_'+str(i)],
            localization_proxy_elapsed_seconds=ordered[LOCATION_CALL[i]-1].get('end'),
            observed_hypothesis_proxy_elapsed_seconds=hyp['seconds'],
            hypothesis_to_first_edit_interval_seconds=dict(lower=interval['lower_seconds']-hyp['seconds'],upper=interval['upper_seconds']-hyp['seconds']) if interval else None,
            last_edit_to_first_subsequent_effective_target_test_seconds=ordered[target_after_last[0]-1]['end']-lastedit['end'] if target_after_last else None,
            last_edit_to_last_submit_completion_seconds=last_submit['end']-lastedit['end'] if last_submit and lastedit else None,
            first_edit_to_last_submit_completion_interval_seconds=dict(lower=last_submit['end']-interval['upper_seconds'],upper=last_submit['end']-interval['lower_seconds']) if last_submit and interval else None,
            submit_tool_envelope_seconds=sum(c['end']-c['start'] for c in submits),
            post_last_submit_until_agent_end_seconds=row['agent_seconds']-last_submit['end'] if last_submit else None,
            final_invalid_idle_wait_seconds=None,final_idle_caveat='UNKNOWN: post-submit time includes real final-completion HTTP and Harness work; no basis to label all of it idle or removable.',
            http_request_roundtrip_union_inside_agent_seconds=total_http,tool_call_envelope_union_inside_agent_seconds=total_tools,
            observer_interval_overlap_seconds=overlap,unattributed_agent_seconds=row['agent_seconds']-combined,
            pure_model_generation_seconds=None,server_queue_seconds=None,internal_thinking_seconds=None,
            charged_tools=row['charged_tools'],attempted_tools=len(ordered),http_requests=len(requests),native_llm_counter=row['llm_calls'],
            SDK_compaction_requests=sum(r['purpose']=='SDK_COMPACTION_SUMMARY' for r in http_records),SDK_compaction_roundtrip_seconds=sum(r['roundtrip_seconds'] for r in http_records if r['purpose']=='SDK_COMPACTION_SUMMARY'),
            post_last_submit_HTTP_roundtrip_seconds=sum(r['roundtrip_seconds'] for r in http_records if r['after_last_submit']),
            observed_token_usage={k:sum(u[k] for u in usage) for k in ('prompt_tokens','completion_tokens','total_tokens')} if usage else None,token_usage_complete=len(usage)==len(requests),
            original_issue_target_passed=row['evaluation'].get('target_passed'),positive_controls_passed=row['evaluation'].get('positive_controls_passed'),
            official_native_resolved=row['official_native_resolved'],canonical_swebench_resolved=row['canonical_swebench_resolved'],agent_error=row.get('agent_error'),
            no_fabricated_wait_or_generation_attribution=True)
        time_rows.append(time_row)
        # Preserve compact raw fields needed to audit a classification without copying all source output.
        compact=[]
        for c in ordered:
            d={k:v for k,v in c.items() if k!='response'};resp=c.get('response') or {}
            d['response_summary']={k:resp[k] for k in ['status','error_type','error_message','error','patch_size','files_changed','budget_warning','time_seconds_remaining','tool_calls_remaining','agent_elapsed_seconds','start_line','end_line','total_lines','is_truncated'] if k in resp}
            if resp.get('stdout'):d['response_summary']['stdout_excerpt']=resp['stdout'][:450]
            if resp.get('content'):d['response_summary']['source_content_sha256']=sha(resp['content'].encode())
            d['next_action_id']=ordered[c['ordinal']]['id'] if c['ordinal']<len(ordered) else None
            compact.append(d)
        all_sessions.append(dict(index=i,candidate=candidate,task=task,actions=compact,category_statistics=category_stats,charged_tools=row['charged_tools'],attempted_tools=len(ordered),schema_errors=schema_missing,
            automatic_call_budget_warnings=warnings,status_queries=sum(c['tool']=='get_status' for c in ordered),explicit_diff_calls=len(explicit_diff),
            same_argument_repeats=same,production_edit_diff_visible_to_model=bool(lastedit and (lastedit.get('response') or {}).get('diff')),
            http_requests=http_records,inference_caveat='Associated request roundtrip includes server queue/prefill/decode/transport; not pure thinking, not a removable-cost estimate. Tool envelope includes host dispatch; exact sandbox command duration is not recorded.'))
    raw_index.append(dict(member='execution/events.jsonl',sha256=sha(z.read('execution/events.jsonl'))))
    raw_index.append(dict(member='execution/PAIR_RESULTS.json',sha256=sha(z.read('execution/PAIR_RESULTS.json'))))
    raw_index.append(dict(member='extension/r12_issue_checks.py',sha256=sha(z.read('extension/r12_issue_checks.py'))))

assert len(time_rows)==9 and sum(s['attempted_tools'] for s in all_sessions)==209
assert sum(s['charged_tools'] for s in all_sessions)==192
assert sum(len(s['schema_errors']) for s in all_sessions)==5
r2=[r for r in time_rows if r['candidate']=='R2'];total=sum(r['agent_execution_seconds'] for r in r2)
reconciliation=dict(R2_agent_total_seconds=total,R2_agent_mean_seconds=total/3,
    R2_generation_proxy_total_seconds=sum(r['phase1_generation_cost_proxy_seconds'] for r in r2),
    R2_generation_proxy_mean_seconds=statistics.mean(r['phase1_generation_cost_proxy_seconds'] for r in r2),
    additional_import_setup_proxy_mean_seconds=statistics.mean(r['worker_import_initialization_and_sandbox_setup_proxy_seconds'] for r in r2),
    additional_save_cleanup_proxy_mean_seconds=statistics.mean(r['post_agent_cleanup_and_patch_save_proxy_seconds'] for r in r2),
    R2_worker_complete_mean_seconds=statistics.mean(r['worker_reported_complete_cost_seconds'] for r in r2),
    official_charged_time_seconds=None,
    budget_recommendation='Use separate conditional generation-proxy and stress-overhead scenarios; only officially scoped Phase 1 plus setup timestamps would establish real official cost. Exclude independent verification, do not add tool latency already inside Agent time, and do not substitute Notebook wall time.')
assert abs(reconciliation['R2_agent_mean_seconds']+reconciliation['additional_import_setup_proxy_mean_seconds']+reconciliation['additional_save_cleanup_proxy_mean_seconds']-reconciliation['R2_generation_proxy_mean_seconds'])<1e-6
save('R2_TIME_DECOMPOSITION.json',dict(archive_sha256=sha(ARCHIVE.read_bytes()),clock_definitions='All seconds relative to each raw agent_started monotonic clock. UNKNOWN values are null; confirmed no action is a count zero, not an imputed unknown duration.',reconciliation=reconciliation,sessions=time_rows))
save('R2_TOOL_ACTION_AUDIT.json',dict(archive_sha256=sha(ARCHIVE.read_bytes()),categories=CATEGORIES,total_attempted_tool_calls=209,total_charged_tools=192,classification_method='Source-grounded reviewer adjudication with per-call raw member/line/id/hash links. Expected bug failures and useful negative lookups are not automatically invalid. No assertion that novel information caused an internal decision.',sessions=all_sessions))
save('RAW_EVIDENCE_INDEX.json',dict(archive_path=str(ARCHIVE),archive_sha256=sha(ARCHIVE.read_bytes()),archive_crc_pass=True,members=raw_index))
print(json.dumps(dict(reconciliation=reconciliation,sessions=[dict(index=r['index'],agent=r['agent_execution_seconds'],http=r['http_request_roundtrip_union_inside_agent_seconds'],tools=r['tool_call_envelope_union_inside_agent_seconds'],unknown=r['unattributed_agent_seconds']) for r in time_rows]),indent=2))
