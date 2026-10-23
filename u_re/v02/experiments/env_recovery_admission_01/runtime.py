"""Trusted research environment only; native Verifier/test commands unchanged."""
import ast,asyncio,hashlib,importlib.metadata as md,inspect,json,os,subprocess,sys,time
from pathlib import Path
from .dependencies import HERE,ROOT,sha

def fingerprint():
    from packaging.requirements import Requirement
    from packaging.markers import default_environment
    env=default_environment();env['extra']='';queue=['inline-snapshot','pytest','fastapi','pydantic'];seen=set();rows=[]
    while queue:
        name=queue.pop(0)
        try:d=md.distribution(name)
        except md.PackageNotFoundError:
            rows.append(dict(name=name,version=None,missing=True));continue
        key=d.metadata['Name'].lower().replace('_','-')
        if key in seen:continue
        seen.add(key);requires=[]
        for raw in d.requires or []:
            req=Requirement(raw)
            if req.marker and not req.marker.evaluate(env):continue
            actual=md.version(req.name)
            assert not req.specifier or actual in req.specifier,(key,raw,actual)
            requires.append(raw);queue.append(req.name)
        files={}
        for item in d.files or []:
            p=Path(d.locate_file(item))
            if p.is_file() and p.suffix in ('.py','.so') and '__pycache__' not in p.parts:files[str(item)]=sha(p.read_bytes())
        rows.append(dict(name=key,version=d.version,requires=requires,code_files_sha256=sha(json.dumps(files,sort_keys=True).encode())))
    return dict(Python=sys.version,Python_version=list(sys.version_info[:3]),packages=sorted(rows,key=lambda r:r['name']))

def install_extras(output):
    manifest=json.loads((HERE/'NEW_DEPENDENCIES.json').read_bytes())
    wheels=[]
    for row in manifest['packages']:
        p=HERE/'wheels'/row['filename'];assert sha(p.read_bytes())==row['sha256'];wheels.append(str(p))
    command=[sys.executable,'-m','pip','install','--no-index','--no-deps','--force-reinstall']+wheels
    result=subprocess.run(command,capture_output=True,text=True,timeout=180)
    from harness_v2.evidence import atomic_json,atomic_bytes
    atomic_json(Path(output)/'DEPENDENCY_INSTALL.json',dict(command=command,exit_code=result.returncode,network=False,packages=manifest['packages']))
    atomic_bytes(Path(output)/'dependency.stdout.log',result.stdout.encode());atomic_bytes(Path(output)/'dependency.stderr.log',result.stderr.encode())
    assert result.returncode==0,'Fixed offline dependency installation failed'
    for row in manifest['packages']:assert md.version(row['name'])==row['version']
    return fingerprint()

async def native(data,ident,output,expected):
    """One genuine original empty-patch verify_task with durable raw capture."""
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.models import load_tasks
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.verification import verify_task
    from s1.task_identity import identify
    from s1.verifier_v3.environment import SubprocessManager as Observed,research_environment
    from .junit_audit import audit_verifier
    from u_re.v01.experiments.fastapi_pilot_01.screen import source_hashes,provenance
    from harness_v2.evidence import atomic_json
    import psutil
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    identity=identify(data,[ident])[ident]
    for key,value in expected.items():assert identity[key]==value,('Task identity drift',ident,key)
    atomic_json(output/'task_identity.json',identity)
    tasks={t.instance_id:t for t in load_tasks(data/'tasks.jsonl')};task=tasks[ident]
    class SubprocessManager(Observed):
        def exec(self,sid,command,*,timeout=None):
            if ' -m pytest ' in command and not (output/'before.json').exists():
                w=self.sandboxes[sid]['workspace'];atomic_json(output/'before.json',source_hashes(w))
                originals={}
                for rel in ('fastapi/exceptions.py','fastapi/params.py','fastapi/param_functions.py','fastapi/_compat/__init__.py','requirements-tests.txt','requirements.txt','pyproject.toml'):
                    p=w/rel
                    if p.is_file():originals[rel]=dict(sha256=sha(p.read_bytes()),text=p.read_text())
                atomic_json(output/'PRIVATE_BASE_SOURCE.json',originals)
                probe='import json,sys,importlib.metadata as m;names='+repr(['inline-snapshot','asttokens','executing','pytest','rich','pydantic','fastapi'])+';d={};\nfor n in names:\n try:d[n]=m.version(n)\n except m.PackageNotFoundError:d[n]=None\nprint(json.dumps(dict(Python=sys.version,versions=d)))'
                import shlex
                p=super().exec(sid,'python3 -c '+shlex.quote(probe),timeout=30)
                assert p.exit_code==0
                atomic_json(output/'INTERPRETER.json',json.loads(p.stdout.strip().splitlines()[-1]))
            return super().exec(sid,command,timeout=timeout)
        def stop(self,sid):
            if sid in self.sandboxes and sid in self.junit_paths:
                w=self.sandboxes[sid]['workspace'];atomic_json(output/'after.json',source_hashes(w));atomic_json(output/'provenance.json',provenance(output,'fastapi',w))
                # Missing metadata is evidence only when actually queried in the
                # same sandbox interpreter, never because a dict key is absent.
                log=(output/'phase2.log').read_text() if (output/'phase2.log').exists() else ''
                import re,shlex
                modules=sorted(set(re.findall(r"ModuleNotFoundError: No module named ['\"]([a-zA-Z_][\w.]*)['\"]",log)))
                mapping={'inline_snapshot':'inline-snapshot','dirty_equals':'dirty-equals','multipart':'python-multipart','python_multipart':'python-multipart','pytest_subtests':'pytest-subtests'}
                names=[mapping.get(n,n.replace('_','-')) for n in modules]
                if names:
                    code='import json,importlib.metadata as m;d={};\nfor n in '+repr(names)+':\n try:d[n]=m.version(n)\n except m.PackageNotFoundError:d[n]=None\nprint(json.dumps(dict(versions=d)))'
                    probe=super().exec(sid,'python3 -c '+shlex.quote(code),timeout=30)
                    assert probe.exit_code==0
                    atomic_json(output/'MISSING_DEPENDENCY_PROBE.json',json.loads(probe.stdout.strip().splitlines()[-1]))
            return super().stop(sid)
    from harness_v2.evidence import Journal
    manager=SubprocessManager(journal=Journal(output),base_dir=output/'roots',audit_modules=['fastapi'],task_wheels=data/'wheels')
    manager.agent_id='TRUSTED_EVALUATOR_NO_AGENT'
    config=EvalConfig(tasks_path=data/'tasks.jsonl',snapshots_dir=data/'snapshots',results_dir=output/'unused',submission_dir=ROOT/'u_re/v01/candidate_noegv',models=ModelRegistry(),sandbox='subprocess',wheels_dir=data/'wheels',verification_timeout_seconds=300,enable_sandbox_testing=True,display_mode='quiet')
    snapshot,base,overlay=resolve_task_snapshot_paths(data/'snapshots',ident,task.repo)
    initial={p.pid for p in psutil.Process().children(recursive=True)};started=time.monotonic();result=None;error=None
    try:
        with research_environment(audit_modules=['fastapi'],task_wheels=data/'wheels'):
            result=await verify_task(manager,config,task,snapshot,base_snapshot_path=base,patch_path=overlay,agent_patch='',start_time=time.perf_counter())
        atomic_json(output/'official_result.json',result.model_dump(mode='json',exclude={'trace'}))
    except BaseException as exc:
        import traceback
        error=type(exc).__name__;atomic_json(output/'exception.json',dict(type=error,traceback=traceback.format_exc()))
    finally:
        manager.cleanup_all()
        for p in psutil.Process().children(recursive=True):
            if p.pid not in initial and p.status()==psutil.STATUS_ZOMBIE:
                try:os.waitpid(p.pid,os.WNOHANG)
                except ChildProcessError:pass
        remaining=[p.pid for p in psutil.Process().children(recursive=True) if p.pid not in initial and p.is_running() and p.status()!=psutil.STATUS_ZOMBIE]
        cleanup=not manager.sandboxes and not remaining
        atomic_json(output/'cleanup.json',dict(complete=cleanup,new_remaining_processes=remaining))
    audit=audit_verifier(output);atomic_json(output/'audit.json',audit)
    capture=json.loads((output/'phase2_junit_capture.json').read_bytes()) if (output/'phase2_junit_capture.json').exists() else {}
    source_ok=(output/'before.json').exists() and (output/'after.json').exists() and (output/'before.json').read_bytes()==(output/'after.json').read_bytes()
    proof=json.loads((output/'provenance.json').read_bytes()) if (output/'provenance.json').exists() else {}
    counts=audit.get('counts') or {};failure=bool(counts.get('failures') or counts.get('errors'))
    consistent=result is not None and result.resolved==(not failure)
    evidence_ok=error is None and cleanup and source_ok and proof.get('verified') and capture.get('status')=='captured' and consistent
    row=dict(instance_id=ident,identity=identity,counts=counts,native_resolved=result.resolved if result else None,native_exit_code=result.test_exit_code if result else None,JUnit_sha256=capture.get('sha256'),TaskResult_sha256=sha((output/'official_result.json').read_bytes()) if result else None,cleanup=cleanup,source_unchanged=source_ok,provenance=proof.get('verified'),evidence_ok=bool(evidence_ok),exception=error,seconds=time.monotonic()-started,raw_directory=output.name)
    atomic_json(output/'BASELINE_EVIDENCE.json',row)
    return row,audit
