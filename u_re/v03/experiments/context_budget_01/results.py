"""Offline analysis of confirmed existing outputs; never controls Agent decisions."""
import inspect,json,zipfile
from pathlib import Path
from .common import HERE,ROOT,write,sha
from .audit import counts
from .offline import distribution
from u_re.v02.experiments.real_gemma_replication_01.results import enrich,safe_error

def analyze(archive):
    archive=Path(archive).resolve();assert not archive.is_relative_to(ROOT)
    receipt=json.loads((HERE/'gpu01/execution/HTTP_RECEIPT.json').read_bytes())
    manifest=json.loads(sorted((HERE/'gpu01/read_observations').glob('read-*/OUTPUT_MANIFEST.json'))[-1].read_bytes())
    item=next(f for f in manifest['files'] if f['file']=='v03-context-gpu01.zip')
    assert manifest['version_bound_before_after'] and item['complete'] and item['Notebook_id']==receipt['Notebook_id'] and item['version']==1 and item['sha256']==sha(archive.read_bytes())
    lock=json.loads((HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    from u_re.v01.experiments.action_priority_01.real_gemma_abba01 import analyze as prior
    code=inspect.getsource(prior.analyze).replace("HERE.parent/'integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json'","STUDY/'ABBA_EXPERIMENT_LOCK.json'").replace('Notebook_id=140228050','Notebook_id='+str(receipt['Notebook_id']))
    # Existing helper's raw exceptions and stdout remain in private analysis only.
    intermediate=archive.parent/'offline_analysis';intermediate.mkdir(exist_ok=True)
    ns=dict(prior.__dict__,HERE=intermediate,ROOT=ROOT,STUDY=HERE,write=lambda name,value:write(intermediate/name,value))
    exec(compile(code,'<Reused-native-metrics-V03>','exec'),ns)
    import contextlib
    with (intermediate/'analysis.log').open('w') as log:
        with contextlib.redirect_stdout(log):ns['analyze'](archive)
    results=json.loads((intermediate/'ABBA_RESULTS.json').read_bytes());metrics=json.loads((intermediate/'AGENT_BEHAVIOR_METRICS.json').read_bytes());native=json.loads((intermediate/'NATIVE_VERIFIER_RESULTS.json').read_bytes());execution=json.loads((intermediate/'GPU_EXECUTION_RECORD.json').read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        load=lambda n:json.loads(z.read(n))
        names=set(z.namelist());registration=json.loads((HERE/'GPU03_PAYLOAD_MANIFEST.json').read_bytes())
        assert load('PAYLOAD_IDENTITY.json')['payload_sha256']==registration['payload_sha256']
        for n,h in registration['files'].items():assert sha(z.read('source/'+n))==h,n
        if 'results/MODEL_FILES.json' in names:assert load('results/MODEL_FILES.json')==lock['model']['files']
        identities=load('results/TASK_IDENTITIES.json')
        for task in lock['tasks']:
            ident=task['instance_id']
            for key in ('repo','base_commit','issue_sha256','task_record_sha256','test_patch_sha256','input_files'):assert identities[ident][key]==task[key]
            baseline='results/baselines/'+ident+'/'
            assert load(baseline+'audit.json')['counts']==task['native_baseline_counts']
            assert not load(baseline+'official_result.json')['resolved'] and load(baseline+'official_result.json')['test_exit_code']==1
            assert counts(z.read(baseline+'phase2.junit.xml'))==task['native_baseline_counts']
            assert z.read(baseline+'before.json')==z.read(baseline+'after.json')
            assert load(baseline+'cleanup.json')['complete'] and load(baseline+'provenance.json')['verified']
        for r,m,n in zip(results['runs'],metrics['runs'],native['runs']):
            enrich(z,m,r)
            r['policy']='P0' if r['arm']=='A' else 'P1';m['policy']=r['policy'];n['policy']=r['policy']
            p=f"results/runs/{r['run']:02d}-{r['instance_id']}-{r['arm']}/"
            if r['status']!='COMPLETE':continue
            cfg=load(p+'runtime_config.json');cap=lock['arms'][r['arm']]['max_output_tokens']
            assert cfg['generation']['max_output_tokens']==cfg['budget']['output_tokens']==cap
            assert cfg['generation']['thinking_config']['thinking_budget']==4096 and cfg['generation']['seed']==17
            assert cfg['real_model'] and cfg['model_transport']=='REAL_GEMMA'
            assert cfg['original_candidate_sha256']==lock['arms'][r['arm']]['ZIP_sha256']=='70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8'
            assert z.read(p+'research_candidate/prompts/system.md')==z.read('source/u_re/v01/experiments/action_priority_01/candidate_action_v01/prompts/system.md')
            native_value=load(p+'official_result.json');native_counts=counts(z.read(p+'verifier/phase2.junit.xml'))
            assert native_value['resolved']==r['resolved']==n['resolved']
            assert native_counts['errors']==0 and native_counts['tests']==1
            assert (native_value['test_exit_code'],native_counts['failures'])==((0,0) if r['resolved'] else (1,1))
            assert load(p+'worker_done.json')['integrity_complete'] and load(p+'worker_done.json')['cleanup_complete'] and load(p+'audit_result.json')['allow_next_run']
            wire=[json.loads(x) for x in z.read(p+'agent/http_wire.jsonl').splitlines()]
            requests={e['request_id']:e['body'] for e in wire if e['kind']=='http_request'};responses=[e for e in wire if e['kind']=='http_response']
            assert requests and all(b.get('max_completion_tokens',b.get('max_tokens'))==cap and b['thinking_token_budget']==4096 and b['seed']==17 for b in requests.values())
            output=[]
            for e in responses:
                b=e['body'];u=b.get('usage') or {};choice=b.get('choices',[{}])[0];msg=choice.get('message') or {}
                format_errors=0
                for tool in msg.get('tool_calls') or []:
                    try:
                        args=json.loads(tool.get('function',{}).get('arguments',''))
                        assert isinstance(args,dict)
                    except (ValueError,TypeError,AssertionError):format_errors+=1
                output.append(dict(prompt_tokens=u.get('prompt_tokens'),completion_tokens=u.get('completion_tokens'),total_tokens=u.get('total_tokens'),finish_reason=choice.get('finish_reason'),stop_reason=choice.get('stop_reason'),truncated=choice.get('finish_reason')=='length',tool_calls=len(msg.get('tool_calls') or []),malformed_tool_arguments=format_errors,reasoning_present=bool(msg.get('reasoning')),reasoning_tokens=None,status=e['status']))
            m.update(max_output_tokens=cap,input_cap=32768-cap-1024,HTTP_responses=output,max_received_prompt_tokens=max([e['prompt_tokens'] for e in output if isinstance(e['prompt_tokens'],int)],default=None),completion_distribution=distribution([e['completion_tokens'] for e in output if e['completion_tokens'] is not None]),output_truncated_requests=sum(e['truncated'] for e in output),malformed_tool_arguments=sum(e['malformed_tool_arguments'] for e in output),production_edit_operations=sum(bool(e.get('production_changed')) for e in [json.loads(x) for x in z.read(p+'agent/events.jsonl').splitlines()]),first_meaningful_production_edit=None,first_supported_repair=None,meaningful_edit_review='PENDING_PRIVATE_PATCH_AND_TRACE_REVIEW' if m['ever_production_modified'] else 'NO_PRODUCTION_EDIT')
            assert m['HTTP_terminal_integrity']
            events=[json.loads(x) for x in z.read(p+'agent/events.jsonl').splitlines()]
            start=next(e['recorded_monotonic'] for e in events if e.get('agent_started'))
            edits=[e for e in events if e.get('kind')=='source_boundary_observation' and e['start_monotonic']>=start and e.get('production_changed')]
            m['production_edit_operations']=len(edits)
            # A workspace bootstrap copy is not an Agent edit. Meaningful edit
            # classification is a separate, archive-bound offline trace review.
            review_path=HERE/'TRACE_REVIEW.json'
            if review_path.exists():
                review=json.loads(review_path.read_bytes());assert review['archive_sha256']==sha(archive.read_bytes())
                assessment=next(a for a in review['runs'] if a['run']==r['run'])
                index=assessment['first_meaningful_edit_observation_index']
                m['first_meaningful_production_edit']=edits[index]['end_monotonic']-start if index is not None else None
                m['meaningful_edit_review']=assessment['classification']
                m['first_local_regression_pass_seconds']=assessment.get('first_local_regression_pass_seconds')
                m['local_support_status']=assessment['local_support_status']
                for candidate in m['local_assertion_candidates']:candidate['review']=assessment['local_support_status']
            # The first directly observed native-positive test is after Agent
            # termination. Do not backdate this proof to first edit/guard time.
            verifier=[json.loads(x) for x in z.read(p+'verifier/events.jsonl').splitlines()]
            native_test=next((e for e in verifier if e.get('kind')=='sandbox_command_start' and e.get('command_kind')=='pytest'),None)
            native_end=next((e for e in verifier if native_test and e.get('kind')=='sandbox_command_end' and e['recorded_monotonic']>=native_test['recorded_monotonic']),None)
            if r['resolved'] is True and native_end and native_end.get('exit_code')==0:
                m['first_supported_repair']=dict(seconds=native_end['recorded_monotonic']-start,source='TRUSTED_NATIVE_VERIFIER_AFTER_AGENT',scope='First observed native-positive final patch; not proof of earliest moment patch became correct,not visible to Agent')
        env_before=load('PRODUCTION_ENVIRONMENT_BEFORE.json') if 'PRODUCTION_ENVIRONMENT_BEFORE.json' in names else None
        env_after=load('PRODUCTION_ENVIRONMENT_AFTER.json') if 'PRODUCTION_ENVIRONMENT_AFTER.json' in names else None
        environment=env_before==env_after==json.loads((ROOT/'u_re/v02/experiments/env_recovery_admission_01/V02B_ENVIRONMENT_LOCK.json').read_bytes())['fingerprint']
    for r,m in zip(results['runs'],metrics['runs']):
        r['agent_error']=safe_error(r.get('agent_error'))
        if r['agent_error'] and m['failure_classification']=='AGENT_TIMEOUT':r['agent_error']['category']='AGENT_TIMEOUT'
        if r.get('cleanup'):r['cleanup']['agent_error']=safe_error(r['cleanup'].get('agent_error'))
        if r.get('cleanup',{}).get('agent_error') and m['failure_classification']=='AGENT_TIMEOUT':r['cleanup']['agent_error']['category']='AGENT_TIMEOUT'
    for n,m in zip(native['runs'],metrics['runs']):
        if n.get('structured_verifier'):n['structured_verifier']['agent_error']=safe_error(n['structured_verifier'].get('agent_error'))
        if n.get('structured_verifier',{}).get('agent_error') and m['failure_classification']=='AGENT_TIMEOUT':n['structured_verifier']['agent_error']['category']='AGENT_TIMEOUT'
    results['STOP']=safe_error(results.get('STOP'));execution['STOP']=safe_error(execution.get('STOP'))
    execution.update(platform_status=manifest['status'],environment_matches=environment,payload_sha256=registration['payload_sha256'],source_archive_bytes=archive.stat().st_size)
    assert environment and execution['cleanup']['confirmed'] and not execution['cleanup']['remaining'] and execution['cleanup']['idle_error'] is None
    assert len(execution['devices'])==4 and all(d['name']=='NVIDIA L4' and d['memory_bytes']>=22*1024**3 for d in execution['devices'])
    assert execution['VLLM_config']['tensor_parallel_size']==4 and execution['VLLM_config']['max_model_len']==32768
    assert execution['isolation']['exit_code']==0 and execution['STOP'] is None
    results['status']='V03_CONTEXT_PILOT_COMPLETE' if all(r['status']=='COMPLETE' for r in results['runs']) else 'V03_CONTEXT_PILOT_PARTIAL'
    execution['integrity_complete']=True
    write(HERE/'NATIVE_RESULTS.json',results);write(HERE/'NATIVE_VERIFIER_RESULTS.json',native);write(HERE/'AGENT_BEHAVIOR_METRICS.json',metrics);write(HERE/'GPU_EXECUTION.json',execution)
    pairs=[]
    for ident in ('fastapi_5077','fastapi_11355'):
        a=next(r for r in results['runs'] if r['instance_id']==ident and r['arm']=='A');b=next(r for r in results['runs'] if r['instance_id']==ident and r['arm']=='B')
        pairs.append(dict(task=ident,P0=a['resolved'],P1=b['resolved']))
    totals={}
    for arm in ('A','B'):
        rows=[m for m in metrics['runs'] if m['arm']==arm and m['status']=='COMPLETE'];usage=[m['received_usage'] for m in rows]
        totals['P0' if arm=='A' else 'P1']=dict(observed_sessions=len(rows),native_resolved=sum(r['resolved'] is True for r in results['runs'] if r['arm']==arm),Agent_wall_seconds=sum(m['Agent_wall_seconds'] for m in rows),Worker_wall_seconds=sum(m['Worker_wall_seconds'] for m in rows),charged_tools=sum(m['charged_tools'] for m in rows),HTTP_requests=sum(m['model_requests'] for m in rows),prompt_tokens=sum(u['prompt_tokens'] for u in usage) if usage and all(usage) else None,completion_tokens=sum(u['completion_tokens'] for u in usage) if usage and all(usage) else None,total_received_tokens=sum(u['total_tokens'] for u in usage) if usage and all(usage) else None,context_guard_sessions=sum(m['context_guard_triggered'] for m in rows),truncated_requests=sum(m.get('output_truncated_requests',0) for m in rows))
    # Sum observed received usage without pretending a cancelled request cost0.
    for arm,key in [('A','P0'),('B','P1')]:
        subset=[m for m in metrics['runs'] if m['arm']==arm and m['status']=='COMPLETE']
        totals[key].update(received_usage_complete=bool(subset) and all(m.get('usage_complete') for m in subset),HTTP_responses=sum(m.get('actual_HTTP_responses',0) for m in subset),unobserved_request_token_usage=None if any(not m.get('usage_complete') for m in subset) else 'NONE_MISSING',malformed_tool_arguments=sum(m.get('malformed_tool_arguments',0) for m in subset))
        totals[key].update(successful_task_received_tokens=sum(m['received_usage']['total_tokens'] for m in subset if m['failure_classification']=='SUCCESSFUL_REPAIR'),all_observed_received_tokens_per_native_success=totals[key]['total_received_tokens']/totals[key]['native_resolved'] if totals[key]['native_resolved'] else None,local_assertion_command_seconds=sum(t['duration_seconds'] for m in subset for t in m['observed_assertion_tests']))
    write(HERE/'COST_ANALYSIS.json',dict(pairs=pairs,policies=totals,resource=execution.get('cost'),limits='Received response sums only. A cancelled/unknown request has UNKNOWN usage,never0. No separate reasoning token allocation or per-session GPU bill. Two exposed FastAPI tasks; no leaderboard/population inference.'))
    write(HERE/'CONTEXT_GUARD_COMPARISON.json',dict(runs=[{k:m.get(k) for k in ('run','instance_id','policy','max_output_tokens','input_cap','context_guard_triggered','context_guard_events','context_admissions','max_measured_input_tokens','max_received_prompt_tokens','actual_HTTP_requests','output_truncated_requests','malformed_tool_arguments','failure_classification')} for m in metrics['runs']]))
    write(HERE/'RAW_ARCHIVES.json',dict(GPU=[dict(Notebook_id=receipt['Notebook_id'],version=1,path=str(archive),sha256=sha(archive.read_bytes()),bytes=archive.stat().st_size,CRC_valid=True)],CPU=json.loads((HERE/'CPU_END_TO_END_ACCEPTANCE.json').read_bytes())['raw_archive_sha256']))
    print(json.dumps(dict(status=results['status'],pairs=pairs,totals=totals)))
if __name__=='__main__':
    import sys
    analyze(sys.argv[1])
