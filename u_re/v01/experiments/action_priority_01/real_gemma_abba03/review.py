"""Offline trace attribution after all four frozen sessions;never an Agent input."""
import ast,hashlib,json,re,zipfile
from pathlib import Path
from .notebook import HERE,PRIOR,sha

def run(archive):
    archive=Path(archive);metrics=json.loads((HERE/'AGENT_BEHAVIOR_METRICS.json').read_bytes())
    lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes());reviews=[]
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest=json.loads((HERE/'GPU03_PAYLOAD_MANIFEST.json').read_bytes())
        assert json.loads(z.read('PAYLOAD_IDENTITY.json'))['payload_sha256']==manifest['payload_sha256']
        for name,h in manifest['files'].items():assert sha(z.read('source/'+name))==h
        assert json.loads(z.read('results/MODEL_FILES.json'))==lock['model']['files']
        assert json.loads(z.read('results/SERVER_CLEANUP.json'))['confirmed']
        for row in metrics['runs']:
            i=row['run'];root=f"results/runs/{i:02d}-{row['instance_id']}-{row['arm']}/"
            assert json.loads(z.read(root+'runtime_config.json'))['model_transport']=='REAL_GEMMA'
            audit=json.loads(z.read(root+'audit_result.json'));assert audit['allow_next_run'] and audit['process_tree_stopped']
            adk=[json.loads(line) for line in z.read(root+'agent/adk_events.jsonl').splitlines()]
            events=[json.loads(line) for line in z.read(root+'agent/events.jsonl').splitlines()]
            start=next(e['recorded_monotonic'] for e in events if e.get('agent_started'))
            calls=[];responses={};call_indices={}
            for index,event in enumerate(adk):
                for part in event.get('event',{}).get('content',{}).get('parts',[]):
                    if part.get('function_call'):
                        call=dict(part['function_call'],time=event['recorded_monotonic'],index=index);calls.append(call);call_indices[call['id']]=index
                    if part.get('function_response'):
                        r=part['function_response'];responses[r['id']]=dict(r,time=event['recorded_monotonic'],index=index)
            # Manually reviewed scripts contain executed target assertions.9425A
            # made no production change,so a passing diagnostic is not patch support.
            command={2:'python3 test_endpoint_none.py',3:'python3 repro.py',4:'python3 repro_issue.py'}.get(i)
            support=[]
            for call in calls:
                r=responses.get(call['id'])
                if command and call['name']=='run_command' and call.get('args',{}).get('command')==command and r and r['response'].get('status')=='ok':
                    support.append(dict(command_sha256=sha(command.encode()),call_event_index=call['index'],response_event_index=r['index'],seconds=r['time']-start))
            row['first_locally_supported_patch_seconds']=support[0]['seconds'] if support else None
            row['local_support_status']='TARGET_ASSERTIONS_PASSED_ON_MODIFIED_WORKSPACE' if support else 'NO_PRODUCTION_PATCH'
            row['local_support_scope']='Agent-created Issue-aligned assertions;does not substitute for native resolved'
            row['strict_test_repeat_review']='Repeated bearer pytest in run4 followed actual test-file additions;test inputs changed. Identical print-only diagnostics are not assertion tests.'
            paths=[line.split(' b/',1)[1] for line in z.read(root+'final.patch').decode().splitlines() if line.startswith('diff --git ')]
            row['final_patch_paths']=paths
            row['diagnostic_patch_residue']=bool(i==1)
            row['context_reservation_rejected']=bool('"decision": "reject"' in (json.loads(z.read(root+'agent/agent_result.json')).get('error') or ''))
            reads=set();repeat_reads=0;test_edits=[];command_failures=[]
            test_epoch=0;scripts={};seen_tests=set();strict_repeats=0
            for call in calls:
                response=responses.get(call['id']);args=call.get('args',{})
                if not response:continue
                result=response['response']
                path=str(args.get('filepath',''))
                if call['name'] in ('write_file','edit_file') and result.get('status')=='ok' and path.endswith('.py'):
                    if not path.startswith('fastapi/'):test_epoch+=1
                    if call['name']=='write_file':scripts[path]=args.get('content','')
                if call['name']=='run_command':
                    cmd=args.get('command','');is_test=bool(re.search(r'pytest|unittest|\bassert\b',cmd))
                    script=re.search(r'\bpython3?\s+([\w./-]+\.py)',cmd)
                    if script and script.group(1) in scripts:
                        try:is_test|=any(isinstance(n,ast.Assert) for n in ast.walk(ast.parse(scripts[script.group(1)])))
                        except SyntaxError:pass
                    observation=next((e for e in events if e.get('kind')=='source_boundary_observation' and e.get('mode')=='exec' and e.get('operation_sha256')==sha(cmd.encode()) and e['start_monotonic']>=call['time']),None)
                    if is_test and observation:
                        key=(cmd,json.dumps(observation['before'],sort_keys=True),test_epoch)
                        strict_repeats+=int(key in seen_tests);seen_tests.add(key)
                if call['name']=='read_file' and result.get('status')=='ok':
                    key=(json.dumps(args,sort_keys=True),json.dumps(result,sort_keys=True));repeat_reads+=int(key in reads);reads.add(key)
                if call['name']=='edit_file' and str(args.get('filepath','')).startswith('tests/'):
                    test_edits.append(dict(path=args['filepath'],event_index=call['index'],status=result.get('status')))
                if call['name']=='run_command' and result.get('status')=='error':
                    cmd=args.get('command','');detail=result.get('details',{});text=str(result)
                    category='DEPENDENCY_COLLECTION_ERROR' if 'python-multipart' in text and detail.get('exit_code')==2 else 'ASSERTION_COUNTEREXAMPLE' if 'Assertion failed' in text else 'NEGATIVE_SEARCH_OR_PATH_RESULT' if re.search(r'grep|\bls\b',cmd) else 'COMMAND_FAILURE'
                    command_failures.append(dict(event_index=call['index'],command_sha256=sha(cmd.encode()),category=category,exit_code=detail.get('exit_code')))
            row['repeated_identical_read_response_proxy']=repeat_reads
            row['repeated_unchanged_test_count']=strict_repeats
            row['strict_repeat_definition']='Exact assertion-test command+production hashes+observed Python test/diagnostic edit epoch. Conservative observed proxy;does not prove complete hidden environment identity.'
            reviews.append(dict(run=i,local_support=support,final_patch_paths=paths,test_edit_attempts=test_edits,
                final_patch_contains_tests=any(p.startswith('tests/') for p in paths),command_failure_categories=command_failures,
                notes='Run4 adds two positive public regression cases;official final patch excludes test edits. No weakened assertion observed. Run1 leaves three diagnostic files and no production edit.' if i in (1,4) else 'Temporary diagnostics were removed before final patch.'))
        cost=json.loads(z.read('results/GPU_COST.json'));runtime=json.loads(z.read('results/GPU_RUNTIME.json'))
        root_events=[json.loads(l) for l in z.read('results/events.jsonl').splitlines()]
        prepare=next(e['recorded_monotonic'] for e in root_events if e.get('stage')=='prepare_agent')
        load=next(e['recorded_monotonic'] for e in root_events if e.get('stage')=='load_model')
        first_worker=json.loads(z.read('results/runs/01-fastapi_9425-A/events.jsonl').splitlines()[0])['recorded_monotonic']
        agents=sum(r['Agent_wall_seconds'] for r in metrics['runs']);workers=sum(r['Worker_wall_seconds'] for r in metrics['runs'])
        resource=dict(Notebook_code_elapsed_seconds=cost['session_elapsed_seconds'],sum_Agent_wall_seconds=agents,sum_Worker_wall_seconds=workers,
            non_Agent_code_seconds=cost['session_elapsed_seconds']-agents,worker_non_Agent_seconds=workers-agents,
            outside_Worker_seconds=cost['session_elapsed_seconds']-workers,
            setup_before_shared_entry_seconds=prepare-runtime['session_started'],shared_preflight_seconds=load-prepare,
            model_start_to_first_worker_prepare_upper_bound_seconds=first_worker-load,
            model_start_bound_includes='Model startup,health,idle checks,supervisor startup and child imports;not pure measured weight-load time',
            independent_GPU_billed_seconds=None)
    pair=[];totals={}
    for arm in ('A','B'):
        rows=[r for r in metrics['runs'] if r['arm']==arm]
        totals[arm]=dict(Agent_wall_seconds=sum(r['Agent_wall_seconds'] for r in rows),Worker_wall_seconds=sum(r['Worker_wall_seconds'] for r in rows),
            charged_tools=sum(r['charged_tools'] for r in rows),model_requests=sum(r['model_requests'] for r in rows),
            received_usage={key:sum(r['received_usage'][key] for r in rows) for key in ('prompt_tokens','completion_tokens','total_tokens')},
            explicit_submit_runs=sum(r['successful_submit'] for r in rows),post_submit_tool_calls=sum(r['post_submit_tool_calls'] for r in rows),
            repeated_successful_submits=sum(r['repeated_successful_submits'] for r in rows))
    for task in ('fastapi_9425','fastapi_14786'):
        a=next(r for r in metrics['runs'] if r['instance_id']==task and r['arm']=='A');b=next(r for r in metrics['runs'] if r['instance_id']==task and r['arm']=='B')
        pair.append(dict(instance_id=task,first_source_edit_B_minus_A_seconds=None if a['first_source_edit_seconds'] is None or b['first_source_edit_seconds'] is None else b['first_source_edit_seconds']-a['first_source_edit_seconds'],
            first_edit_interpretation='Only B edited production' if a['first_source_edit_seconds'] is None else 'B was about0.693seconds later',
            Agent_wall_B_minus_A_seconds=b['Agent_wall_seconds']-a['Agent_wall_seconds'],charged_tools_B_minus_A=b['charged_tools']-a['charged_tools'],received_total_tokens_B_minus_A=b['received_usage']['total_tokens']-a['received_usage']['total_tokens']))
    for name,value in [('AGENT_BEHAVIOR_METRICS.json',metrics),('TRAJECTORY_REVIEW.json',dict(analysis_only=True,raw_archive_sha256=sha(archive.read_bytes()),reviews=reviews)),
                       ('PAIRED_SUMMARY.json',dict(native_outcomes=dict(Both_Resolved=1,A_Only=0,B_Only=1,Neither_Resolved=0,Unknown=0),pairs=pair,arm_totals=totals)),('RESOURCE_ACCOUNTING.json',resource)]:
        (HERE/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(totals=totals,resource=resource)))

if __name__=='__main__':
    import sys
    run(sys.argv[1])
