"""Bounded official CLI, private logs and durable once-only mutation records."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import hashlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PRIVATE=Path('C:/Users/HP/.codex/private-evidence/egrd_v03')
DATASET='wudangdexiaodoashi/egrd-repair-development'
NOTEBOOK='wudangdexiaodoashi/egrd-v03-repair-development-cpu'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf8',newline='\n')


def run(args,label,timeout=300):
    d=PRIVATE/'cli'/label;d.mkdir(parents=True,exist_ok=False)
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        result=subprocess.run(['kaggle',*args],capture_output=True,timeout=timeout,
            env=dict(os.environ,HTTPS_PROXY='http://127.0.0.1:7890',PYTHONIOENCODING='utf-8'))
        code,out,err=result.returncode,result.stdout,result.stderr
    except subprocess.TimeoutExpired as exc:
        code,out,err=None,exc.stdout or b'',exc.stderr or b''
    (d/'stdout.txt').write_bytes(out);(d/'stderr.txt').write_bytes(err)
    write(d/'record.json',dict(args=args,started=start,returncode=code,
        stdout_sha256=sha(out),stderr_sha256=sha(err)))
    print(json.dumps(dict(label=label,returncode=code,stdout_bytes=len(out),stderr_bytes=len(err))),flush=True)
    return code,out.decode('utf8',errors='replace'),err.decode('utf8',errors='replace')


def mutation(kind,folder,version=1):
    folder=Path(folder).resolve()
    if kind=='dataset':
        assert version in (1,2)
        metadata=json.loads((folder/'dataset-metadata.json').read_bytes())
        assert metadata['id']==DATASET and metadata['title']=='EGRD Repair Development'
        assert metadata['isPrivate'] is True
        assert 20<=len(metadata['subtitle'])<=80
        args=['datasets','create','-p',str(folder),'-t'] if version==1 else [
            'datasets','version','-p',str(folder),'-t','-m','CPU reproduction outcomes and environment provenance; source/probes unchanged']
        assert '-u' not in args and '--public' not in args
    else:
        assert kind=='notebook' and version in (1,2)
        metadata=json.loads((folder/'kernel-metadata.json').read_bytes())
        assert metadata['id']==NOTEBOOK and metadata['is_private'] is True
        assert metadata['enable_gpu'] is False and metadata['enable_tpu'] is False
        assert metadata['enable_internet'] is False and metadata['machine_shape']==''
        assert not metadata['model_sources']
        if version==2:assert (PRIVATE/'confirmed-cpu-v1-infrastructure-failure.json').is_file()
        args=['kernels','push','-p',str(folder),'-t','3600']
    PRIVATE.mkdir(parents=True,exist_ok=True)
    with (PRIVATE/f'{kind}-dispatch-v{version}.json').open('x',encoding='utf8') as f:
        json.dump(dict(kind=kind,version=version,status='ATTEMPT_RECORDED_NO_AUTORETRY',
            file_hashes={p.name:sha(p.read_bytes()) for p in folder.iterdir() if p.is_file()},
            CPU_only=True,GPU_inference=False,formal_submission=False),f,indent=2)
    return run(args,f'{kind}-dispatch-v{version}',timeout=900)


if __name__=='__main__':
    import sys
    if sys.argv[1]=='mutation':mutation(sys.argv[2],sys.argv[3],int(sys.argv[4]))
    else:run(sys.argv[2:],sys.argv[1])
