import asyncio
from dataclasses import asdict
import importlib.metadata as md
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from .common import ROOT,HERE,ORDER,sha,write
from .data import prepare
from .evaluate import evaluate
from harness_v2.evidence import Journal

def file_sha(path):
    import hashlib
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for b in iter(lambda:stream.read(8388608),b''):h.update(b)
    return h.hexdigest()

async def run(out,started):
    import torch,psutil,httpx
    from adk_submission import VllmConfig,VllmServer,discover_adapters
    from harness_v2.supervisor import supervise
    from s1.experiments.e3_localize_smoke_03.idle import require_idle
    from s1.verifier_v3.backend_logs import capture_logs
    # The supervisor owns the exclusive controller_started.json claim and
    # creates this directory before starting us. Accept that fresh directory.
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    assert not (out/'PAIR_RESULTS.json').exists(),'Do not overwrite an earlier study'
    journal=Journal(out)
    runtime=json.loads((HERE/'GPU_ENVIRONMENT_LOCK.json').read_bytes())
    results=[];server=None;known=[];completed=False
    try:
        journal.stage('prepare_agent')
        assert sys.platform=='linux' and sys.version_info[:2]==(3,12)
        devices=[dict(name=torch.cuda.get_device_name(i),memory=torch.cuda.get_device_properties(i).total_memory) for i in range(torch.cuda.device_count())]
        assert len(devices)==4 and all(d['name']=='NVIDIA L4' for d in devices)
        versions={n:md.version(n) for n in runtime['versions']}
        write(out/'GPU_RUNTIME.json',dict(devices=devices,versions=versions,CUDA=torch.version.cuda,Python=sys.version))
        assert versions==runtime['versions'] and torch.version.cuda=='12.8'
        models=[p.parent for p in Path('/kaggle/input').rglob('config.json') if
            'gemma-4-31b-it-qat-w4a16-ct' in p.parts and p.parent.name=='2' and (p.parent/'model.safetensors').is_file()]
        assert len(models)==1;model=models[0]
        assets={p.relative_to(model).as_posix():file_sha(p) for p in model.rglob('*') if p.is_file()}
        assert assets==runtime['model_files']
        write(out/'MODEL_IDENTITY.json',dict(model_path=str(model),source=runtime['model_source'],files=assets))
        data=prepare(out/'data')
        for ident,binding in data.items():
            row=evaluate(binding,out/'baseline'/ident)
            assert row['target_failed'] and row['positive_controls_passed'] and row['cleanup'],ident
        os.environ.update(VLLM_WORKER_MULTIPROC_METHOD='spawn',VLLM_NO_USAGE_STATS='1',VLLM_ENGINE_READY_TIMEOUT_S='1200',
            VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS='1',NCCL_DEBUG='WARN',PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True',
            LOCAL_API_KEY='EMPTY',OPENAI_API_KEY='EMPTY')
        empty=out/'no_adapters';empty.mkdir()
        config=VllmConfig(model=str(model),**runtime['VllmConfig'])
        server=VllmServer(config,adapter_manifest=discover_adapters(str(empty)))
        write(out/'SERVER_CONFIGURATION.json',dict(config=asdict(config),command=server.build_cmd(),
            generation_probes_outside_sessions=0,context_policy='Pinned guide compaction15/overlap2/threshold14336/retain5 for both arms',
            historical_serving_equivalence='UNVERIFIED'))
        journal.stage('load_model');begin=time.monotonic();server.start()
        write(out/'MODEL_LOAD_COMPLETED.json',dict(seconds=time.monotonic()-begin))
        known=[psutil.Process(server.process.pid)]+psutil.Process(server.process.pid).children(recursive=True)
        async with httpx.AsyncClient(trust_env=False,timeout=30) as client:
            r=await client.get(server.base_url+'/models');r.raise_for_status();write(out/'SERVED_MODELS.json',r.json())
            assert str(model) in {m['id'] for m in r.json()['data']}
        for index,(ident,name) in enumerate(ORDER):
            # Reserve full remaining schedule before starting each independent worker.
            remaining=sum((480 if n=='SUPERAGENT' else 300)+240 for _,n in ORDER[index:])+300
            elapsed=time.monotonic()-started
            assert 10800-elapsed>=remaining,'Insufficient complete remaining study window'
            await require_idle(server.base_url,out/f'idle_before_{index+1}',seconds=60)
            journal.stage('session_'+str(index+1))
            spec=dict(binding=data[ident],candidate=name,model_path=str(model),real_Gemma=True)
            specfile=out/'specs'/f'{index+1}.json';write(specfile,spec)
            directory=out/'sessions'/f'{index+1:02d}_{name}_{ident}'
            print('PAIRED_SESSION_START',index+1,ident,name,flush=True)
            seconds=480 if name=='SUPERAGENT' else 300
            outcome=await asyncio.to_thread(supervise,[sys.executable,'-m','gemma_pair.worker',str(specfile),str(directory)],directory,
                outer_seconds=seconds+600,stage_caps=dict(prepare_agent=240,agent=seconds+45,save_patch=60,
                    verification=240,persist=60,cleanup=120),cwd=ROOT)
            row=json.loads((directory/'SESSION_RESULT.json').read_bytes()) if (directory/'SESSION_RESULT.json').exists() else None
            results.append(dict(index=index+1,task=ident,candidate=name,worker=outcome,result=row))
            write(out/'PAIR_RESULTS.json',dict(records=results,not_run=ORDER[len(results):]))
            assert outcome['allow_next_run'] and row is not None,'Worker integrity/cleanup failure; stop admission'
            await require_idle(server.base_url,out/f'idle_after_{index+1}',seconds=60)
            print('PAIRED_SESSION_END',index+1,json.dumps(dict(submitted=row['patch_submitted'],patch_bytes=row['patch_bytes'],
                  scoped_pass=row['evaluation'].get('scoped_development_pass'),agent_seconds=row['agent_seconds'])),flush=True)
        completed=True
    except BaseException as exc:
        write(out/'STOP.json',dict(type=type(exc).__name__,reason=str(exc),traceback=traceback.format_exc(),records=len(results)))
        raise
    finally:
        journal.stage('cleanup');clean=True
        if server is not None:
            try:capture_logs(server,out/'backend_logs',phase='before_stop')
            finally:server.stop();capture_logs(server,out/'backend_logs',phase='after_stop')
            psutil.wait_procs(known,timeout=10)
            live=[]
            for p in known:
                try:
                    if p.is_running() and p.status()!=psutil.STATUS_ZOMBIE:p.kill()
                except psutil.NoSuchProcess:pass
            psutil.wait_procs(known,timeout=5)
            for p in known:
                try:
                    if p.is_running() and p.status()!=psutil.STATUS_ZOMBIE:live.append(p.pid)
                except psutil.NoSuchProcess:pass
            clean=not live;write(out/'SERVER_CLEANUP.json',dict(complete=clean,live=live))
        write(out/'PAIR_RESULTS.json',dict(records=results,not_run=ORDER[len(results):],complete=completed and clean,
              scoped_development_only=True,official_native_resolved=None,canonical_swebench_resolved=None,
              first_cell_elapsed_seconds=time.monotonic()-started))
        if completed and clean:write(out/'worker_done.json',dict(cleanup_complete=True))

if __name__=='__main__':asyncio.run(run(sys.argv[1],float(sys.argv[2])))
