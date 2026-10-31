"""One authorized R12 execution: observed allocation gates an ephemeral manifest."""
import asyncio,hashlib,json,re,subprocess,sys,time,traceback,zipfile
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for b in iter(lambda:stream.read(8388608),b''):h.update(b)
    return h.hexdigest()

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,default=str)+'\n')

def observe_allocation(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);evidence=dict(status='GPU_ALLOCATION_FAILED',model_loaded=False)
    try:
        for key,args in [('list',['nvidia-smi','-L']),('memory',['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'])]:
            r=subprocess.run(args,capture_output=True,text=True,timeout=30)
            evidence[key]=dict(command=args,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr)
            assert r.returncode==0
        rows=[r.strip() for r in evidence['memory']['stdout'].splitlines() if r.strip()]
        assert len(rows)==4 and all(r.split(',')[0].strip()=='NVIDIA L4' and re.search(r',\s*[1-9][0-9]*\s*MiB',r) for r in rows)
        assert len([r for r in evidence['list']['stdout'].splitlines() if r.startswith('GPU ')])==4
        import torch
        evidence['torch_count']=torch.cuda.device_count();assert evidence['torch_count']==4
        devices=[]
        for i in range(4):
            p=torch.cuda.get_device_properties(i)
            with torch.cuda.device(i):
                free,total=torch.cuda.mem_get_info(i)
                check=torch.zeros(1,device='cuda:'+str(i));torch.cuda.synchronize(i);assert check.item()==0;del check
            devices.append(dict(index=i,name=p.name,memory_bytes=p.total_memory,free_bytes=free,total_bytes=total,CUDA_accessible=True))
        assert all(d['name']=='NVIDIA L4' and d['memory_bytes']>0 for d in devices)
        evidence.update(status='GPU_ALLOCATION_CONFIRMED',devices=devices,observed_monotonic=time.monotonic())
    except BaseException as e:evidence.update(error_type=type(e).__name__,error=str(e))
    write(out/'GPU_ALLOCATION.json',evidence)
    (out/evidence['status']).write_text(evidence['status']+'\n')
    return evidence

def validate(original,authorization,package,extension,allocation):
    original=Path(original);authorization=Path(authorization);extension=Path(extension)
    m=json.loads(original.read_bytes());a=json.loads(authorization.read_bytes())
    assert a['study']=='gemma-r12-01' and a['explicit_user_GPU_authorization'] is True
    assert a['maximum_dispatches']==1 and a['maximum_node_seconds']==18000 and not a['formal_submission_authorized']
    assert sha(original)==a['original_manifest_sha256'] and sha(package)==a['dispatch_zip_sha256']==m['CPU_dispatch_archive_sha256']
    assert sha(__file__)==a['authorized_wrapper_sha256']
    assert sha(extension/'RESOURCE_READINESS.original.json')==a['original_resource_readiness_sha256']
    assert m['gate']=='R12_RESOURCE_BLOCKED' and allocation['status']=='GPU_ALLOCATION_CONFIRMED'
    assert a['quota_admission']['available_seconds_after_reservations']>=73200
    for name,h in m['CPU_rehearsal_build']['extension_sha256'].items():
        p=extension.parent/'source'/name.removeprefix('source-overlay/') if name.startswith('source-overlay/') else extension/name
        assert sha(p)==h,name
    assert a['candidate_zip_sha256']==m['candidate_zip_sha256']
    assert a['sessions']==[[r['instance_id'],r['candidate']] for r in m['sessions']]
    assert all(r['agent_limit_seconds']==480 and r['charged_tool_limit']==28 and r['max_turns']==80 and r['command_timeout_seconds']==240 for r in m['sessions'])
    assert m['configuration']['temperature']==.2 and m['configuration']['top_p']==.95 and m['configuration']['max_output_tokens']==8192
    assert m['configuration']['thinking_budget']==4096 and m['configuration']['include_thoughts'] is True and not m['configuration']['prefix_cache'] and not m['configuration']['LoRA']
    return m,a

def strict_admission(row,supervisor):
    if not supervisor['allow_next_run'] or row is None:return 'STOP_INFRASTRUCTURE'
    if row.get('evidence_complete') is not True:return 'STOP_EVIDENCE'
    if not row.get('cleanup'):return 'STOP_CLEANUP'
    error=str(row.get('agent_error') or '')
    if re.search(r'context_length|context.window|ContextBudget|ContextCounting|ContextWindow|litellm\.|OpenAIException|connection.error|service.unavailable|CUDA|out of memory',error,re.I):return 'STOP_BACKEND_COMPATIBILITY'
    e=row.get('evaluation') or {}
    if not e.get('cleanup'):return 'STOP_CLEANUP'
    # A model-produced inapplicable patch is an ordinary repair failure.
    if e.get('patch_applicable') is False:return 'CONTINUE'
    if not e.get('check_unchanged') or not e.get('check_write_denied') or not e.get('source_unchanged_by_checks'):return 'STOP_TRUST'
    if not e.get('positive_controls_passed'):return 'STOP_ENVIRONMENT'
    return 'CONTINUE'

def recover_owned(execution):
    from egrd.v0311.lifecycle import release_owned
    from u_re.v01.experiments.action_priority_01.integrated_cpu_01.CHROOT_TASK_RUNTIME import kill_owned
    execution=Path(execution).resolve();records=[]
    for registry in execution.rglob('owned_uids.json'):
        assert not registry.is_symlink() and registry.resolve().is_relative_to(execution)
        data=json.loads(registry.read_bytes());assert data['kind']=='URE_OWNED_UID_REGISTRY_V1'
        for entry in data['entries']:
            root=Path(entry['root']);lease=Path(entry['lease'])
            assert root.resolve().parent==registry.parent.resolve() and not root.is_symlink()
            assert lease==Path('/tmp/ure_owned_uid_leases')/str(entry['uid'])
            if lease.exists():records.append(release_owned(entry,registry.parent,kill_owned))
            else:assert not root.exists(),'Residual owned root without lease'
    return dict(complete=True,records=records)

async def run(original,authorization,package,out,first_started):
    from unittest.mock import patch
    import r12_final_cpu,r12_coordinator
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    extension=Path(__file__).parent;allocation=json.loads((out.parent/'GPU_ALLOCATION.json').read_bytes())
    m,a=validate(original,authorization,package,extension,allocation)
    runtime=dict(m,gate='R12_GPU_READY',dispatch_authorized=True,one_time_execution=True,
        original_manifest_sha256=sha(original),authorization_receipt_sha256=sha(authorization),
        allocation_evidence_sha256=sha(out.parent/'GPU_ALLOCATION.json'),actual_allocation=allocation)
    runtime_path=out.parent/'ONE_TIME_RUNNING_MANIFEST.json'
    with runtime_path.open('x') as f:json.dump(runtime,f,indent=2)
    before=sha(original)
    try:
        with patch.object(r12_final_cpu,'admission',strict_admission):
            await r12_coordinator.run(runtime_path,package,out,authorization,first_started)
    finally:
        assert sha(original)==before,'Original frozen manifest changed'

if __name__=='__main__':
    try:asyncio.run(run(*sys.argv[1:]))
    except BaseException as e:
        write(Path(sys.argv[4]).parent/'AUTHORIZED_EXECUTION_STOP.json',dict(type=type(e).__name__,reason=str(e),traceback=traceback.format_exc()))
        raise
