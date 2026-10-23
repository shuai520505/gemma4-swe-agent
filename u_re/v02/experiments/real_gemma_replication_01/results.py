"""Offline private-archive metrics and integrity replay; never imported by Agent."""
import ast,hashlib,inspect,json,re,types,zipfile
from pathlib import Path
from .notebook import HERE,ROOT,PRODUCTION,PREP,ID,sha,location,verify_shared

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=True)+'\n',encoding='utf8')

def safe_error(value):
    if value is None:return None
    text=json.dumps(value,sort_keys=True) if not isinstance(value,str) else value
    category='CONTEXT_RESERVATION_STOP' if '"decision": "reject"' in text else 'RUNTIME_ERROR_RECORDED_PRIVATELY'
    return dict(category=category,raw_sha256=sha(text.encode()),raw_location='PRIVATE_ARCHIVE')

def _assertion_command(command,scripts):
    if re.search(r'\b(pytest|unittest)\b',command):return True
    if re.search(r'\bassert\b',command):return True
    m=re.search(r'\bpython3?\s+([\w./-]+\.py)',command)
    if m and m.group(1) in scripts:
        try:return any(isinstance(n,ast.Assert) for n in ast.walk(ast.parse(scripts[m.group(1)])))
        except SyntaxError:return False
    return False

def enrich(z,metric,result):
    prefix=f"results/runs/{metric['run']:02d}-{metric['instance_id']}-{metric['arm']}/"
    names=set(z.namelist())
    def load(n,default=None):return json.loads(z.read(prefix+n)) if prefix+n in names else default
    def rows(n):return [json.loads(v) for v in z.read(prefix+n).splitlines()] if prefix+n in names else []
    events=rows('agent/events.jsonl');adk=rows('agent/adk_events.jsonl');wire=rows('agent/http_wire.jsonl')
    start=next((e['recorded_monotonic'] for e in events if e.get('agent_started')),None)
    calls=[];responses={}
    for index,event in enumerate(adk):
        for part in event.get('event',{}).get('content',{}).get('parts',[]):
            if part.get('function_call'):calls.append(dict(part['function_call'],time=event['recorded_monotonic'],index=index))
            if part.get('function_response'):
                r=part['function_response'];responses[r['id']]=dict(r,time=event['recorded_monotonic'],index=index)
    observations=[e for e in events if e.get('kind')=='source_boundary_observation' and start is not None and e['start_monotonic']>=start]
    edits=[e for e in observations if e['production_changed']]
    patch=z.read(prefix+'final.patch') if prefix+'final.patch' in names else None
    paths=[line.split(' b/',1)[1] for line in patch.decode(errors='replace').splitlines() if line.startswith('diff --git ')] if patch else []
    production_paths=[p for p in paths if p.startswith('fastapi/') and p.endswith('.py')]
    diagnostic_paths=[p for p in paths if not p.startswith('fastapi/')]
    production_sections=[];keep=False
    for line in patch.decode(errors='replace').splitlines(keepends=True) if patch else []:
        if line.startswith('diff --git '):keep=line.rstrip('\r\n').split(' b/',1)[-1] in production_paths
        if keep:production_sections.append(line)
    metric.update(final_production_patch_sha256=sha(''.join(production_sections).encode()) if production_sections else None,production_patch_paths=production_paths,nonproduction_patch_paths=diagnostic_paths,diagnostic_only_patch=bool(patch and patch.strip() and not production_paths),ever_production_modified=bool(edits),final_production_patch_present=bool(production_paths))
    if not production_paths:metric['first_observed_applicable_patch_seconds']=None
    tests=[];searches=[];scripts={};test_epoch=0;seen_test=set();seen_search=set();repeated_test=0;repeated_search=0;support=[]
    for call in calls:
        reply=responses.get(call['id']);args=call.get('args') or {};name=call['name'];path=str(args.get('filepath',''))
        if reply and reply.get('response',{}).get('status')=='ok' and name in ('write_file','edit_file'):
            if not path.startswith('fastapi/'):test_epoch+=1
            if name=='write_file':scripts[path]=args.get('content','')
            elif path in scripts:scripts[path]=scripts[path].replace(args.get('old_string',''),args.get('new_string',''))
        if name!='run_command':continue
        command=args.get('command','');h=sha(command.encode())
        observation=next((o for o in observations if o.get('mode')=='exec' and o.get('operation_sha256')==h and o['start_monotonic']>=call['time']),None)
        if not observation:continue
        is_test=_assertion_command(command,scripts)
        if re.search(r'(^|[;&|\s])(rg|grep|find)\s',command):
            key=(command,json.dumps(observation['before'],sort_keys=True));repeated_search+=int(key in seen_search);seen_search.add(key)
            searches.append(dict(command_sha256=h,event_index=call['index'],seconds=call['time']-start))
        if is_test:
            key=(command,json.dumps(observation['before'],sort_keys=True),test_epoch);repeated_test+=int(key in seen_test);seen_test.add(key)
            row=dict(command_sha256=h,event_index=call['index'],seconds=call['time']-start,duration_seconds=observation['end_monotonic']-observation['start_monotonic'],exit_code=observation['exit_code'],production_revision_sha256=sha(json.dumps(observation['before'],sort_keys=True).encode()))
            tests.append(row)
            # An executable assertion is evidence only on an actually modified
            # production revision. Human Issue relation review remains explicit.
            prior_edits=[e for e in edits if e['end_monotonic']<=observation['start_monotonic']]
            if observation['exit_code']==0 and prior_edits and reply and reply['response'].get('status')=='ok':support.append(dict(row,completed_seconds=observation['end_monotonic']-start,review='PENDING_ISSUE_RELATION_REVIEW'))
    metric.update(repeated_unchanged_test_count=repeated_test if result['status']!='NOT_RUN' else None,repeated_search_count=repeated_search if result['status']!='NOT_RUN' else None,observed_assertion_tests=tests,local_assertion_candidates=support,first_locally_supported_assertion_seconds=None,first_locally_supported_patch_seconds=None,local_support_status='PENDING_PRIVATE_TRACE_REVIEW' if support else 'NO_OBSERVED_PASSING_ASSERTION_ON_MODIFIED_PRODUCTION',strict_repeat_definition='Exact assertion command+observed production hashes+observed test/script edit epoch; conservative proxy, not complete filesystem equivalence.')
    # Guard emits on the trusted Worker's journal; tool/source events are on
    # the Agent journal. Both use the same host monotonic clock, not sequence ID.
    admissions=sorted([e for e in rows('events.jsonl')+events if e.get('kind')=='context_admission'],key=lambda e:e['recorded_monotonic'])
    rejections=[e for e in admissions if e.get('decision')=='reject']
    guard=[]
    for event in rejections:
        t=event['recorded_monotonic'];prior_edits=[e for e in edits if e['end_monotonic']<=t]
        prior_submit=[r for r in responses.values() if r.get('name')=='submit_patch' and r.get('response',{}).get('status')=='ok' and r['time']<=t]
        unchanged_after=not any(e['production_changed'] and e['end_monotonic']>t for e in observations)
        guard.append(dict(seconds=t-start,input_tokens=event.get('input_tokens'),total_reserved=event.get('total_reserved'),tools_before=sum(c['time']<=t for c in calls),charged_tool_proxy_before=sum(c['time']<=t and c['name'] not in ('get_status','submit_patch') for c in calls),production_edited_before=bool(prior_edits),submitted_before=bool(prior_submit),blocked_new_model_request=True,native_resolved=result['resolved'],correct_production_patch_at_guard_supported_by_final_native=True if result['resolved'] is True and prior_edits and production_paths and unchanged_after else None,correctness_limit='Only inferred from final native positive plus no subsequent observed production mutation; not a direct verification at guard time.'))
    actual_requests=[e for e in wire if e.get('kind')=='http_request'];actual_responses=[e for e in wire if e.get('kind')=='http_response']
    agent=load('agent/agent_result.json',{}) or {};error=agent.get('error') or ''
    outcome='SUCCESSFUL_REPAIR' if result['resolved'] is True else 'CONTEXT_RESERVATION_STOP' if rejections else 'AGENT_TIMEOUT' if metric.get('deadline_exhausted') else 'TOOL_BUDGET_EXHAUSTED' if metric.get('tool_budget_exhausted') else 'ORDINARY_ALGORITHM_FAILURE' if result['status']=='COMPLETE' else 'NOT_RUN' if result['status']=='NOT_RUN' else 'INFRASTRUCTURE_OR_UNKNOWN'
    metric.update(context_guard_triggered=bool(guard),context_guard_events=guard,context_admissions=[dict(seconds=e['recorded_monotonic']-start,decision=e.get('decision'),input_tokens=e.get('input_tokens'),output_reserved=e.get('output_reserved'),total_reserved=e.get('total_reserved'),input_growth=None if i==0 or not isinstance(e.get('input_tokens'),int) or not isinstance(admissions[i-1].get('input_tokens'),int) else e['input_tokens']-admissions[i-1]['input_tokens']) for i,e in enumerate(admissions)],max_measured_input_tokens=max([e['input_tokens'] for e in admissions if isinstance(e.get('input_tokens'),int)],default=None),actual_HTTP_requests=len(actual_requests),actual_HTTP_responses=len(actual_responses),HTTP_status_counts={str(status):sum(e['status']==status for e in actual_responses) for status in sorted({e['status'] for e in actual_responses})},received_prompt_tokens_per_request=[e.get('body',{}).get('usage',{}).get('prompt_tokens') for e in actual_responses],failure_classification=outcome)
    result['failure_classification']=outcome
    return metric

def analyze(batch,archive):
    directory,slug,_=location(batch);archive=Path(archive).resolve();assert not archive.is_relative_to(ROOT)
    receipt=json.loads((directory/'execution/HTTP_RECEIPT.json').read_bytes())
    manifest=json.loads(sorted((directory/'read_observations').glob('read-*/OUTPUT_MANIFEST.json'))[-1].read_bytes())
    item=next(f for f in manifest['files'] if f['file']=='v02b-gemma-batch'+f'{batch:02d}'+'.zip')
    assert item['Notebook_id']==receipt['Notebook_id'] and item['version']==1 and item['complete'] and manifest['version_bound_before_after']
    assert sha(archive.read_bytes())==item['sha256']
    # Reuse actual GPU03 metrics extraction; only batch/task lock and destination differ.
    from u_re.v01.experiments.action_priority_01.real_gemma_abba01 import analyze as proven
    source=inspect.getsource(proven.analyze).replace("HERE.parent/'integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json'","PRODUCTION/'ABBA_EXPERIMENT_LOCK.json'")
    source=source.replace("for frozen in lock['order']:","for frozen in [r for r in lock['order'] if r['batch']==BATCH]:")
    source=source.replace('Notebook_id=140228050','Notebook_id='+str(receipt['Notebook_id']))
    namespace=dict(proven.__dict__,HERE=directory,ROOT=ROOT,PRODUCTION=PRODUCTION,BATCH=batch)
    exec(compile(source,'<Reused-GPU03-offline-metrics>','exec'),namespace)
    namespace['analyze'](archive)
    metrics=json.loads((directory/'AGENT_BEHAVIOR_METRICS.json').read_bytes());results=json.loads((directory/'ABBA_RESULTS.json').read_bytes());execution=json.loads((directory/'GPU_EXECUTION_RECORD.json').read_bytes())
    lock,_=verify_shared();integrity=[]
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        load=lambda n:json.loads(z.read(n))
        assert load('PAYLOAD_IDENTITY.json')['payload_sha256']==json.loads((PREP/'CPU_END_TO_END_ACCEPTANCE.json').read_bytes())['payload_sha256']
        for n,h in json.loads((PRODUCTION/'GPU03_PAYLOAD_MANIFEST.json').read_bytes())['files'].items():assert sha(z.read('source/'+n))==h,n
        if 'results/MODEL_FILES.json' in z.namelist():assert load('results/MODEL_FILES.json')==lock['model']['files']
        for metric,result in zip(metrics['runs'],results['runs']):
            enrich(z,metric,result)
            prefix=f"results/runs/{result['run']:02d}-{result['instance_id']}-{result['arm']}/"
            if result['status']=='COMPLETE':
                done=load(prefix+'worker_done.json');audit=load(prefix+'audit_result.json');runtime=load(prefix+'runtime_config.json')
                assert done['integrity_complete'] and done['cleanup_complete'] and audit['allow_next_run'] and audit['process_tree_stopped']
                assert runtime['model_transport']=='REAL_GEMMA' and runtime['real_model']
                assert runtime['budget']['agent_seconds']==300 and runtime['budget']['tool_budget']==60 and runtime['budget']['command_seconds']==120
                assert metric['HTTP_terminal_integrity'] and metric['actual_HTTP_requests']>0
                integrity.append(result['run'])
        clean=execution.get('cleanup') or {};status=execution.get('execution') or {}
        env_after=load('PRODUCTION_ENVIRONMENT_AFTER.json') if 'PRODUCTION_ENVIRONMENT_AFTER.json' in z.namelist() else None
        env_before=load('PRODUCTION_ENVIRONMENT_BEFORE.json') if 'PRODUCTION_ENVIRONMENT_BEFORE.json' in z.namelist() else None
        expected_env=json.loads((PREP/'V02B_ENVIRONMENT_LOCK.json').read_bytes())['fingerprint']
        environment_complete=env_before==env_after==expected_env
        full=len(integrity)==4 and not execution.get('STOP') and clean.get('confirmed') and clean.get('idle_error') is None and environment_complete
        if full:
            ids=load('results/TASK_IDENTITIES.json')
            assert set(ids)=={r['instance_id'] for r in lock['order'] if r['batch']==batch}
            for task in lock['tasks']:
                if task['instance_id'] in ids:
                    for k in ('repo','base_commit','issue_sha256','task_record_sha256','test_patch_sha256','input_files'):assert ids[task['instance_id']][k]==task[k]
                    p='results/baselines/'+task['instance_id']+'/'
                    assert not load(p+'official_result.json')['resolved'] and load(p+'official_result.json')['test_exit_code']==1
                    assert load(p+'audit.json')['counts']==task['native_baseline_counts']
                    assert z.read(p+'before.json')==z.read(p+'after.json')
                    assert load(p+'cleanup.json')['complete'] and load(p+'provenance.json')['verified']
        resource=dict(batch=batch,Notebook_id=receipt['Notebook_id'],version=1,status=manifest['status'],completed_sessions=len(integrity),integrity_complete=bool(full),shared_payload_sha256=load('PAYLOAD_IDENTITY.json')['payload_sha256'],environment_before_after_matches=environment_complete,devices=execution.get('devices'),runtime=execution.get('runtime'),model_files=execution.get('model_files'),VLLM_config=execution.get('VLLM_config'),cleanup=clean,cost=execution.get('cost'),STOP=execution.get('STOP'),execution=status,private_archive=str(archive),archive_sha256=sha(archive.read_bytes()),archive_bytes=archive.stat().st_size,CRC_valid=True,formal_submission_requests=0)
        events=[json.loads(v) for v in z.read('results/events.jsonl').splitlines()] if 'results/events.jsonl' in z.namelist() else []
        start=(execution.get('runtime') or {}).get('session_started')
        load_stage=next((e['recorded_monotonic'] for e in events if e.get('stage')=='load_model'),None)
        worker_starts=[]
        for r in results['runs']:
            p=f"results/runs/{r['run']:02d}-{r['instance_id']}-{r['arm']}/events.jsonl"
            if p in z.namelist():worker_starts.append(json.loads(z.read(p).splitlines()[0])['recorded_monotonic'])
        resource['model_start_to_first_worker_upper_bound_seconds']=min(worker_starts)-load_stage if worker_starts and load_stage is not None else None
        resource['timing_limit']='Upper bound includes startup/health/idle/supervision imports; billed GPU time and pure model weight-load time are not independently exposed.'
    # Raw exceptions/tracebacks stay in the already verified private archive.
    for r in results['runs']:
        r['agent_error']=safe_error(r.get('agent_error'))
        if r.get('cleanup'):r['cleanup']['agent_error']=safe_error(r['cleanup'].get('agent_error'))
    results['STOP']=safe_error(results.get('STOP'));resource['STOP']=safe_error(resource.get('STOP'))
    execution['STOP']=safe_error(execution.get('STOP'));write(directory/'GPU_EXECUTION_RECORD.json',execution)
    native=json.loads((directory/'NATIVE_VERIFIER_RESULTS.json').read_bytes())
    for r in native['runs']:
        if r.get('structured_verifier'):r['structured_verifier']['agent_error']=safe_error(r['structured_verifier'].get('agent_error'))
    write(directory/'NATIVE_VERIFIER_RESULTS.json',native)
    write(directory/'AGENT_BEHAVIOR_METRICS.json',metrics);write(directory/'ABBA_RESULTS.json',results)
    write(HERE/f'BATCH_{batch:02d}_EXECUTION.json',resource)
    print(json.dumps(dict(batch=batch,integrity_complete=full,resolved=[(r['instance_id'],r['arm'],r['resolved']) for r in results['runs']])))

def paired(runs,ids):
    counts=dict(Both_Resolved=0,A_Only=0,B_Only=0,Neither_Resolved=0,Unknown=0);pairs=[]
    for ident in ids:
        a=next((r for r in runs if r['instance_id']==ident and r['arm']=='A'),None)
        b=next((r for r in runs if r['instance_id']==ident and r['arm']=='B'),None)
        av=a.get('resolved') if a else None;bv=b.get('resolved') if b else None
        category='Unknown' if av is None or bv is None else 'Both_Resolved' if av and bv else 'A_Only' if av else 'B_Only' if bv else 'Neither_Resolved'
        counts[category]+=1;pairs.append(dict(instance_id=ident,NoEGV=av,Action_First=bv,paired_category=category))
    return dict(counts=counts,pairs=pairs)

def aggregate():
    lock,_=verify_shared();runs=[];metrics=[];native=[];batches=[];archives=[]
    for batch in (1,2):
        d,_,_=location(batch)
        if not (HERE/f'BATCH_{batch:02d}_EXECUTION.json').exists():continue
        execution=json.loads((HERE/f'BATCH_{batch:02d}_EXECUTION.json').read_bytes());batches.append(execution)
        runs+=json.loads((d/'ABBA_RESULTS.json').read_bytes())['runs'];metrics+=json.loads((d/'AGENT_BEHAVIOR_METRICS.json').read_bytes())['runs'];native+=json.loads((d/'NATIVE_VERIFIER_RESULTS.json').read_bytes())['runs']
        archives.append({k:execution[k] for k in ('batch','Notebook_id','version','status','private_archive','archive_sha256','archive_bytes','CRC_valid')})
    observed={r['run'] for r in runs}
    for r in lock['order']:
        if r['run'] not in observed:runs.append(dict(r,status='NOT_RUN',resolved=None,patch_sha256=None))
    runs.sort(key=lambda r:r['run']);metrics.sort(key=lambda r:r['run'])
    ids=[t['instance_id'] for t in lock['tasks']]
    comparison=dict(overall=paired(runs,ids),carry=paired(runs,ids[:1]),new_prospective=paired(runs,ids[1:]),scope='Four FastAPI tasks, one predeclared carry and three new; task/repository dependence, no significance or cross-repository generality claim')
    historical=json.loads((ROOT/'u_re/v01/experiments/action_priority_01/real_gemma_abba03/ABBA_RESULTS.json').read_bytes())['runs']
    comparison['GPU03_separate_exploratory']=paired(historical,['fastapi_9425','fastapi_14786'])
    comparison['combined_six_descriptive']=paired(historical+runs,['fastapi_9425','fastapi_14786']+ids)
    comparison['combined_limit']='Different cohorts and trusted dependency environments; combined six-task description is not a homogeneous confirmatory sample or a leaderboard prediction.'
    arm_totals={}
    for arm in ('A','B'):
        group=[m for m in metrics if m['arm']==arm];results=[r for r in runs if r['arm']==arm]
        successes=sum(r['resolved'] is True for r in results);complete_usage=bool(len(group)==4 and all(m.get('usage_complete') and m.get('received_usage') for m in group))
        tokens={k:sum((m.get('received_usage') or {}).get(k,0) for m in group) for k in ('prompt_tokens','completion_tokens','total_tokens')}
        successful_metrics=[m for m in group if next(r for r in results if r['run']==m['run'])['resolved'] is True]
        observed_success_tokens=sum((m.get('received_usage') or {}).get('total_tokens',0) for m in successful_metrics)
        arm_totals[arm]=dict(resolved=successes,planned_tasks=4,known_native_results=sum(r['resolved'] is not None for r in results),received_usage_observed=tokens if any(m.get('received_usage') for m in group) else None,usage_complete_all_runs=complete_usage,total_tokens_per_success_including_failures=tokens['total_tokens']/successes if complete_usage and successes else None,observed_tokens_in_successful_runs=observed_success_tokens if successful_metrics else None,observed_tokens_in_failed_or_unknown_runs=tokens['total_tokens']-observed_success_tokens if group else None,Agent_wall_seconds_observed=sum(m.get('Agent_wall_seconds') or 0 for m in group) if group else None,Worker_wall_seconds_observed=sum(m.get('Worker_wall_seconds') or 0 for m in group) if group else None,charged_tools_observed=sum(m.get('charged_tools') or 0 for m in group) if group else None,HTTP_requests_observed=sum(m.get('actual_HTTP_requests') or 0 for m in group),HTTP_responses_observed=sum(m.get('actual_HTTP_responses') or 0 for m in group),explicit_submit_runs=sum(m.get('successful_submit') is True for m in group),post_submit_tools=sum(m.get('post_submit_tool_calls') or 0 for m in group),repeated_successful_submits=sum(m.get('repeated_successful_submits') or 0 for m in group),no_observed_production_edit_runs=sum(m.get('ever_production_modified') is False for m in group),diagnostic_only_patch_runs=sum(m.get('diagnostic_only_patch') is True for m in group),context_guard_runs=sum(m.get('context_guard_triggered') is True for m in group),repeated_unchanged_tests=sum(m.get('repeated_unchanged_test_count') or 0 for m in group),cost_scope='Observed costs include failures; missing usage is not zero-imputed. Rates are null unless all planned usage is complete. Per-run nulls remain authoritative.')
    for p in comparison['overall']['pairs']:
        a=next((m for m in metrics if m['instance_id']==p['instance_id'] and m['arm']=='A'),None);b=next((m for m in metrics if m['instance_id']==p['instance_id'] and m['arm']=='B'),None)
        for key in ('first_source_edit_seconds','Agent_wall_seconds','charged_tools'):
            p[key+'_B_minus_A']=b[key]-a[key] if a and b and a.get(key) is not None and b.get(key) is not None else None
    total_agent=sum(m.get('Agent_wall_seconds') or 0 for m in metrics);total_worker=sum(m.get('Worker_wall_seconds') or 0 for m in metrics)
    total_elapsed=sum((b.get('cost') or {}).get('session_elapsed_seconds',0) for b in batches)
    resource=dict(batches=[dict(batch=b['batch'],Notebook_id=b['Notebook_id'],session_elapsed_seconds=(b.get('cost') or {}).get('session_elapsed_seconds'),model_start_to_first_worker_upper_bound_seconds=b.get('model_start_to_first_worker_upper_bound_seconds')) for b in batches],actual_GPU_Notebooks=len(batches),actual_Agent_sessions=sum(r['status']!='NOT_RUN' for r in runs),actual_HTTP_model_requests=sum(m.get('actual_HTTP_requests') or 0 for m in metrics),actual_HTTP_model_responses=sum(m.get('actual_HTTP_responses') or 0 for m in metrics),sum_Notebook_code_elapsed_seconds=total_elapsed,sum_Agent_wall_seconds=total_agent,sum_Worker_wall_seconds=total_worker,observed_non_Agent_code_seconds=total_elapsed-total_agent,observed_outside_Worker_seconds=total_elapsed-total_worker,independent_billed_GPU_seconds=None,peak_memory_by_run=None,limitations='Code wall time is observed, not a billing meter. Account quota deltas are not a per-Notebook bill. Pure model load time/individual GPU active time and unreturned cancelled usage may be unobservable.',formal_Submissions=0)
    final='V02B_REAL_GEMMA_REPLICATION_COMPLETE' if len(batches)==2 and all(b['integrity_complete'] for b in batches) and len(metrics)==8 else 'V02B_REAL_GEMMA_REPLICATION_PARTIAL'
    for name,value in [('ABBA_RESULTS.json',dict(experiment_id=ID,status=final,runs=runs)),('AGENT_BEHAVIOR_METRICS.json',dict(runs=metrics,arm_totals=arm_totals,analysis_only=True)),('NATIVE_VERIFIER_RESULTS.json',dict(runs=native)),('CONTEXT_GUARD_ANALYSIS.json',dict(runs=[{k:m.get(k) for k in ('run','instance_id','arm','context_guard_triggered','context_guard_events','context_admissions','max_measured_input_tokens','received_prompt_tokens_per_request','failure_classification')} for m in metrics],native_and_stop_independent=True)),('PAIRED_ANALYSIS.json',comparison),('RESOURCE_ACCOUNTING.json',resource),('RAW_ARCHIVES.json',dict(archives=archives))]:write(HERE/name,value)
    print(json.dumps(dict(status=final,paired=comparison['overall'],arm_totals=arm_totals)))

if __name__=='__main__':
    import sys
    if sys.argv[1]=='aggregate':aggregate()
    else:analyze(int(sys.argv[1]),sys.argv[2])
