"""CPU-only prospective screening. No Agent/model/reference repair or test edits."""
import asyncio
import hashlib
import json
from pathlib import Path
import re
import sys
import time

from harness_v2.evidence import Journal,atomic_json
from s1.task_identity import find_data,identify

HERE=Path(__file__).resolve().parent


def source_hashes(workspace):
    return {p.relative_to(workspace).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(workspace.rglob('*')) if p.is_file()
        and not {'.git','__pycache__','.pytest_cache'}.intersection(p.relative_to(workspace).parts)
        and '.egg-info' not in str(p)
        and (p.suffix=='.py' or p.name in ('pyproject.toml','pytest.ini','setup.cfg','tox.ini') or p.name.startswith('requirements'))}


def decide(audit,*,evidence_ok):
    if not evidence_ok:return 'STOP','evidence_identity_or_cleanup_failure'
    if audit['category']=='assertion_failure' and not audit['infrastructure_stop']:
        return 'ELIGIBLE','native_behavior_failure_without_setup_collection_errors'
    if audit['category']=='passed' and not audit['infrastructure_stop']:
        return 'REJECT','all_passing_base_not_discriminating'
    events=audit.get('events',[])
    errors=[e for e in events if e.get('category') in ('setup_error','collection_error','internal_error','unknown_unparsed')]
    if errors and all(e['category']=='setup_error' and re.search(r"recursive dependency involving fixture '(?:httpbin|httpbin_secure)'",e.get('details','')) for e in errors):
        return 'REJECT','known_pytest_httpbin_dependency_block_PR10_no_repeat_investigation'
    # No broad ERROR/stdout regex and no generic unexplained-error skipping.
    # ModuleNotFoundError is only a candidate explanation. Preserve a global
    # stop unless this version has direct independent dependency evidence.
    return 'STOP','unexplained_or_unsupported_native_environment_error'


def provenance(directory,prefix,workspace):
    records=[];paths=[]
    for p in (directory/'import_audit').rglob('*.json'):
        record=json.loads(p.read_text())
        if record.get('stage')!='exit':continue
        entry=record.get('modules',{}).get(prefix,{})
        file=entry.get('realpath')
        if not file:continue
        within=Path(file).is_relative_to(workspace)
        executed=any(x.get('filename')==file or str(Path(x.get('filename','')).resolve())==file for x in record.get('executed_modules',[]))
        rows=dict(record=str(p.relative_to(directory)),pid=record['pid'],sys_path=record['sys_path'],
                  target_module=prefix,file=file,source_sha256=entry.get('source_sha256'),within_workspace=within,module_code_executed=executed)
        records.append(rows)
        if within and executed:paths.append(file)
    return dict(verified=bool(paths),records=records,scope='Module execution provenance, not proof that all Issue behavior is covered')


async def run(output):
    import torch,psutil
    assert sys.platform=='linux' and torch.cuda.device_count()==0
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.models import load_tasks
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.verification import verify_task
    from s1.verifier_v3.environment import SubprocessManager as Observed,research_environment
    from s1.verifier_v3.audit import audit_verifier
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    protocol=json.loads((HERE/'SELECTION_PROTOCOL.json').read_text())
    ranked=json.loads((HERE/'RANKED_POOL.json').read_text())['rows']
    assert protocol['execution']==dict(execute=False,gpu_authorized=False,formal_submission=False,Agent_runs=0,model_calls=0)
    data=find_data();tasks={t.instance_id:t for t in load_tasks(data/'tasks.jsonl')}
    for row in ranked:
        t=tasks[row['instance_id']]
        assert t.repo==row['repo'] and t.base_commit==row['base_commit']
        assert hashlib.sha256(t.problem_statement.encode()).hexdigest()==row['issue_sha256']
    source_protocol=hashlib.sha256((HERE/'SELECTION_PROTOCOL.json').read_bytes()).hexdigest()
    selected=[];rows=[];checked=0;stopped=None
    for row in ranked:
        item=dict(row,exclusion_check=True,cpu_entered=False,status='NOT_RUN')
        if stopped or len(selected)==2 or checked>=protocol['selection_algorithm']['max_cpu_checks']:
            item['reason']=stopped or ('selection_complete' if len(selected)==2 else 'max8_checks_reached');rows.append(item);continue
        if row['repo'] in {s['repo'] for s in selected}:
            item.update(status='SKIPPED_REPOSITORY_ALREADY_SELECTED',reason='Predeclared diversity skip; no CPU result observed')
            rows.append(item);continue
        checked+=1;ident=row['instance_id'];directory=output/f'{checked:02d}-{ident}'
        directory.mkdir();item.update(cpu_entered=True,check_number=checked,evidence=directory.name)
        atomic_json(directory/'task_identity.json',identify(data,[ident])[ident])
        task=tasks[ident];snapshot,base,overlay=resolve_task_snapshot_paths(data/'snapshots',ident,task.repo)
        prefix=task.repo.split('/')[-1];journal=Journal(directory)
        class SubprocessManager(Observed):
            def exec(self,sid,command,*,timeout=None):
                if ' -m pytest ' in command and not (directory/'before_pytest_files.json').exists():
                    atomic_json(directory/'before_pytest_files.json',source_hashes(self.sandboxes[sid]['workspace']))
                return super().exec(sid,command,timeout=timeout)
            def stop(self,sid):
                if sid in self.sandboxes and sid in self.junit_paths:
                    workspace=self.sandboxes[sid]['workspace'].resolve()
                    atomic_json(directory/'after_pytest_files.json',source_hashes(workspace))
                    atomic_json(directory/'source_provenance.json',provenance(directory,prefix,workspace))
                return super().stop(sid)
        manager=SubprocessManager(journal=journal,base_dir=directory/'sandbox_tmp',audit_modules=[prefix],task_wheels=data/'wheels',timeout_seconds=120)
        manager.agent_id='evaluator_only_no_agent'
        config=EvalConfig(tasks_path=data/'tasks.jsonl',snapshots_dir=data/'snapshots',results_dir=directory/'unused_native',
            submission_dir=HERE.parents[1]/'candidate_noegv',models=ModelRegistry(),sandbox='subprocess',wheels_dir=data/'wheels',
            verification_timeout_seconds=300,enable_sandbox_testing=True,display_mode='quiet')
        # Capture actual implementation identities separately from historical claims.
        import inspect
        if not (output/'official_source_hashes.json').exists():
            import importlib
            names=['swegemma.harness.verification','swegemma.harness.container_setup','swegemma.sandbox.subprocess']
            atomic_json(output/'official_source_hashes.json',{n:hashlib.sha256(Path(inspect.getfile(importlib.import_module(n))).read_bytes()).hexdigest() for n in names})
        initial={p.pid for p in psutil.Process().children(recursive=True)}
        started=time.monotonic();result=None
        try:
            with research_environment(audit_modules=[prefix],task_wheels=data/'wheels'):
                result=await verify_task(manager,config,task,snapshot,base_snapshot_path=base,patch_path=overlay,
                    agent_patch='',start_time=time.perf_counter())
            atomic_json(directory/'official_result.json',result.model_dump(mode='json',exclude={'trace'}))
        except Exception as exc:
            stopped='native_exception:'+type(exc).__name__
            atomic_json(directory/'exception.json',dict(type=type(exc).__name__,message=str(exc)))
        finally:
            manager.cleanup_all()
            children=[dict(pid=p.pid,name=p.name(),status=p.status()) for p in psutil.Process().children(recursive=True) if p.pid not in initial and p.is_running()]
            cleanup=not manager.sandboxes and not list((directory/'sandbox_tmp').glob('swegemma_sandbox_*')) and not children
            atomic_json(directory/'cleanup.json',dict(complete=cleanup,new_remaining_processes=children))
        audit=audit_verifier(directory);atomic_json(directory/'structured_verifier.json',audit)
        capture=json.loads((directory/'phase2_junit_capture.json').read_text()) if (directory/'phase2_junit_capture.json').exists() else {}
        proof=json.loads((directory/'source_provenance.json').read_text()) if (directory/'source_provenance.json').exists() else {}
        before=json.loads((directory/'before_pytest_files.json').read_text()) if (directory/'before_pytest_files.json').exists() else None
        after=json.loads((directory/'after_pytest_files.json').read_text()) if (directory/'after_pytest_files.json').exists() else None
        evidence_ok=cleanup and capture.get('status')=='captured' and before is not None and before==after
        decision,reason=decide(audit,evidence_ok=evidence_ok)
        if decision=='ELIGIBLE' and not proof.get('verified'):
            decision,reason='STOP','workspace_module_execution_provenance_missing'
        if stopped:decision,reason='STOP',stopped
        item.update(status=decision,eligible=decision=='ELIGIBLE',reason=reason,native_test_exit_code=result.test_exit_code if result else None,
            native_baseline_resolved=result.resolved if result else None,category=audit['category'],counts=audit.get('counts'),
            summary=audit.get('summary'),setup_errors=sum(e['category']=='setup_error' for e in audit.get('events',[])),
            collection_errors=sum(e['category']=='collection_error' for e in audit.get('events',[])),
            identity=json.loads((directory/'task_identity.json').read_text()),source_provenance_verified=proof.get('verified',False),
            workspace_files_unchanged=before is not None and before==after,cleanup_complete=cleanup,
            seconds=time.monotonic()-started,JUnit_sha256=capture.get('sha256'))
        summary=audit.get('summary') or {}
        item.update(passed=summary.get('passed'),failed=summary.get('failed',0),errors=summary.get('error',0),
                    skipped=summary.get('skipped',0),xfailed=summary.get('xfailed',0))
        if decision=='ELIGIBLE':selected.append(item)
        if decision=='STOP':stopped=reason
        rows.append(item)
        atomic_json(output/'TASK_SCREENING_LEDGER.json',dict(protocol_sha256=source_protocol,checked=checked,selected=selected,rows=rows,
            stop=stopped,Agent_runs=0,model_calls=0,GPU=False,screening_in_progress=True))
        print(json.dumps(dict(task=ident,decision=decision,reason=reason,counts=item.get('counts')),indent=2),flush=True)
    complete=len(selected)==2 and stopped is None
    final=dict(experiment_id='U-RE-V01-MECHANISM-02',protocol_sha256=source_protocol,checked=checked,selected=selected,rows=rows,
        stop=stopped if stopped else None if complete else 'max_checks_or_pool_exhausted_without_two_repositories',
        Agent_runs=0,model_calls=0,GPU=False,screening_in_progress=False,
        status='CPU_BASELINE_GO' if complete else 'TASK_ADMISSION_BLOCKED',GPU_authorized=False)
    atomic_json(output/'TASK_SCREENING_LEDGER.json',final)
    atomic_json(output/'cpu_gate.json',final)
    return 0


if __name__=='__main__':raise SystemExit(asyncio.run(run(sys.argv[1])))
