"""Offline actual-event audit. Publishes classifications/hashes, never raw content."""
import ast,json,re,zipfile
from collections import Counter
from .common import HERE,ROOT,sha,write
from u_re.v03.experiments.context_budget_01.offline import ARCHIVES
SOURCES=ARCHIVES+[('V03',ROOT.parent/'private-evidence/u_re_v03_context_gpu01/read-02/evidence_confirmed/output/v03-context-gpu01.zip','05bbbe3626123f1c4dbc7ce01382867e2d84affca942314fda733b3692d50580')]
CATEGORIES=dict(A='Issue understanding',B='Source localization',C='Call-chain/source analysis',D='Explicit falsifiable hypothesis',E='Target-oriented reproduction attempt',F='Exact unchanged search repetition',G='Overbroad test invocation',H='Observed environment/path failure',I='Diagnostic/supporting edit',J='Behavioral production edit candidate',K='Post-edit targeted validation attempt',L='Patch submission',M='Administrative/unknown')
def assertions(source):
    try:return any(isinstance(n,ast.Assert) for n in ast.walk(ast.parse(source)))
    except SyntaxError:return False

def analyze():
    sessions=[];archive_rows=[];total=Counter();new_count=0
    private=ROOT.parent/'private-evidence/u_re_v04_trace_audit';private.mkdir(exist_ok=True)
    for cohort,path,expected in SOURCES:
        assert sha(path.read_bytes())==expected
        archive_rows.append(dict(cohort=cohort,path=str(path),sha256=expected,bytes=path.stat().st_size))
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            for name in sorted(n for n in z.namelist() if n.endswith('agent/adk_events.jsonl')):
                prefix=name.removesuffix('agent/adk_events.jsonl');label=prefix.split('/')[-2]
                events=[json.loads(v) for v in z.read(prefix+'agent/events.jsonl').splitlines()]
                start=next(e['recorded_monotonic'] for e in events if e.get('agent_started'))
                observations=[e for e in events if e.get('kind')=='source_boundary_observation' and e['start_monotonic']>=start]
                edits=[e for e in observations if e['production_changed']]
                adk=[json.loads(v) for v in z.read(name).splitlines()];calls=[];responses={}
                for i,event in enumerate(adk):
                    for part in event.get('event',{}).get('content',{}).get('parts',[]):
                        if part.get('function_call'):calls.append(dict(part['function_call'],index=i,time=event['recorded_monotonic']))
                        if part.get('function_response'):responses[part['function_response']['id']]=dict(part['function_response'],time=event['recorded_monotonic'])
                wire=[json.loads(v) for v in z.read(prefix+'agent/http_wire.jsonl').splitlines()]
                native=json.loads(z.read(prefix+'official_result.json'))
                seen_search=set();seen_reads=set();scripts={};rows=[];located=None;first_test=None;first_behavior=None;path_errors=0;env_errors=0;private_rows=[]
                for c in calls:
                    a=c.get('args') or {};reply=responses.get(c['id']);result=(reply or {}).get('response') or {};command=a.get('command','');filepath=a.get('filepath','');clock=c['time']-start
                    text=json.dumps(result,sort_keys=True);content=str(result.get('stdout',result.get('content','')))
                    error_text=text.lower();path_error=any(v in error_text for v in ('no such file or directory','file or directory not found','filenotfounderror'))
                    env_error=any(v in error_text for v in ('modulenotfounderror','no module named','fixture not found'))
                    path_errors+=path_error;env_errors+=env_error
                    production_path=filepath.startswith('fastapi/') and filepath.endswith('.py')
                    target=production_path or bool(re.search(r'fastapi/(dependencies|security|routing|_compat)',command))
                    if located is None and target and c['name'] in ('read_file','run_command') and result.get('status')=='ok':located=reply['time']-start
                    prior=[e for e in edits if e['end_monotonic']<=c['time']]
                    observation=next((e for e in observations if e['mode']=='exec' and e['operation_sha256']==sha(command.encode()) and e['start_monotonic']>=c['time']),None) if command else None
                    changed=[e for e in edits if c['time']<=e['end_monotonic']<=((reply or {}).get('time',c['time']))]
                    primary='M';reason='Administrative action or purpose not directly established';novel=None;level=None
                    if c['name']=='submit_patch':primary='L';reason='Explicit submission response observed' if reply else 'Submission outcome unobserved'
                    elif c['name'] in ('edit_file','write_file'):
                        source=a.get('new_string',a.get('content',''))
                        debug_only='DEBUG:' in source and ('print(' in source) and c['name']=='edit_file'
                        import_only=source.lstrip().startswith('from typing import (')
                        primary='J' if production_path and changed and not debug_only and not import_only else 'I'
                        reason='Observed production mutation with behavioral code candidate' if primary=='J' else 'Diagnostic/import/support file edit, not demonstrated repair'
                        if primary=='J' and first_behavior is None:first_behavior=changed[0]['end_monotonic']-start
                        if filepath and result.get('status')=='ok':
                            if c['name']=='write_file':scripts[filepath]=a.get('content','')
                            elif filepath in scripts:scripts[filepath]=scripts[filepath].replace(a.get('old_string',''),a.get('new_string',''))
                        level='PRODUCTION_CANDIDATE' if primary=='J' else 'DIAGNOSTIC_EDIT'
                    elif c['name']=='read_file':
                        primary='C' if target else 'M';reason='Implementation/caller read' if target else 'Read relation to target not established'
                        fingerprint=(filepath,sha(text.encode()))
                        novel=True if target and result.get('status')=='ok' and fingerprint not in seen_reads else False if fingerprint in seen_reads else None
                        seen_reads.add(fingerprint);level='SOURCE_OBSERVATION' if novel else None
                    elif c['name']=='run_command':
                        search=bool(re.search(r'(^|[;&|\s])(rg|grep|find)\s',command))
                        pytest=bool(re.search(r'\b(pytest|unittest)\b',command))
                        python=re.search(r'\bpython3?\s+([\w./-]+\.py)',command)
                        test=pytest or bool(python and python.group(1) in scripts) or 'assert ' in command
                        if search:
                            primary='B';reason='Localization query; no presumption that a search is useless'
                            fingerprint=(command,sha(text.encode()),json.dumps(observation['before'],sort_keys=True) if observation else None)
                            if fingerprint in seen_search:primary='F';reason='Exact same query/result/production state; new uncertainty not demonstrated';novel=False
                            seen_search.add(fingerprint)
                        elif test:
                            primary='K' if prior else 'E';reason='Executable check attempt; correctness/contract discrimination requires separate evidence'
                            if first_test is None:first_test=clock
                            broad=pytest and bool(re.search(r'(?:^|&&\s*|;\s*)(?:python3? -m )?pytest\s*$',command))
                            if broad:primary='G';reason='Unscoped entire pytest before locating a relevant existing test set'
                            has_assert=bool('assert ' in command or (python and assertions(scripts.get(python.group(1),''))))
                            level='EXPLICIT_ASSERTION_ATTEMPT' if has_assert else 'PYTEST_SCOPE_UNKNOWN' if pytest else 'PRINT_OR_REPRO_ATTEMPT_NOT_ASSERTION_PROOF'
                        elif re.search(r'\b(ls|sed|head)\b',command):primary='B';reason='File/implementation localization'
                    secondary=[]
                    if path_error or env_error:secondary.append('H')
                    if primary=='M':secondary.append('M')
                    row=dict(event_index=c['index'],tool=c['name'],seconds=clock,response_seconds=(reply['time']-start) if reply else None,category=primary,secondary=secondary,reason=reason,args_sha256=sha(json.dumps(a,sort_keys=True).encode()),response_sha256=sha(text.encode()) if reply else None,confirmed_novel_source_observation=novel,evidence_level=level,observed_path_error=path_error,observed_dependency_error=env_error,production_mutation_observed=bool(changed),non_target_read=True if c['name']=='read_file' and filepath and not filepath.startswith(('fastapi/','tests/')) else None)
                    rows.append(row);private_rows.append(dict(row,args=a,response=result));total[primary]+=1
                first_edit=edits[0]['end_monotonic'] if edits else None
                before_responses=[e for e in wire if e['kind']=='http_response' and first_edit is not None and e['recorded_monotonic']<=first_edit]
                usage=[e['body'].get('usage') for e in before_responses]
                seen_novel=sum(r['confirmed_novel_source_observation'] is True for r in rows);new_count+=seen_novel
                result=json.loads(z.read(prefix+'agent/agent_result.json'))
                all_usage=[e['body'].get('usage') for e in wire if e['kind']=='http_response']
                observed_usage=[u for u in all_usage if u is not None]
                source_reads=[r['response_seconds'] for r in rows if r['tool']=='read_file' and r['confirmed_novel_source_observation'] is True]
                session=dict(cohort=cohort,session=label,raw_events_sha256=sha(z.read(name)),native_resolved=native['resolved'],tools=len(calls),first_target_source_location_seconds=located,source_location_limit='First target-related path/source observation, not proof the defect/call chain was understood',first_confirmed_implementation_read_seconds=min(source_reads) if source_reads else None,first_verifiable_hypothesis_seconds=None,first_production_edit_seconds=first_edit-start if first_edit is not None else None,first_target_behavior_edit_seconds=first_behavior,first_reproduction_or_test_attempt_seconds=first_test,first_genuinely_discriminating_test_seconds=None,repeated_search_count=sum(r['category']=='F' for r in rows),non_target_file_reads_confirmed=sum(r['non_target_read'] is True for r in rows),non_target_read_scope='Outside fastapi/ and tests/; reads of other fastapi modules have UNKNOWN target relevance, not counted as unrelated',path_error_actions=path_errors,dependency_error_actions=env_errors,broad_test_actions=sum(r['category']=='G' for r in rows),tools_before_first_production_edit=sum(c['time']<first_edit for c in calls) if first_edit is not None else None,received_tokens_before_first_production_edit=sum(u['total_tokens'] for u in usage) if usage and all(u is not None for u in usage) else None,Agent_time_before_first_production_edit=first_edit-start if first_edit is not None else None,total_agent_seconds=result.get('agent_seconds'),total_received_tokens_observed=sum(u['total_tokens'] for u in observed_usage) if observed_usage else None,HTTP_responses_missing_usage=len(all_usage)-len(observed_usage),confirmed_novel_source_observations=seen_novel,events=rows,hypothesis_limit='Model reasoning/intent alone is not execution evidence. Earliest falsifiable hypothesis is null unless independently reviewed; no zero-imputation.',discrimination_limit='Automatic green/exit0 is never labeled fail-before/pass-after. Trace review below may establish specific cases.')
                sessions.append(session);write(private/(cohort+'-'+label+'.json'),dict(events=private_rows))
    write(HERE/'TRACE_BEHAVIOR_METRICS.json',dict(archives=archive_rows,categories=CATEGORIES,sessions=sessions,aggregate=dict(observed_sessions=len(sessions),tool_actions=sum(total.values()),primary_categories=dict(total),confirmed_novel_source_observations=new_count),limits='Deterministic conservative annotation of actual commands/results/mutations. Categories are operational descriptions, not proof of necessity or causal effect. Unclassified administrative/uncertain=M. Novel source response is a documented new observation, not proof it advanced repair. Native outcomes never inferred from local tests. Raw details only in controlled private audit exports.'))
    print(json.dumps(dict(sessions=len(sessions),actions=sum(total.values()),counts=total,novel_source=new_count)))
if __name__=='__main__':analyze()
