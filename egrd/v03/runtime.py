"""CPU development driver: isolated venvs, unchanged sources, bounded probes.

Not a production Agent sandbox, official Native Verifier or SWE-bench harness.
Only the frozen, owned diagnostic programs are invoked; no model is loaded.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import shutil
import stat
import subprocess
import sys
import tarfile
import time


def sha(raw):return hashlib.sha256(raw).hexdigest()


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf8')


def tree_identity(root):
    root=Path(root).resolve();rows={}
    for path in sorted(root.rglob('*')):
        name=path.relative_to(root).as_posix()
        if path.is_symlink():
            assert path.resolve().is_relative_to(root),'Source symlink escapes root'
            rows[name]=dict(link=os.readlink(path))
        elif path.is_file():rows[name]=dict(sha256=sha(path.read_bytes()))
    return sha(json.dumps(rows,sort_keys=True).encode())


def restore(snapshot,destination,expected_root):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    base=destination.resolve()
    with tarfile.open(snapshot,'r:gz') as archive:
        members=archive.getmembers()
        for member in members:
            target=(base/member.name).resolve()
            assert not member.name.startswith('/') and target.is_relative_to(base)
            assert member.name.split('/')[0]==expected_root
            assert member.isfile() or member.isdir() or member.issym(),'Unsupported source archive entry'
            if member.issym():
                assert (target.parent/member.linkname).resolve().is_relative_to(base/expected_root)
        archive.extractall(base,filter='data')
    return base/expected_root


def cleanup(path,parent):
    path=Path(path);parent=Path(parent).resolve()
    assert path.resolve()!=parent and path.resolve().is_relative_to(parent)
    assert not path.is_symlink()
    shutil.rmtree(path)
    return not path.exists()


def command(args,cwd,output,env,timeout=120):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    start=time.monotonic();timed_out=False
    with (output/'stdout.log').open('wb') as stdout,(output/'stderr.log').open('wb') as stderr:
        process=subprocess.Popen([str(a) for a in args],cwd=cwd,env=env,stdout=stdout,stderr=stderr,
            start_new_session=os.name=='posix')
        try:process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True
            if os.name=='posix':
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
            else:process.kill()
            process.wait(timeout=10)
    result=dict(returncode=process.returncode,timed_out=timed_out,seconds=time.monotonic()-start,
        stdout_sha256=sha((output/'stdout.log').read_bytes()),stderr_sha256=sha((output/'stderr.log').read_bytes()),
        stdout_bytes=(output/'stdout.log').stat().st_size,stderr_bytes=(output/'stderr.log').stat().st_size,
        owned_process_reaped=process.poll() is not None)
    write(output/'COMMAND.json',result)
    return result


def execute_task(task,data,output,workspaces):
    out=output/task['instance_id'];out.mkdir(parents=True,exist_ok=False)
    work=workspaces/task['instance_id'];work.mkdir(parents=True,exist_ok=False)
    record=dict(instance_id=task['instance_id'],repo=task['repo'],base_commit=task['base_commit'],
        issue_sha256=task['issue_sha256'],snapshot_sha256=task['snapshot_sha256'],
        split=task['split'],exposure=task['exposure'],status='NOT_YET_RUNNABLE',
        classification='ENVIRONMENT_BLOCKED',environment_verified=False,
        genuine_issue_failure=False,source_unchanged=None,cleanup=False,
        official_native_resolved=None,swebench_resolved=None,model_requests=0,
        prompt_tokens=None,completion_tokens=None,tool_requests=None,
        termination_reason=None,probe=None)
    source=None;before=None;start=time.monotonic()
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
        PIP_CONFIG_FILE=os.devnull,PIP_DISABLE_PIP_VERSION_CHECK='1',PIP_NO_INDEX='1',
        OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONIOENCODING='utf-8',
        MPLCONFIGDIR=str(work/'mpl-config'),XDG_CACHE_HOME=str(work/'cache'))
    try:
        snapshot=data/task['snapshot_path'];assert sha(snapshot.read_bytes())==task['snapshot_sha256']
        source=restore(snapshot,work/'restored',task['archive_root'])
        before=tree_identity(source);record['source_tree_before']=before
        record['probe_sha256']=sha((data/task['diagnostic_path']).read_bytes())
        assert record['probe_sha256']==task['diagnostic_sha256']
        venv=work/'venv';python=venv/'bin/python'
        setup=command([sys.executable,'-m','venv','--without-pip',venv],work,out/'venv',env,timeout=60)
        record['venv_creation']=setup
        if setup['returncode']!=0:raise RuntimeError('VENV_CREATION_FAILED')
        install=command([sys.executable,'-m','pip','--python',python,'install','--no-index','--no-deps',
            '--require-hashes','--find-links',data/'wheels','-r',data/task['requirements_path']],
            work,out/'install',env,timeout=180)
        record['installation']=install
        if install['returncode']!=0:raise RuntimeError('DEPENDENCY_INSTALL_FAILED')
        record['requirements_sha256']=sha((data/task['requirements_path']).read_bytes())
        record['pip_check']=command([sys.executable,'-m','pip','--python',python,'check'],work,out/'pip-check',env,timeout=60)
        if record['pip_check']['returncode']!=0:raise RuntimeError('DEPENDENCY_CLOSURE_FAILED')
        env.update(PYTHONPATH=str(source)+os.pathsep+str((data/'diagnostics').resolve()),
            EGRD_SOURCE=str(source),EGRD_RESULT_PATH=str(out/'probe.json'))
        smoke_code=('import json,sys,importlib.metadata as m;from pathlib import Path;import '+task['module']+' as target;'
            'assert Path(target.__file__).resolve().is_relative_to(Path('+repr(str(source))+').resolve());'
            'print(json.dumps(dict(module_file=str(target.__file__),module_version=getattr(target,"__version__",None),'
            'python=sys.version,isolated_prefix=sys.prefix,base_prefix=sys.base_prefix,'
            'packages=sorted((d.metadata["Name"],d.version) for d in m.distributions()),'
            'installed_RECORD_sha256={d.metadata["Name"]:__import__("hashlib").sha256('
            '(d.read_text("RECORD") or "").encode()).hexdigest() for d in m.distributions()})))')
        smoke=command([python,'-s','-B','-c',smoke_code],work,out/'import',env,timeout=60)
        record['import_smoke']=smoke
        if smoke['returncode']!=0:raise RuntimeError('SOURCE_IMPORT_FAILED')
        record['runtime']=json.loads((out/'import/stdout.log').read_text())
        assert record['runtime']['isolated_prefix']!=record['runtime']['base_prefix']
        record['source_import_verified']=True
        result=command([python,'-s','-B',data/task['diagnostic_path']],work,out/'diagnostic',env,timeout=60)
        record['diagnostic_execution']=result
        if result['timed_out']:
            record.update(classification='DIAGNOSTIC_TIMEOUT',termination_reason='TIMEOUT')
        elif not (out/'probe.json').exists():
            record.update(classification='UNKNOWN_FAILURE',termination_reason='NO_STRUCTURED_RECEIPT')
        else:
            probe=json.loads((out/'probe.json').read_bytes());record['probe']=probe
            record['environment_verified']=bool(probe['controls_passed'])
            record['classification']=probe['classification']
            record['termination_reason']='CHECK_COMPLETED'
            record['genuine_issue_failure']=probe['classification']=='TARGET_BEHAVIOR_FAILURE' and probe['controls_passed']
            record['status']='BUG_REPRODUCED' if record['genuine_issue_failure'] else 'CHECK_PASS' if probe['classification']=='CHECK_PASS_NON_DISCRIMINATING' else 'NOT_YET_RUNNABLE'
    except BaseException as exc:
        record.update(exception_type=type(exc).__name__,environment_error=str(exc)[:1000],termination_reason='SETUP_OR_INTEGRITY_ERROR')
        if isinstance(exc,AssertionError):record['classification']='INTEGRITY_FAILURE'
    finally:
        try:
            if source and source.exists():
                record['source_tree_after']=tree_identity(source)
                record['source_unchanged']=record['source_tree_after']==before
            if source and not record['source_unchanged']:
                record.update(classification='INTEGRITY_FAILURE',genuine_issue_failure=False,status='NOT_YET_RUNNABLE')
        except BaseException as exc:
            record.update(classification='INTEGRITY_FAILURE',genuine_issue_failure=False,status='NOT_YET_RUNNABLE',
                integrity_error=type(exc).__name__)
        record['cleanup']=cleanup(work,workspaces)
        record['wall_seconds']=time.monotonic()-start
        write(out/'RESULT.json',record)
    return record


def run(data,output):
    data=Path(data).resolve();output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((data/'MANIFEST.json').read_bytes())
    for name,digest in manifest['files'].items():assert sha((data/name).read_bytes())==digest,name
    registry=json.loads((data/'metadata/task_registry.json').read_bytes())
    assert registry['execution_order']==['django__django-16333','pydata__xarray-3095','fastapi_14297']
    assert not list(Path('/dev').glob('nvidia[0-9]*')),'CPU-only authorization'
    assert sys.version_info[:2]==(3,12),'Pinned CPU development interpreter changed'
    write(output/'ENVIRONMENT.json',dict(python=sys.version,platform=platform.platform(),CPU_only=True,
        GPU_device_nodes=[],dataset_manifest_sha256=sha((data/'MANIFEST.json').read_bytes()),
        dataset_revision=manifest['revision'],network_at_runtime=False,Compiler_retested=False))
    workspaces=output/'workspaces';workspaces.mkdir()
    records=[]
    for task in registry['tasks']:
        records.append(execute_task(task,data,output/'tasks',workspaces))
        if records[-1]['classification']=='INTEGRITY_FAILURE':break
    summary=dict(schema='EGRD_DEV_RESULTS_V1',dataset_revision=manifest['revision'],records=records,
        environment_verified=sum(r['environment_verified'] for r in records),
        genuine_issue_failures=sum(r['genuine_issue_failure'] for r in records),
        model_requests=0,official_native_resolved=None,swebench_resolved=None,
        all_cleanup=all(r['cleanup'] for r in records),GPU=False,formal_submission=False)
    write(output/'TASK_REPRODUCTIONS.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='records'}),flush=True)
    return summary


if __name__=='__main__':run(sys.argv[1],sys.argv[2])
