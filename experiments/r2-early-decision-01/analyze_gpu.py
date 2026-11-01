"""Read-only recovery/metrics from the sole dispatched artifact; no model calls."""
import hashlib,json,statistics,zipfile
from pathlib import Path
D=Path(__file__).resolve().parent
def digest(b):return hashlib.sha256(b).hexdigest()
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def main():
    artifact=D/'gpu-output/r2a-real-gpu-01.zip'
    with zipfile.ZipFile(artifact) as z:
        assert z.testzip() is None
        read=lambda n:json.loads(z.read(n))
        pair=read('execution/PAIR_RESULTS.json');assert pair['complete'] and len(pair['records'])==8 and not pair['not_run']
        issues={i['instance_id']:i for i in json.loads((D/'ISSUES.agent.json').read_bytes())}
        wanted=[];rows=[]
        for record in pair['records']:
            s=record['result'];idx=record['index'];candidate=s['candidate'];task=s['task_id']
            prefix=f'execution/sessions/{idx:02d}_{candidate}_{task}/'
            raw=read(prefix+'SESSION_RESULT.json');assert raw==s
            events=[json.loads(x) for x in z.read(prefix+'events.jsonl').decode().splitlines()]
            adk=[json.loads(x) for x in z.read(prefix+'adk_events.jsonl').decode().splitlines()]
            trace=read(prefix+'native_trace.json')
            assert any(issues[task]['problem_statement'] in t.get('message','') for t in trace['steps'] if t['source']=='user')
            stages=[e for e in events if e.get('kind')=='stage' and e.get('stage')=='agent'];t0=max(e['recorded_monotonic'] for e in stages)
            first=next((e for e in events if e.get('first_production_edit_observed')),None)
            prior=[e for e in events if e.get('kind')=='production_version_observed' and (not first or e['recorded_monotonic']<first['recorded_monotonic'])]
            lower=max((e['after'] for e in prior),default=t0)-t0 if first else None
            calls=[];responses=[]
            for e in adk:
                for p in (e['event'].get('content') or {}).get('parts',[]):
                    if 'function_call' in p:calls.append(dict(t=e['recorded_monotonic']-t0,**p['function_call']))
                    if 'function_response' in p:responses.append(dict(t=e['recorded_monotonic']-t0,**p['function_response']))
            byid={r.get('id'):r for r in responses}
            for c in calls:c['response']=byid.get(c.get('id'))
            sub=[c['t'] for c in calls if c['name']=='submit_patch']
            cfg=read(prefix+'CONFIGURATION.json')
            expected={'A':'4fa5461c7d11d1e7d2e8b91c88dbd136a5daefc5dc155287234c4c735de04dff','R2':'3a543f027d43108f1d655b2379b1446ee915f9c39beb3ec7b8c61c76c5938c75'}
            assert cfg['instruction_sha256']==expected[candidate]
            patch=z.read(prefix+s['patch_kind']+'.patch');assert len(patch)==s['patch_bytes']
            assert not patch or digest(patch)==s['patch_sha256']
            native=s['evaluation']['sdk_native'];assert native['agent_patch'].encode()==patch
            dst=D/'results'/f'{idx:02d}_{candidate}_{task}'
            write(dst/'SESSION_METRICS.json',dict(index=idx,candidate=candidate,task_id=task,agent_seconds=s['agent_seconds'],worker_seconds=s['worker_seconds'],verification_seconds=native['duration_seconds'],charged_tools=s['charged_tools'],model_requests=s['http_audit']['requests'],patch_submitted=s['patch_submitted'],patch_kind=s['patch_kind'],patch_bytes=s['patch_bytes'],agent_error=s['agent_error'],first_tracked_production_edit_interval_seconds=[lower,first['after']-t0] if first else None,first_edit_timing_scope='Interval after last unchanged observation through first changed observation; no exact timestamp; tracked production Python only',submit_call_seconds=sub,sdk_native_resolved=s['sdk_native_resolved'],independent_test_pass=s['independent_test_pass'],observed_token_usage=s['http_audit']['observed_response_usage'],token_usage_complete=s['http_audit']['usage_complete'],cleanup=s['cleanup'],evidence_complete=s['evidence_complete']))
            (dst/'agent.patch').write_bytes(patch)
            write(dst/'TOOL_ACTIONS.json',calls)
            # Preserve original verdict and source guard, never rewrite raw result.
            write(dst/'NATIVE_RESULT.json',native)
            rows.append(json.loads((dst/'SESSION_METRICS.json').read_bytes()))
            endings=('.patch','adk_events.jsonl','native_trace.json','events.jsonl','SESSION_RESULT.json','CONFIGURATION.json','HTTP_EVIDENCE_AUDIT.json','.xml','SOURCE_GUARD.json','CLEANUP.json')
            wanted.extend(n for n in z.namelist() if n.startswith(prefix) and not n.endswith('/') and ('/model_transport/' in n or n.endswith(endings)))
        top=['GPU_ALLOCATION.json','ONE_TIME_RUN_MANIFEST.json','NOTEBOOK_FINAL_STATUS.json','NOTEBOOK_SUPERVISOR.json','OWNED_ROOT_RECOVERY.json','execution/PAIR_RESULTS.json','execution/MODEL_IDENTITY.json','execution/GPU_RUNTIME.json','execution/SERVER_CONFIGURATION.json','execution/MODEL_LOAD_COMPLETED.json','execution/SERVER_CLEANUP.json','execution/ENDPOINT_SCOPE.json']
        for n in top:
            write(D/'results'/'receipts'/n.replace('/','__'),read(n))
        wanted+=top
        entries=[dict(path=n,bytes=len(z.read(n)),sha256=digest(z.read(n))) for n in sorted(set(wanted))]
        write(D/'GPU_SESSION_EVIDENCE_INDEX.json',dict(artifact=str(artifact.relative_to(D)),artifact_sha256=digest(artifact.read_bytes()),artifact_bytes=artifact.stat().st_size,zip_crc_pass=True,original_entry_count=len(z.namelist()),selected_evidence=entries,raw_artifact_url='https://www.kaggle.com/code/wudangdexiaodoashi/r2a-frozen-paired-real-gpu-01/output',exclusions='CPU_evidence/replay is scripted plumbing and excluded from all eight real-session metrics. Full artifact retained locally and as private Kaggle output.'))
        write(D/'GPU_BEHAVIOR_METRICS.json',dict(rows=rows,aggregate={c:dict(agent_seconds=sum(r['agent_seconds'] for r in rows if r['candidate']==c),worker_seconds=sum(r['worker_seconds'] for r in rows if r['candidate']==c),charged_tools=sum(r['charged_tools'] for r in rows if r['candidate']==c),independent_test_passes=sum(r['independent_test_pass'] for r in rows if r['candidate']==c),explicit_submits=sum(r['patch_submitted'] for r in rows if r['candidate']==c),token_usage_complete=all(r['token_usage_complete'] for r in rows if r['candidate']==c),observed_tokens={k:sum(r['observed_token_usage'][k] for r in rows if r['candidate']==c) for k in ['prompt_tokens','completion_tokens','total_tokens']}) for c in ['R2','A']}))
        print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
