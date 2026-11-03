"""Read-only historical audit. No model, evaluator, or dispatch invocation.

Archive members, not summary verdicts, are the primary input. Missing observations
stay null. Classification is evidence inventory, not automated semantic judgment.
"""
from __future__ import annotations
import collections, datetime, hashlib, io, json, re, zipfile
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
OLD=Path('D:/kaggle/Gemma 4 Developer Agent Competition/gemma4-swe-agent')
def sha(b): return hashlib.sha256(b).hexdigest()
def dump(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def parse(b):
    try:return json.loads(b.decode('utf-8-sig'))
    except (ValueError,UnicodeError):return None
def rows(b):
    return [v for line in b.decode('utf-8-sig',errors='replace').splitlines() if isinstance(v:=parse(line.encode()),dict)]
def loc(p):
    try:return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:return p.as_posix()
def is_prod(f):
    p=f.lower().removeprefix('a/').removeprefix('b/')
    return (p.endswith(('.py','.pyi','.js','.ts','.go','.rs','.c','.h')) and
            not re.search(r'(^|/)(tests?|repro[^/]*|diagnos[^/]*|docs?|examples?|scripts?)(/|\.|$)',p)
            and not Path(p).name.startswith(('test_','repro','check_','probe','conftest')))
def utc(ts):
    try:return datetime.datetime.fromtimestamp(ts,datetime.timezone.utc).isoformat()
    except (TypeError,ValueError,OSError):return None

archives=[]; sessions=[]; excluded=[]; duplicates=[]; seen={}

def scan(p,family):
    raw=p.read_bytes(); ah=sha(raw)
    if ah in seen:
        duplicates.append({'archive':loc(p),'sha256':ah,'same_as':seen[ah]});return
    seen[ah]=loc(p)
    try:z=zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:return
    ns=z.namelist()
    archives.append({'path':loc(p),'sha256':ah,'bytes':len(raw),'family':family})
    # Do not recursively count inner ZIPs whose extracted copy is already present.
    result_names=[n for n in ns if n.endswith('/SESSION_RESULT.json')]
    if not result_names:
        result_names=[n for n in ns if n.endswith('/official_result.json') and not any(x in n for x in ['validation/','phase2-cpu/'])]
    if not result_names:
        result_names=[n for n in ns if n.endswith('/result.json') and n.startswith(('runs/','tasks/'))]
    for n in result_names:
        if any(q in n for q in ['CPU_evidence/','/baselines/','/verifier/','/trusted/']):
            excluded.append({'archive':loc(p),'member':n,'reason':'CPU replay / pre-agent baseline / nested evaluator copy'});continue
        d=parse(z.read(n))
        if not isinstance(d,dict):continue
        prefix=n.rsplit('/',1)[0]+'/'
        related=[x for x in ns if x.startswith(prefix) and not x.endswith('/')]
        def get(end,default=None):
            x=prefix+end
            return parse(z.read(x)) if x in ns else default
        conf=get('CONFIGURATION.json') or get('COMPILED_CONFIGURATION.json') or get('runtime_config.json') or {}
        # ADK/legacy trace are execution evidence, synthetic CPU traces are excluded by source selection.
        adkn=next((x for x in related if x in [prefix+'adk_events.jsonl',prefix+'agent/adk_events.jsonl']),None)
        legacy=get('incremental_trace_legacy.json') or get('agent/incremental_trace_legacy.json') or get('agent_boundary_trace_legacy.json') or {}
        trace=get('agent_boundary_trace.json') or get('native_trace.json') or get('agent/native_trace.json') or {}
        adk=rows(z.read(adkn)) if adkn else []
        calls=[]; responses=[]; usage=[]; timestamps=[]; models=set()
        for i,r in enumerate(adk):
            e=r.get('event',r); content=e.get('content') or {}
            if e.get('timestamp') is not None:timestamps.append(e['timestamp'])
            if e.get('model_version'):models.add(e['model_version'])
            u=e.get('usage_metadata')
            if isinstance(u,dict):usage.append(u)
            for part in content.get('parts',[]):
                if c:=part.get('function_call'):
                    calls.append({'tool':c.get('name'),'args_sha256':sha(json.dumps(c.get('args'),sort_keys=True).encode()),'timestamp':e.get('timestamp'),'monotonic':r.get('recorded_monotonic'),'trace_row':i+1,'id':c.get('id')})
                if c:=part.get('function_response'):
                    responses.append({'tool':c.get('name'),'id':c.get('id'),'response':c.get('response'),'trace_row':i+1})
        if not calls:
            for i,e in enumerate(legacy.get('entries',[])):
                if e.get('model'):models.add(e['model'])
                if e.get('type')=='tool_call':calls.append({'tool':e.get('tool'),'args_sha256':sha(json.dumps(e.get('args'),sort_keys=True).encode()),'timestamp':e.get('timestamp'),'elapsed_seconds':e.get('elapsed_s'),'trace_row':i+1})
        if not calls:
            # ATIF official trace fallback: each tool_calls element is one actual call.
            for st in trace.get('steps',[]):
                for c in st.get('tool_calls') or []:
                    calls.append({'tool':c.get('function_name') or c.get('name'),'trace_step':st.get('step_id'),'args_sha256':sha(json.dumps(c.get('arguments'),sort_keys=True).encode())})
        counts=dict(collections.Counter(c['tool'] for c in calls)) if calls else None
        agent=get('AGENT_RESULT.json') or get('agent/agent_result.json') or {}
        ev=d.get('evaluation') or {}
        native=ev.get('sdk_native') or (d if 'resolved' in d else None)
        if native is None:
            for end in ['official_result.json','phase2/official_result.json','trusted/NATIVE_RESULT.json']:
                a=get(end)
                if isinstance(a,dict) and 'resolved' in a:native=a;break
        # Production classification is conservative path heuristic, never semantic proof.
        patches=[]
        for x in related:
            if x.endswith(('.patch','.diff')) and not any(q in x for q in ['/candidate/','reference','gold']):
                b=z.read(x); files=sorted(set(re.findall(r'^diff --git a/(.*?) b/',b.decode(errors='replace'),re.M)))
                patches.append({'member':x,'sha256':sha(b),'bytes':len(b),'files':files,'production_paths_heuristic':[f for f in files if is_prod(f)]})
        # Keep final submitted/fallback patch distinct from transient source observations.
        source_events=[]; eventn=prefix+'events.jsonl'
        ers=rows(z.read(eventn)) if eventn in ns else []
        for i,e in enumerate(ers):
            if e.get('kind')=='production_version_observed':source_events.append({'row':i+1,**e})
        first_edit=(d.get('metrics') or {}).get('first_production_edit')
        tools=d.get('charged_tools',d.get('total_tool_calls'))
        task=d.get('task_id') or d.get('instance_id') or (native or {}).get('task_id')
        if family=='RECOVERED_egrd-v032-real-gemma-evidence-ab':task='django__django-16333'
        candidate=d.get('candidate') or conf.get('candidate') or prefix.rstrip('/').split('/')[-1]
        observed_usage=(d.get('http_audit') or {}).get('observed_response_usage') or (d.get('metrics') or {}).get('observed_usage')
        if not observed_usage and usage:
            observed_usage={k:sum(u.get(k,0) or 0 for u in usage) for k in ['prompt_token_count','candidates_token_count','total_token_count']}
        cleanup=d.get('cleanup')
        if cleanup is None:cleanup=(get('CLEANUP.json') or get('audit_result.json') or {}).get('cleanup_complete')
        sid=f'{family}/{ah[:10]}/{prefix.rstrip("/")}'
        evidence={'archive':loc(p),'archive_sha256':ah,'result_member':n,'result_sha256':sha(z.read(n)),'trace_member':adkn,'trace_sha256':sha(z.read(adkn)) if adkn else None}
        # Exact result AND trace identity deduplicates nested/archive copies without
        # merging distinct runs that happen to produce the same repair.
        key=(evidence['result_sha256'],evidence['trace_sha256'])
        prior=next((r for r in sessions if r['_key']==key),None)
        if prior:duplicates.append({'session_alias':sid,'same_as':prior['session_id']});continue
        a={'session_id':sid,'family':family,'evidence_kind':'REAL_GEMMA_OBSERVATION' if models or adk else 'EXECUTION_IDENTITY_UNCONFIRMED','task_id':task,'candidate':candidate,'commit':None,'package_sha256':None,'model':{'observed_model_ids':sorted(models),'configuration':conf},'prompt_sha256':conf.get('instruction_sha256'),'skill':{'identity':None,'load_skill_calls':counts.get('load_skill',0) if counts is not None else None,'run_skill_script_calls':counts.get('run_skill_script',0) if counts is not None else None,'activation_confirmed':False if calls and not any('skill' in (c['tool'] or '').lower() for c in calls) else None},'runtime_sha256':None,'evaluator_sha256':None,'hardware':None,'start_timestamp':None,'end_timestamp':None,'first_observed_event_utc':utc(min(timestamps)) if timestamps else None,'last_observed_event_utc':utc(max(timestamps)) if timestamps else None,'tokens_observed':observed_usage,'usage_complete':(d.get('http_audit') or {}).get('usage_complete',(d.get('metrics') or {}).get('usage_complete')),'native_token_counter_raw':(native or {}).get('total_tokens'),'tool_calls_observed':len(calls) if calls else None,'tool_counts':counts,'charged_tools':tools,'agent_seconds':d.get('agent_seconds'),'worker_seconds':d.get('worker_seconds',d.get('duration_seconds')),'agent_error':d.get('agent_error') or agent.get('error'),'patch_submitted':d.get('patch_submitted') if 'patch_submitted' in d else (bool(counts.get('submit_patch')) if counts is not None else None),'patch_bytes':d.get('patch_bytes'),'patches':patches,'first_production_edit_record':first_edit,'production_version_events':source_events,'native_resolved_raw':(native or {}).get('resolved',d.get('official_native_resolved')),'native_status_raw':(native or {}).get('status'),'native_trust':'NOT_REAUDITED' if native else 'NOT_AVAILABLE','custom_target_pass':ev.get('target_passed'),'custom_controls_pass':ev.get('positive_controls_passed'),'cleanup_raw':cleanup,'evidence':evidence,'tool_actions':calls,'tool_response_errors':[],'_key':key}
        for r in responses:
            s=json.dumps(r.get('response'))
            if re.search(r'"status"\s*:\s*"error"|"error_type"|"is_error"\s*:\s*true',s):
                a['tool_response_errors'].append({'tool':r['tool'],'trace_row':r['trace_row'],'response_sha256':sha(s.encode())})
        if tools is None:a['charged_tools']=agent.get('tool_calls')
        if a['agent_seconds'] is None:a['agent_seconds']=agent.get('duration_seconds')
        # Native result patches are observations even when no standalone patch survived.
        if not patches and native and isinstance(native.get('agent_patch'),str):
            b=native['agent_patch'].encode();files=sorted(set(re.findall(r'^diff --git a/(.*?) b/',native['agent_patch'],re.M)))
            patches.append({'member':n+'#agent_patch','sha256':sha(b),'bytes':len(b),'files':files,'production_paths_heuristic':[f for f in files if is_prod(f)]})
        for x in related:
            if x.endswith('/system.md') and not a['prompt_sha256']:a['prompt_sha256']=sha(z.read(x))
        # Extract exact scalar identity claims only, leaving absent/unmatched values null.
        a['legacy_trace_member']=next((x for x in related if x.endswith('incremental_trace_legacy.json')),None)
        a['legacy_trace_sha256']=sha(z.read(a['legacy_trace_member'])) if a['legacy_trace_member'] else None
        a['raw_agent_result_member']=next((x for x in related if x.endswith(('AGENT_RESULT.json','agent_result.json'))),None)
        a['first_production_edit_record']=first_edit or agent.get('first_production_edit')
        a['native_error_raw']=(native or {}).get('error_message')
        a['native_test_exit_raw']=(native or {}).get('test_exit_code')
        a['native_test_output_sha256']=sha(native['test_output'].encode()) if native and isinstance(native.get('test_output'),str) else None
        a['native_infrastructure_indicators']=sorted(set(re.findall(r'(?i)ModuleNotFoundError|ImportError|PermissionError|fixture .{0,60} not found|ERROR collecting|INTERNALERROR|ConnectionRefusedError',str((native or {}).get('test_output','')))))
        a['production_code_inspected_paths']=[]
        a['test_command_attempts']=[]
        for i,e in enumerate(legacy.get('entries',[])):
            if e.get('type')!='tool_call':continue
            ar=e.get('args') or {};fp=ar.get('filepath')
            if e.get('tool')=='read_file' and fp and is_prod(fp):a['production_code_inspected_paths'].append({'path':fp,'legacy_row':i+1,'elapsed_seconds_trace_clock':e.get('elapsed_s')})
            command=ar.get('command','')
            if re.search(r'pytest|unittest|runtests|test_|repro|sphinx-build|pylint ',command):a['test_command_attempts'].append({'command_sha256':sha(command.encode()),'legacy_row':i+1,'elapsed_seconds_trace_clock':e.get('elapsed_s'),'meaningfulness':'UNKNOWN_REQUIRES_SEMANTIC_REVIEW'})
        a['stage_timestamps']=[e for e in ers if e.get('kind')=='stage']
        a['source_edit_observation']=next((e for e in source_events if e.get('changed_files')),None)
        if a['source_edit_observation']:
            se=a['source_edit_observation'];sdk=next((e['recorded_monotonic'] for e in a['stage_timestamps'] if e.get('official_phase')=='Agent Loop'),None)
            worker=next((e['recorded_monotonic'] for e in a['stage_timestamps'] if e.get('agent_started')),None)
            a['source_edit_observation']['SDK_clock_interval_seconds']=[se['before']-sdk,se['after']-sdk] if sdk else None
            a['source_edit_observation']['late_worker_clock_interval_seconds']=[se['before']-worker,se['after']-worker] if worker else None
        # Record immutable packaged Skill identities. Their presence is not activation.
        skill_members=[x for x in related if '/skills/' in x and x.endswith(('SKILL.md','egrd.py')) and '/trusted/' not in x]
        a['skill']['identity']=[{'member':x,'sha256':sha(z.read(x))} for x in skill_members] or None
        rawcodes=[{'member':x,'sha256':sha(z.read(x))} for x in ns if x.endswith('.py') and x.startswith(('dispatched-code/','source/')) and any(k in Path(x).name for k in ['worker','coordinator','runtime','evaluator'])]
        a['runtime_members']=rawcodes
        a['runtime_sha256']=sha(json.dumps(rawcodes,sort_keys=True).encode()) if rawcodes else None
        for x in ns:
            if x.endswith(('EARLY_GPU_ALLOCATION.json','GPU_ALLOCATION_CONFIRMED.json','GPU_ALLOCATION.json')):
                obs=parse(z.read(x))
                if obs and 'L4' in json.dumps(obs):a['hardware']={'allocation_member':x,'sha256':sha(z.read(x)),'observed':obs};break
        # Store hash references to every relevant identity record, without secrets/raw prompts.
        a['identity_evidence']=[{'member':x,'sha256':sha(z.read(x))} for x in related if Path(x).name in ['CONFIGURATION.json','runtime_config.json','agent.yaml','system.md','SKILL.md','NATIVE_RESULT.json','official_result.json','CLEANUP.json','AGENT_RESULT.json']]
        sessions.append(a)

def main():
    paths=[(ROOT/'experiments/egrd-v01-12b/gpu-output/egrd-v01-12b-pilot01.zip','EGRD_SKILL_V01'),(ROOT/'work/gemma-r12-01/gpu-run02-output/gemma-r12-authorized-gpu-02.zip','R12'),(ROOT/'work/gemma-pair-01/gpu-output-v2/gemma-pair-01-gpu-v2.zip','S0_SUPERAGENT_PAIR'),(ROOT/'experiments/r2-early-decision-01/gpu-output/r2a-real-gpu-01.zip','R2_EARLY_DECISION')]
    for p in (OLD/'artifacts').rglob('*.zip'):
        s=p.as_posix().lower()
        if any(x in s for x in ['/cpu','cpu-','/s0/validation','/research-','/cure-v01/','/v1-mri/']):continue
        if any(x in s for x in ['formal-paired-01','harness-v2','cure-gpu-mechanism','kaggle-single','v1-pilot']):paths.append((p,'LEGACY_'+p.relative_to(OLD/'artifacts').parts[0]))
    for p in (OUT/'raw_recovered').rglob('*.zip'):
        if p.stat().st_size>2000:paths.append((p,'RECOVERED_'+p.parent.relative_to(OUT/'raw_recovered').parts[0]))
    for p,f in paths:
        if p.exists():scan(p,f)
    for s in sessions:s.pop('_key',None)
    dump('ARCHIVE_PROVENANCE.json',{'archives':archives,'deduplicated':duplicates,'excluded_records':excluded,'selection':'GPU source paths only; nested extracted copies deduplicated by raw result+trace hashes; CPU archives excluded from model evidence.'})
    dump('HISTORICAL_EXPERIMENT_DATASET.json',{'schema':'RESET_V1_HISTORICAL_1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'unknown_policy':'null is UNKNOWN; raw zero token counters are preserved separately, never used as observed usage','sessions':sessions,'non_session_records':[{'family':'EGRD_SKILL_V02','evidence_kind':'CPU_SCRIPTED_ONLY','real_gemma_sessions':0,'cpu_acceptance':'BLOCKED_INFRASTRUCTURE','source':'experiments/egrd-v02-entrypoint-hardening/native-recovery/NATIVE_TRUST_AUDIT.json'}]})
    print(json.dumps({'sessions':len(sessions),'by_family':dict(collections.Counter(s['family'] for s in sessions)),'archives':len(archives),'duplicates':len(duplicates)},indent=2))

if __name__=='__main__':main()
