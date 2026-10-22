"""Read only the unique accepted GPU version;retain original UNKNOWN events."""
import json
from pathlib import Path
import shutil
import types
from .GPU_NOTEBOOK import HERE,ROOT,SLUG

def collect(private_root):
    private_root=Path(private_root).resolve();assert not private_root.is_relative_to(ROOT)
    receipt=json.loads((HERE/'execution/HTTP_RECEIPT.json').read_bytes())
    identity=receipt['Notebook_id'];assert type(identity) is int and receipt['accepted_version']==1
    if not (HERE/'BUILD_FREEZE.json').exists():shutil.copyfile(HERE/'BUILD.json',HERE/'BUILD_FREEZE.json')
    path=ROOT/'u_re/v01/experiments/fastapi_pilot_01/attempts/cpu02/reconciliation_01/recover.py'
    source=path.read_text(encoding='utf-8')
    old="item.file_name.endswith('.zip') and 'cpu02/' in item.file_name and '/source/' not in item.file_name"
    assert source.count(old)==1;source=source.replace(old,"item.file_name == 'u_re_actionfirst_abba01.zip'")
    source=source.replace("meta['enable_gpu'] is False","meta['enable_gpu'] is True")
    source=source.replace("meta['model_data_sources'] == []","len(meta['model_data_sources'] or []) == 1 and meta['machine_shape']=='NvidiaL4'")
    m=types.ModuleType('real_gpu_readonly');m.__file__=str(path);exec(compile(source,str(path),'exec'),m.__dict__)
    index=len(list((HERE/'read_observations').glob('read-*')))+1;assert index<=24,'Bounded24 full source-pinned collection attempts'
    dest=private_root/f'read-{index:02d}';dest.mkdir(parents=True,exist_ok=False)
    m.HERE=dest;m.CPU02=HERE;m.OWNER=SLUG.split('/')[0];m.SLUG=SLUG.split('/')[1];m.REF=SLUG;m.ID=identity
    try:m.run(read_latest=True,confirmed_read=True)
    finally:
        safe=HERE/'read_observations'/f'read-{index:02d}';safe.mkdir(parents=True,exist_ok=True)
        for name in ('RESOURCE_IDENTITY.json','RUN_STATUS.json','OUTPUT_MANIFEST.json','READONLY_QUERY_LEDGER.json','LATEST_BEFORE_STATUS.json','LATEST_AFTER_DOWNLOAD.json'):
            p=dest/'evidence_confirmed'/name
            if p.exists():shutil.copyfile(p,safe/name)

if __name__=='__main__':
    import sys
    collect(sys.argv[1])
