"""Copy untouched Kaggle archives, verify members and expose selected evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from cure.build import write_new


def collect(kind,status):
    repo=Path(__file__).resolve().parents[2]
    base=repo/'artifacts/cure-gpu-mechanism-01'/kind/'output'
    archives=[p for p in base.rglob('*.zip') if p.parent.name==kind]
    assert len(archives)==1,archives
    source=archives[0]
    out=repo/'cure/gpu-study-01/results'/kind;out.mkdir(parents=True,exist_ok=False)
    manifest={}
    with zipfile.ZipFile(source) as z:
        assert z.testzip() is None
        for name in z.namelist():
            if name.endswith('/'): continue
            raw=z.read(name)
            manifest[name]=dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
            selected=(name in ('original63.log','study.log','study_cpu_gate.json','records.json','not_run.json',
                'batch_gate.json','gpu_probe.json','oversize_probe.json','model_identity.json','served_models.json',
                'vllm_config.json','vllm.log','server_stopped.json','session_exception.json','wheel_hashes.json')
                or (name.startswith('runs/') and not '/sandbox_tmp/' in name and not name.endswith('.zip'))
                or (name.startswith('phase2-cpu/') and name.endswith(('official_result.json','phase2_execution.json','worker_done.json','worker.log')))
                or name=='validation/cpu_gate.json')
            if selected: write_new(out/name,raw)
    write_new(out/'evidence.zip',source.read_bytes())
    write_new(out/'archive-members.json',(json.dumps(manifest,indent=2)+'\n').encode())
    for p in base.glob('*.log'): write_new(out/p.name,p.read_bytes())
    record=dict(kind=kind,kernel='wudangdexiaodoashi/gemma4-cure-mechanism-01-'+kind,kernel_version=1,
        kaggle_status=status,archive_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),bytes=source.stat().st_size,
        original_archive=str(source),crc_verified=True,member_count=len(manifest),formal_submission=False)
    write_new(out/'collection.json',(json.dumps(record,indent=2)+'\n').encode())
    print(json.dumps(record,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind');p.add_argument('status');a=p.parse_args();collect(a.kind,a.status)
