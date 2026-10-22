"""Read local capabilities/official source and rank existing metadata only.

Never creates a container, Notebook, task baseline, model or inference request.
"""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
PARENT=HERE.parent


def sha(raw):return hashlib.sha256(raw).hexdigest()


def save(name,value):
    with (HERE/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False)


def source_audit():
    wheel=ROOT.parent/'gemma4-swe-agent/artifacts/harness-v2/official-wheels/swegemma-0.2.11-py3-none-any.whl'
    pins=json.loads((ROOT/'u_re/v01/experiments/gemma_smoke_01/SMOKE_PLAN.json').read_text(encoding='utf-8'))
    assert sha(wheel.read_bytes())==pins['official_wheels'][wheel.name]
    result={}
    with zipfile.ZipFile(wheel) as z:
        for name in ('docker','subprocess'):
            path='swegemma/sandbox/'+name+'.py';raw=z.read(path);tree=ast.parse(raw.decode())
            cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in ('ContainerManager','SubprocessManager'))
            methods={n.name:n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
            facts=dict(wheel_name=wheel.name,wheel_sha256=sha(wheel.read_bytes()),member=path,member_sha256=sha(raw),
                methods={k:dict(line=methods[k].lineno,end_line=methods[k].end_lineno) for k in ('start','exec')})
            if name=='docker':
                calls=[n for n in ast.walk(methods['start']) if isinstance(n,ast.Call)
                       and isinstance(n.func,ast.Attribute) and n.func.attr=='run']
                assert len(calls)==1
                kwargs={k.arg for k in calls[0].keywords}
                facts.update(start_keyword_names=sorted(kwargs),explicit_host_mount_argument=bool(kwargs & {'volumes','mounts'}),
                    actual_daemon_defaults_or_image_contents_verified=False,
                    network_config_source='ContainerConfig.network_mode defaults to none; must inspect actual HostConfig',
                    status='OFFICIAL_REUSE_CANDIDATE_NOT_DEPLOYMENT_PROOF')
            else:
                calls=[n for n in ast.walk(methods['exec']) if isinstance(n,ast.Call)
                    and isinstance(n.func,ast.Name) and n.func.id=='execute_subprocess_command']
                assert len(calls)==1
                facts.update(exec_keyword_names=sorted(k.arg for k in calls[0].keywords),
                    status='Host subprocess with rewritten paths/venv; no demonstrated mandatory filesystem boundary')
            result[name]=facts
    for path in ('harness_v2/official.py','s1/worker.py','s1/verifier_v3/environment.py',
                 'u_re/v01/experiments/gemma_smoke_01/S2_REUSE_BINDINGS.json'):
        result[path]=dict(sha256=sha((ROOT/path).read_bytes()))
    save('SOURCE_AUDIT.json',result)


def local_capabilities():
    wsl=shutil.which('wsl')
    record=dict(platform=sys.platform,python=sys.version,tools={n:shutil.which(n) is not None
        for n in ('docker','podman','bash','unshare','bwrap','runsc')},
        docker_python_module=importlib.util.find_spec('docker') is not None,
        DockerHost_environment_present=bool(os.environ.get('DOCKER_HOST')),
        docker_named_pipe_present=os.path.exists(r'\\.\pipe\docker_engine'),
        Kaggle_Docker_or_proxy='NOT_TESTED',Kaggle_uid_caps_namespaces='NOT_TESTED',
        local_actual_official_Linux_tool_canary='NOT_RUN')
    if wsl:
        r=subprocess.run([wsl,'--list','--quiet'],capture_output=True,timeout=20)
        raw=r.stdout+r.stderr
        text=raw.decode('utf-16-le',errors='replace').strip('\ufeff\x00\r\n')
        record['WSL']=dict(returncode=r.returncode,output=text,raw_output_sha256=sha(raw),
            interpretation='WSL_NOT_INSTALLED' if '未安装' in text else 'REQUIRES_REVIEW')
    save('LOCAL_CAPABILITIES.json',record)


def metadata_freeze():
    from u_re.v01.experiments.action_priority_01.selection import rank,MAX_CPU_CHECKS,PREFIX
    oldpath=ROOT/'u_re/v01/experiments/mechanism_02/EXCLUSION_LEDGER_V02.json'
    poolpath=ROOT/'u_re/v01/experiments/mechanism_02/TASK_POOL_METADATA.json'
    pilotpath=ROOT/'u_re/v01/experiments/fastapi_pilot_01/RANKED_POOL.json'
    ledger=json.loads(oldpath.read_text(encoding='utf-8'));pool=json.loads(poolpath.read_text(encoding='utf-8'))['rows']
    ranked_pilot=json.loads(pilotpath.read_text(encoding='utf-8'))['rows']
    inherited=set(ledger['excluded_task_ids']);assert len(inherited)==79 and len(pool)==129
    # Previous Pilot can evaluate at most its first8 IDs (no repository skips).
    # Keep those prospective/unknown-save identities reserved; catalog membership
    # of the other42 alone is not model exposure or an exclusive reservation.
    reserved={row['instance_id'] for row in ranked_pilot[:8]}
    assert 'fastapi_14262' in reserved
    excluded=inherited|reserved
    rows=rank(pool,inherited,excluded)
    extra=[dict(instance_id=i,reason='Prior Pilot first8 prospective screening/CPU01-unknown reservation;14262 additionally observed rule-development failure',
        evidence=pilotpath.relative_to(ROOT).as_posix(),model_executed='NO_RECORDED_NEW_MODEL_RUN',
        reference_exposure='UNKNOWN',reservation_released=False) for i in sorted(reserved-inherited)]
    sources=[oldpath,poolpath,pilotpath,
        ROOT/'u_re/v01/experiments/fastapi_pilot_01/SELECTION_PROTOCOL.json',
        ROOT/'u_re/v01/experiments/fastapi_pilot_01/attempts/cpu02/reconciliation_01/TASK_SCREENING_LEDGER.json',
        ROOT/'u_re/v01/experiments/gemma_smoke_01/TASK_IDENTITY.json',
        PARENT/'EXPERIMENT_PROTOCOL_DRAFT.json',PARENT/'selection.py']
    candidates=[dict(row,rank=n,sort_sha256=sha((PREFIX+row['instance_id']).encode()),
        admission='NOT_ADMITTED',baseline='NOT_RUN',snapshot_sha256=None,evaluator_overlay_sha256=None)
        for n,row in enumerate(rows,1)]
    save('TASK_POOL_FREEZE.json',dict(experiment_id='U-RE-V01-ACTION-FIRST-01',
        status='STATIC_ORDER_ONLY_NOT_ADMITTED',pool_count=len(pool),inherited_exclusion_count=len(inherited),
        excluded_ids=sorted(excluded),refreshed_exclusion_count=len(excluded),inherited_entries=ledger['entries'],
        added_reservations=extra,ranking_prefix=PREFIX,ranked_count=len(candidates),ranked_rows=candidates,
        next_max8_in_order=candidates[:MAX_CPU_CHECKS],max_checks=MAX_CPU_CHECKS,
        selected_qualified_tasks=[],CPU_checks_run=0,read_reference_or_test_content=False,
        source_sha256={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in sources},
        source_scope='Current PR19 tree retains PR9–18 registrations;79ledger already audits PR1–10. Later Pilot first8 preserved,14262 analyzed,14492 engineering-only. No new real task exposure in PR18/19 synthetic sessions.',
        uncertainty='No claim about pretraining/unrecorded work. Broader exclusive reservation conflicts must STOP before CPU; this static snapshot never releases reservations.'))


if __name__=='__main__':
    source_audit();local_capabilities();metadata_freeze()
