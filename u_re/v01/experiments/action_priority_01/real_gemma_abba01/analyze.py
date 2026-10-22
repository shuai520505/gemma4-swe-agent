"""Offline actual-output analysis only;never imported by Agent/coordinator."""
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from .GPU_NOTEBOOK import HERE,ROOT

def write(name,value):(HERE/name).write_text(json.dumps(value,indent=2)+'\n')

def analyze(archive):
    archive=Path(archive);assert not archive.resolve().is_relative_to(ROOT)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        names=set(z.namelist())
        def raw(name):return z.read(name)
        def load(name,default=None):return json.loads(raw(name)) if name in names else default
        def rows(name):return [json.loads(v) for v in raw(name).splitlines() if v.strip()] if name in names else []
        lock=json.loads((HERE.parent/'integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json').read_bytes())
        results=[];metrics=[];verifiers=[]
        for frozen in lock['order']:
            prefix=f"results/runs/{frozen['run']:02d}-{frozen['instance_id']}-{frozen['arm']}/"
            native=load(prefix+'official_result.json');agent=load(prefix+'agent/agent_result.json');summary=load(prefix+'native_summary.json')
            events=rows(prefix+'agent/events.jsonl');adk=rows(prefix+'agent/adk_events.jsonl')
            http=load(prefix+'HTTP_AUDIT.json');audit=load(prefix+'audit_result.json');cleanup=load(prefix+'worker_done.json')
            calls=[];responses=[]
            for row in adk:
                for part in row.get('event',{}).get('content',{}).get('parts',[]):
                    for key,target in (('function_call',calls),('function_response',responses)):
                        if part.get(key):target.append(dict(time=row['recorded_monotonic'],**part[key]))
            starts=[e['recorded_monotonic'] for e in events if e.get('kind')=='stage' and e.get('stage')=='agent' and e.get('agent_started')]
            start=starts[0] if starts else None
            observations=[e for e in events if e.get('kind')=='source_boundary_observation' and start is not None and e['start_monotonic']>=start]
            edits=[e for e in observations if e['production_changed']]
            submits=[r for r in responses if r.get('name')=='submit_patch' and r.get('response',{}).get('status')=='ok']
            first=submits[0]['time'] if submits else None
            post=[c for c in calls if first is not None and c['time']>first]
            patch=raw(prefix+'final.patch') if prefix+'final.patch' in names else None
            state='COMPLETE' if native is not None and summary is not None and audit and audit.get('allow_next_run') else 'UNKNOWN' if prefix+'controller_started.json' in names else 'NOT_RUN'
            counts=None;junit_hash=None
            if prefix+'verifier/phase2.junit.xml' in names:
                jraw=raw(prefix+'verifier/phase2.junit.xml');cases=list(ET.fromstring(jraw).iter('testcase'))
                counts=dict(tests=len(cases),failures=sum(c.find('failure') is not None for c in cases),errors=sum(c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases))
                junit_hash=hashlib.sha256(jraw).hexdigest()
            identity=dict(**frozen,status=state,resolved=native.get('resolved') if native else None,patch_sha256=hashlib.sha256(patch).hexdigest() if patch is not None else None,
                patch_bytes=len(patch) if patch is not None else None,cleanup=cleanup,agent_error=agent.get('error') if agent else None)
            results.append(identity)
            verification=load(prefix+'verifier/phase2_execution.json')
            vevents=rows(prefix+'verifier/events.jsonl')
            apply_starts=[e for e in vevents if e.get('kind')=='sandbox_command_start' and e.get('command_kind')=='apply_patch']
            apply_end=None
            if apply_starts:
                found=[e for e in vevents if e.get('kind')=='sandbox_command_end' and e['recorded_monotonic']>=apply_starts[0]['recorded_monotonic']]
                if found and found[0].get('exit_code')==0:apply_end=found[0]['recorded_monotonic']
            # Exact command+unchanged production state repetitions are observable
            # proxies;they do NOT prove identical test inputs or no new evidence.
            seen_search=set();seen_test=set();search_repeats=0;test_repeats=0;test_seconds=0.0
            for call in calls:
                if call.get('name')!='run_command':continue
                cmd=(call.get('args') or {}).get('command','')
                obs=next((o for o in observations if o['mode']=='exec' and o['operation_sha256']==hashlib.sha256(cmd.encode()).hexdigest() and o['start_monotonic']>=call['time']),None)
                if not obs:continue
                key=(cmd,json.dumps(obs['before'],sort_keys=True))
                if re.search(r'(^|[;&|\s])(rg|grep|find)\s',cmd):
                    search_repeats+=int(key in seen_search);seen_search.add(key)
                if re.search(r'pytest|unittest|\bassert\b',cmd):
                    test_repeats+=int(key in seen_test);seen_test.add(key);test_seconds+=obs['end_monotonic']-obs['start_monotonic']
            metrics.append(dict(**frozen,status=state,Agent_wall_seconds=agent.get('agent_seconds') if agent else None,
                Worker_wall_seconds=audit.get('duration_seconds') if audit else None,charged_tools=agent.get('charged_tools') if agent else None,
                first_source_edit_seconds=edits[0]['end_monotonic']-start if edits else None,
                first_source_edit_interval_seconds=[edits[0]['start_monotonic']-start,edits[0]['end_monotonic']-start] if edits else None,
                edit_timing_semantics='Actual filesystem change within operation interval;timestamp is first observed upper bound,not model intent',
                first_observed_applicable_patch_seconds=apply_end-start if apply_end is not None and start is not None and patch and patch.strip() else None,
                applicable_patch_semantics='First observed successful native application of returned patch;earlier checkpoints not independently applied',
                first_locally_supported_patch_seconds=None,local_support_status='REQUIRES_TRACE_ATTRIBUTION' if native else 'NOT_RUN',
                final_nonempty_patch=bool(patch.strip()) if patch is not None else None,
                successful_submit_count=len(submits) if agent else None,successful_submit=bool(submits) if agent else None,
                first_successful_submit_seconds=first-start if first is not None and start is not None else None,
                post_submit_tool_calls=len(post) if agent else None,repeated_successful_submits=max(0,len(submits)-1) if agent else None,
                model_requests=http.get('requests') if http else None,received_usage=http.get('observed_response_usage') if http else None,
                usage_complete=http.get('usage_complete') if http else None,request_usage=http.get('rows') if http else None,
                repeated_search_proxy=search_repeats if agent else None,repeated_test_proxy=test_repeats if agent else None,
                repeated_unchanged_test_count=None,repetition_caveat='Proxy fixes command+production hashes;test/environment identity and diagnostic purpose require manual review',
                observed_agent_test_command_seconds=test_seconds if agent else None,native_verification_seconds=verification.get('duration_seconds') if verification else None,
                deadline_exhausted=(agent.get('agent_seconds',0)>=299) if agent else None,
                tool_budget_exhausted=(agent.get('charged_tools',0)>=60) if agent else None,
                HTTP_terminal_integrity=http.get('passed') if http else None))
            verifiers.append(dict(**frozen,status=state,resolved=native.get('resolved') if native else None,test_exit_code=native.get('test_exit_code') if native else None,
                counts=counts,JUnit_sha256=junit_hash,native_TaskResult_sha256=hashlib.sha256(raw(prefix+'official_result.json')).hexdigest() if native else None,
                structured_verifier=summary,raw_evidence='PRIVATE_ARCHIVE:'+prefix+'verifier/'))
        execution=load('results/EXECUTION_STATUS.json');stop=load('results/STOP.json')
        all_complete=all(r['status']=='COMPLETE' for r in results)
        if all_complete:state='REAL_GEMMA_ABBA_COMPLETE'
        elif any(r['status']=='COMPLETE' for r in results):state='REAL_GEMMA_ABBA_PARTIAL'
        else:
            reason=str(stop)
            state='GPU_BLOCKED_BY_ISOLATION' if 'runtime drift' in reason or 'CANARY' in reason else 'GPU_BLOCKED_BY_MODEL' if 'Model bytes' in reason else 'GPU_BLOCKED_BY_RUNTIME'
        write('ABBA_RESULTS.json',dict(status=state,runs=results,STOP=stop,source_archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest()))
        write('AGENT_BEHAVIOR_METRICS.json',dict(runs=metrics,missing_usage='null/unknown,never zero-imputed',analysis_only=True))
        write('NATIVE_VERIFIER_RESULTS.json',dict(runs=verifiers,ordinary_algorithm_failures_retained=True))
        write('GPU_EXECUTION_RECORD.json',dict(Notebook_id=140228050,version=1,dispatches=1,
            devices=load('results/GPU_DEVICES.json'),runtime=load('results/GPU_RUNTIME.json'),model_files=load('results/MODEL_FILES.json'),
            VLLM_config=load('results/VLLM_CONFIG.json'),isolation=load('results/isolation/result.json'),
            cleanup=load('results/SERVER_CLEANUP.json'),cost=load('results/GPU_COST.json'),STOP=stop,execution=execution,
            raw_archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),CRC_valid=True,formal_submission_requests=0))
        print(json.dumps(dict(status=state,runs=results,STOP=stop)))

if __name__=='__main__':analyze(sys.argv[1])
