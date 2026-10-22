"""CPU-only synthetic capability checks. No task, model or network inference."""
from datetime import datetime, timezone
import errno
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def child(mode):
    import ctypes
    with tempfile.TemporaryDirectory(prefix='ure-cap-') as root:
        root=Path(root);(root/'inside').write_text('owned synthetic canary')
        if mode=='chroot':
            os.chroot(root);os.chdir('/')
            assert Path('/inside').read_text()=='owned synthetic canary'
            return dict(supported=True,inside_read=True,root_changed=True)
        if mode=='uid':
            work=root/'work';work.mkdir();os.chmod(root,0o711);os.chmod(work,0o777)
            secret=root/'secret';secret.mkdir(mode=0o700);(secret/'canary').write_text('owned')
            os.setgroups([]);os.setresgid(65534,65534,65534);os.setresuid(65534,65534,65534)
            try:(secret/'canary').read_text();denied=False
            except PermissionError:denied=True
            (work/'write').write_text('allowed')
            # Child no longer owns temp root; parent cleans after child exits.
            print(json.dumps(dict(supported=True,uid=os.geteuid(),private_denied=denied,workspace_write=True,temporary_root=str(root))),flush=True)
            os._exit(0)
        libc=ctypes.CDLL(None,use_errno=True)
        flag={'mount':0x00020000,'user':0x10000000}[mode]
        result=libc.unshare(ctypes.c_int(flag));number=ctypes.get_errno()
        return dict(supported=result==0,errno=number if result else None,errno_name=errno.errorcode.get(number) if result else None)


def main(out):
    import shutil
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    result=dict(experiment_id='U-RE-ACTION-FIRST-ISOLATION-CAP01',started_utc=datetime.now(timezone.utc).isoformat(),
        python=sys.version,uid=os.geteuid(),gid=os.getegid(),GPU=False,Gemma_calls=0,Agent_runs=0,task_baselines=0,
        Landlock='NOT_REPEATED_PRIOR_ENOSYS',actual_tool_canaries='NOT_RUN_CAPABILITY_PROBE_ONLY',children={})
    status=Path('/proc/self/status').read_text()
    result['kernel_controls']={line.split(':')[0]:line.split(':',1)[1].strip() for line in status.splitlines()
        if line.split(':')[0] in ('CapEff','CapBnd','NoNewPrivs','Seccomp','Seccomp_filters')}
    for mode in ('chroot','uid','mount','user'):
        p=subprocess.run([sys.executable,__file__,'--child',mode],capture_output=True,text=True,timeout=30,close_fds=True)
        row=dict(returncode=p.returncode,stderr=p.stderr[-1000:])
        try:row.update(json.loads(p.stdout))
        except ValueError:row.update(supported=False,output_parse_failed=True)
        root=row.pop('temporary_root',None)
        if root:
            assert Path(root).parent==Path(tempfile.gettempdir()) and Path(root).name.startswith('ure-cap-')
            shutil.rmtree(root);row['parent_cleanup']=True
        result['children'][mode]=row
    try:
        import docker
        result['docker_package']=importlib.metadata.version('docker')
        client=docker.from_env(timeout=12)
        try:
            result['docker_ping']=client.ping()
            info=client.version();result['docker_version']={k:info.get(k) for k in ('Version','ApiVersion','Os','Arch')}
            result['approved_local_images']=[]
            for tag in ('swebench-sandbox:latest','gcr.io/kaggle-playground-170215/swebench-sandbox:v1','gcr.io/kaggle-playground-170215/swebench-sandbox:latest'):
                try:
                    image=client.images.get(tag)
                    result['approved_local_images'].append(dict(tag=tag,id=image.id,repo_digests=image.attrs.get('RepoDigests')))
                except docker.errors.ImageNotFound:result['approved_local_images'].append(dict(tag=tag,present=False))
        finally:client.close()
    except Exception as exc:
        # No raw Docker endpoint, credential-bearing URL or environment is logged.
        result['docker_error']=dict(exception_class=type(exc).__name__,errno=getattr(exc,'errno',None))
        result['docker_ping']=False
    result.update(ended_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-started,
        cleanup='OWNED_CHILD_TEMP_DIRECTORIES_REMOVED',isolation_verified=False)
    (out/'CAPABILITIES.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    if sys.argv[1:2]==['--child']:
        try:value=child(sys.argv[2])
        except OSError as exc:value=dict(supported=False,errno=exc.errno,errno_name=errno.errorcode.get(exc.errno))
        print(json.dumps(value),flush=True)
    else:main(sys.argv[1])
