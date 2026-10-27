"""Once-only CPU CLI dispatch, with private originals and read-only recovery."""
import datetime
import json
import os
import subprocess

from .prepare import HERE,PRIVATE,REF,sha,write


def run(args,label,timeout=300):
    directory=PRIVATE/'cli'/label;directory.mkdir(parents=True,exist_ok=False)
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        r=subprocess.run(['kaggle',*args],capture_output=True,timeout=timeout,
            env=dict(os.environ,HTTPS_PROXY='http://127.0.0.1:7890',PYTHONIOENCODING='utf-8'))
        code,out,err=r.returncode,r.stdout,r.stderr
    except subprocess.TimeoutExpired as exc:code,out,err=None,exc.stdout or b'',exc.stderr or b''
    (directory/'stdout.txt').write_bytes(out);(directory/'stderr.txt').write_bytes(err)
    write(directory/'record.json',dict(args=args,started=start,returncode=code,stdout_sha256=sha(out),stderr_sha256=sha(err)))
    print(json.dumps(dict(label=label,returncode=code,stdout_bytes=len(out),stderr_bytes=len(err))),flush=True)
    return code


def push(version):
    assert version in (1,2)
    folder=PRIVATE/f'notebook-v{version}'
    meta=json.loads((folder/'kernel-metadata.json').read_bytes())
    assert meta['id']==REF and meta['is_private'] is True
    assert meta['enable_gpu'] is False and meta['enable_tpu'] is False and meta['enable_internet'] is False
    assert meta['machine_shape']=='' and not meta['model_sources'] and not meta['competition_sources']
    if version==2:assert (PRIVATE/'CPU_V1_INFRASTRUCTURE_FAILURE.json').is_file()
    with (PRIVATE/f'CPU_DISPATCH_V{version}.json').open('x',encoding='utf8') as file:
        json.dump(dict(version=version,ref=REF,CPU_only=True,model_inference=False,
            status='ATTEMPT_RECORDED_NO_BLIND_RETRY',
            Notebook_sha256=sha((folder/'study.ipynb').read_bytes())),file,indent=2)
    return run(['kernels','push','-p',str(folder),'-t','3600'],f'dispatch-v{version}',900)


if __name__=='__main__':
    import sys
    if sys.argv[1]=='push':push(int(sys.argv[2]))
    else:run(sys.argv[2:],sys.argv[1])
