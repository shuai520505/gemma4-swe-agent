"""Frozen max8 native empty-patch baselines,only after real Runner CPU PASS."""
import asyncio
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import re
import sys
import time

from harness_v2.evidence import Journal,atomic_json
from s1.task_identity import find_data,identify
from u_re.v01.experiments.fastapi_pilot_01.screen import source_hashes,provenance

HERE=Path(__file__).resolve().parent


def classify(audit,evidence_ok,dependency_presence):
    if not evidence_ok:return 'STOP','identity_JUnit_source_or_cleanup_failure'
    if audit['category']=='assertion_failure' and not audit['infrastructure_stop']:
        return 'BASELINE_ELIGIBLE','native_target_assertion_failure'
    if audit['category']=='passed' and not audit['infrastructure_stop']:
        return 'NON_DISCRIMINATING','all_passing_original_base'
    bad=[e for e in audit.get('events',[]) if e.get('category') in ('setup_error','collection_error','internal_error','unknown_unparsed')]
    # Independently established missing dependency only; never interpret every
    # ModuleNotFoundError as environmental (it may be the requested new API).
    if bad and all(re.search(r"ModuleNotFoundError: No module named ['\"]inline_snapshot['\"]",e.get('details','')) for e in bad):
        if dependency_presence['inline_snapshot'] is False:return 'ENVIRONMENT_BLOCKED','known_independent_inline_snapshot_dependency_missing_PR16'
    if bad and all(re.search(r"recursive dependency involving fixture '(?:httpbin|httpbin_secure)'",e.get('details','')) for e in bad):
        return 'ENVIRONMENT_BLOCKED','known_pytest_httpbin_provider_missing_PR10'
    return 'STOP','unexplained_collection_setup_or_native_error'


async def run(output):
    import torch,psutil,importlib.util,ctypes
    assert torch.cuda.device_count()==0 and sys.platform=='linux'
    gate=json.loads((HERE/'CPU_GATE_PIN.json').read_bytes())
    raw=(HERE/'ACCEPTED_CPU_ACCEPTANCE.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==gate['CPU_ACCEPTANCE_sha256']
    assert json.loads(raw)['status']=='INTEGRATED_RUNNER_CPU_PASS'
    for name,sha in gate['accepted_execution_sources'].items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==sha,'Accepted Runner source drift'
    pool=json.loads((HERE/'TASK_POOL_FREEZE.json').read_bytes());protocol=json.loads((HERE/'PROTOCOL.json').read_bytes())
    ranked=pool['next_max8_in_order'];assert [r['instance_id'] for r in ranked]==protocol['screen_order'] and len(ranked)==8
    assert pool['max_checks']==8 and pool['selected_qualified_tasks']==[]
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.models import load_tasks
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.verification import verify_task
    from s1.verifier_v3.environment import SubprocessManager as Observed,research_environment
    from s1.verifier_v3.audit import audit_verifier
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    assert ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)==0
    atomic_json(output/'TASK_ADMISSION_LEDGER.json',dict(checked=0,selected=[],rows=[dict(r,status='NOT_RUN',eligible=None,counts=None) for r in ranked],
        stop=None,screening_in_progress=True,GPU=False,Agent_runs=0,model_calls=0))
    data=find_data();tasks={t.instance_id:t for t in load_tasks(data/'tasks.jsonl')}
    expected=json.loads((HERE/'EXPECTED_TASK_RECORDS.json').read_bytes())
    identities=identify(data,[r['instance_id'] for r in ranked])
    for ident,value in identities.items():
        for key,wanted in expected[ident].items():assert value[key]==wanted,('Task identity drift before any native check',ident,key)
    atomic_json(output/'INPUT_IDENTITIES_BEFORE_EXECUTION.json',identities)
    # Functional third-party dependency check on the accepted runtime,without
    # any real task/evaluator data or model. Fail before native screening.
    from .CHROOT_TASK_RUNTIME import SubprocessManager as Isolated
    dependency=output/'dependency_smoke';dependency.mkdir()
    runtime=Isolated(journal=Journal(dependency),base_dir=dependency/'roots',task_wheels=data/'wheels')
    sid=runtime.start()
    try:
        import shlex
        code='from fastapi import FastAPI;from fastapi.testclient import TestClient;app=FastAPI();app.get("/owned")(lambda:{"ok":True});client=TestClient(app);r=client.get("/owned");assert r.status_code==200 and r.json()=={"ok":True};print("ISOLATED_ASGI_HTTP_ASSERTION_OK")'
        execution=runtime.exec(sid,'python3 -c '+shlex.quote(code),timeout=120)
        atomic_json(dependency/'result.json',dict(exit_code=execution.exit_code,stdout=execution.stdout,stderr=execution.stderr))
        assert execution.exit_code==0 and 'ISOLATED_ASGI_HTTP_ASSERTION_OK' in execution.stdout
        # Explicitly observe successful setsid,not just an attempted call.
        daemon='import os,pathlib,time,json;\nif os.fork()==0:\n os.setsid();pathlib.Path("owned_session.json").write_text(json.dumps(dict(pid=os.getpid(),sid=os.getsid(0),pgid=os.getpgrp())));time.sleep(30)\nelse:time.sleep(30)'
        timed=await asyncio.to_thread(runtime.exec,sid,'python3 -c '+shlex.quote(daemon),timeout=2)
        marker=runtime.sandboxes[sid]['workspace']/'owned_session.json'
        observed=json.loads(marker.read_bytes());assert observed['pid']==observed['sid']==observed['pgid']
        assert timed.timed_out and not psutil.pid_exists(observed['pid'])
        marker.unlink()
        job=asyncio.create_task(asyncio.to_thread(runtime.exec,sid,'python3 -c '+shlex.quote(daemon),timeout=60))
        until=time.monotonic()+15
        while not marker.exists():
            assert time.monotonic()<until;await asyncio.sleep(.05)
        second=json.loads(marker.read_bytes());assert second['pid']==second['sid']==second['pgid']
        assert psutil.Process(second['pid']).uids().real==runtime.sandboxes[sid]['uid']
        await asyncio.to_thread(runtime.stop,sid);await job
        assert not psutil.pid_exists(second['pid'])
        atomic_json(dependency/'DETACHED_SESSION_PROOF.json',dict(timeout_session=observed,abort_session=second,
            timeout_detached_PID_gone=True,abort_detached_PID_gone=True,UID_ownership_verified=True))
    finally:runtime.cleanup_all()
    atomic_json(dependency/'cleanup.json',dict(complete=not runtime.sandboxes))
    dependency_presence={'inline_snapshot':importlib.util.find_spec('inline_snapshot') is not None}
    atomic_json(output/'dependency_presence.json',dependency_presence)
    atomic_json(output/'official_source_hashes.json',{n:hashlib.sha256(Path(inspect.getfile(importlib.import_module(n))).read_bytes()).hexdigest()
        for n in ('swegemma.harness.verification','swegemma.harness.container_setup','swegemma.sandbox.subprocess')})
    rows=[];selected=[];stop=None;checked=0
    for rank,row in enumerate(ranked,1):
        item=dict(row,rank=rank,status='NOT_RUN',eligible=None,counts=None,identity=None,reason=None)
        if stop or len(selected)==2:
            item['reason']=stop or 'first_two_eligible_selected';rows.append(item);continue
        ident=row['instance_id'];task=tasks[ident]
        assert task.repo==row['repo'] and task.base_commit==row['base_commit']
        assert hashlib.sha256(task.problem_statement.encode()).hexdigest()==row['issue_sha256']
        identity=identities[ident]
        checked+=1;directory=output/f'{rank:02d}-{ident}';directory.mkdir()
        atomic_json(directory/'task_identity.json',identity)
        snapshot,base,overlay=resolve_task_snapshot_paths(data/'snapshots',ident,task.repo)
        class SubprocessManager(Observed):
            def exec(self,sid,command,*,timeout=None):
                if ' -m pytest ' in command and not (directory/'before_pytest_files.json').exists():
                    atomic_json(directory/'before_pytest_files.json',source_hashes(self.sandboxes[sid]['workspace']))
                return super().exec(sid,command,timeout=timeout)
            def stop(self,sid):
                if sid in self.sandboxes and sid in self.junit_paths:
                    workspace=self.sandboxes[sid]['workspace'].resolve()
                    atomic_json(directory/'after_pytest_files.json',source_hashes(workspace))
                    atomic_json(directory/'source_provenance.json',provenance(directory,'fastapi',workspace))
                return super().stop(sid)
        manager=SubprocessManager(journal=Journal(directory),base_dir=directory/'sandbox_tmp',audit_modules=['fastapi'],task_wheels=data/'wheels',timeout_seconds=120)
        manager.agent_id='TRUSTED_EVALUATOR_NO_AGENT'
        config=EvalConfig(tasks_path=data/'tasks.jsonl',snapshots_dir=data/'snapshots',results_dir=directory/'unused_native',
            submission_dir=HERE.parents[2]/'candidate_noegv',models=ModelRegistry(),sandbox='subprocess',wheels_dir=data/'wheels',verification_timeout_seconds=300,enable_sandbox_testing=True,display_mode='quiet')
        started=time.monotonic();result=None;exception=None;initial={p.pid for p in psutil.Process().children(recursive=True)}
        try:
            with research_environment(audit_modules=['fastapi'],task_wheels=data/'wheels'):
                result=await verify_task(manager,config,task,snapshot,base_snapshot_path=base,patch_path=overlay,agent_patch='',start_time=time.perf_counter())
            atomic_json(directory/'official_result.json',result.model_dump(mode='json',exclude={'trace'}))
        except Exception as exc:
            import traceback
            exception=type(exc).__name__;atomic_json(directory/'exception.json',dict(type=exception,traceback=traceback.format_exc()))
        finally:
            manager.cleanup_all()
            for p in psutil.Process().children(recursive=True):
                if p.pid not in initial and p.status()==psutil.STATUS_ZOMBIE:
                    try:os.waitpid(p.pid,os.WNOHANG)
                    except ChildProcessError:pass
            children=[dict(pid=p.pid,name=p.name(),status=p.status()) for p in psutil.Process().children(recursive=True) if p.pid not in initial and p.is_running() and p.status()!=psutil.STATUS_ZOMBIE]
            cleanup=not manager.sandboxes and not list((directory/'sandbox_tmp').glob('swegemma_sandbox_*')) and not children
            atomic_json(directory/'cleanup.json',dict(complete=cleanup,new_remaining_processes=children))
        audit=audit_verifier(directory);atomic_json(directory/'structured_verifier.json',audit)
        capture=json.loads((directory/'phase2_junit_capture.json').read_bytes()) if (directory/'phase2_junit_capture.json').exists() else {}
        before=json.loads((directory/'before_pytest_files.json').read_bytes()) if (directory/'before_pytest_files.json').exists() else None
        after=json.loads((directory/'after_pytest_files.json').read_bytes()) if (directory/'after_pytest_files.json').exists() else None
        proof=json.loads((directory/'source_provenance.json').read_bytes()) if (directory/'source_provenance.json').exists() else {}
        # JUnit and TaskResult must agree,including collection failure exit2.
        summary=audit.get('summary') or {};test_failure=bool(summary.get('failed',0) or summary.get('error',0))
        verdict_consistent=result is not None and ((result.resolved is True and not test_failure) or (result.resolved is False and test_failure))
        evidence_ok=cleanup and capture.get('status')=='captured' and before is not None and before==after and verdict_consistent and exception is None
        status,reason=classify(audit,evidence_ok,dependency_presence)
        if status=='BASELINE_ELIGIBLE' and not proof.get('verified'):status,reason='STOP','workspace_execution_provenance_missing'
        item.update(status=status,eligible=True if status=='BASELINE_ELIGIBLE' else None if status=='STOP' else False,
            reason=reason,identity=identity,counts=audit.get('counts'),summary=summary,native_exit_code=result.test_exit_code if result else None,
            native_resolved=result.resolved if result else None,JUnit_sha256=capture.get('sha256'),cleanup=cleanup,workspace_files_unchanged=before is not None and before==after,
            source_provenance_verified=proof.get('verified'),seconds=time.monotonic()-started,raw_evidence=directory.name,
            setup_errors=sum(e.get('category')=='setup_error' for e in audit.get('events',[])),collection_errors=sum(e.get('category')=='collection_error' for e in audit.get('events',[])))
        if status=='BASELINE_ELIGIBLE':selected.append(item)
        if status=='STOP':stop=reason
        rows.append(item)
        atomic_json(output/'TASK_ADMISSION_LEDGER.json',dict(checked=checked,selected=selected,rows=rows,stop=stop,screening_in_progress=True,GPU=False,Agent_runs=0,model_calls=0))
        print(json.dumps(dict(task=ident,status=status,reason=reason,counts=item['counts'])),flush=True)
    final=dict(experiment_id='U-RE-V01-ACTION-FIRST-01',status='TWO_TASKS_ADMITTED' if len(selected)==2 and stop is None else 'TASK_ADMISSION_STOPPED_BY_INTEGRITY' if stop else 'TASKS_INSUFFICIENT',
        checked=checked,selected=selected,rows=rows,stop=stop,screening_in_progress=False,GPU=False,Agent_runs=0,model_calls=0,
        pool_sha256=hashlib.sha256((HERE/'TASK_POOL_FREEZE.json').read_bytes()).hexdigest(),CPU_gate=gate)
    atomic_json(output/'TASK_ADMISSION_LEDGER.json',final)
    print(final['status'],flush=True)


if __name__=='__main__':asyncio.run(run(sys.argv[1]))
