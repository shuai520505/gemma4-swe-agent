"""Collect study02 untouched archives and expose the CPU Runner/GPU evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from cure.build import write_new

def collect(kind,status,kernel):
    repo=Path(__file__).resolve().parents[2]
    base=repo/'artifacts/cure-gpu-mechanism-02-c1'/kind/'output'
    archives=[p for p in base.rglob('*.zip') if p.parent.name==kind]
    assert len(archives)==1,archives
    source=archives[0];out=repo/'cure/gpu-study-02-c1/results'/kind
    out.mkdir(parents=True,exist_ok=False)
    manifest={}
    with zipfile.ZipFile(source) as z:
        assert z.testzip() is None
        for name in z.namelist():
            if name.endswith('/'):continue
            raw=z.read(name);manifest[name]=dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
            selected=(name in ('original63.log','runner.log','full_runner_cpu_gate.json','records.json','not_run.json',
                'batch_gate.json','gpu_probe.json','oversize_probe.json','model_identity.json','served_models.json',
                'vllm_config.json','vllm.log','server_stopped.json','session_exception.json','wheel_hashes.json')
                or name.startswith('runner-evidence/') or name=='validation/cpu_gate.json'
                or (name.startswith('runs/') and '/sandbox_tmp/' not in name and not name.endswith('.zip')))
            if selected:write_new(out/name,raw)
    write_new(out/'evidence.zip',source.read_bytes())
    write_new(out/'archive-members.json',(json.dumps(manifest,indent=2)+'\n').encode())
    for p in base.glob('*.log'):write_new(out/p.name,p.read_bytes())
    data=dict(kind=kind,kernel=kernel,kernel_version=1,kaggle_status=status,
        archive_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),bytes=source.stat().st_size,
        crc_verified=True,member_count=len(manifest),formal_submission=False)
    write_new(out/'collection.json',(json.dumps(data,indent=2)+'\n').encode())
    print(json.dumps(data,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind');p.add_argument('status');p.add_argument('kernel');a=p.parse_args();collect(a.kind,a.status,a.kernel)
