"""Only recover this already-saved CPU version, never dispatch."""
import json,types,shutil
from pathlib import Path
from .cpu_notebook import CPU,ROOT,SLUG

def collect(private_root):
    private_root=Path(private_root).resolve();assert not private_root.is_relative_to(ROOT)
    receipt=json.loads((CPU/'execution/HTTP_RECEIPT.json').read_text(encoding='utf-8'))
    ID=receipt['Notebook_id'];assert type(ID) is int and receipt['accepted_version']==1
    frozen=CPU/'BUILD_FREEZE.json'
    if not frozen.exists():shutil.copyfile(CPU/'BUILD.json',frozen)
    original=ROOT/'u_re/v01/experiments/fastapi_pilot_01/attempts/cpu02/reconciliation_01/recover.py'
    text=original.read_text(encoding='utf-8')
    old="item.file_name.endswith('.zip') and 'cpu02/' in item.file_name and '/source/' not in item.file_name"
    assert text.count(old)==1;text=text.replace(old,"item.file_name == 'u_re_action_first_cpu01.zip'")
    m=types.ModuleType('action_cpu_readonly');m.__file__=str(original);exec(compile(text,str(original),'exec'),m.__dict__)
    n=len(list((CPU/'read_observations').glob('read-*')))+1;assert n<=5
    dest=private_root/f'read-{n:02d}';dest.mkdir(parents=True,exist_ok=False)
    m.HERE=dest;m.CPU02=CPU;m.OWNER=SLUG.split('/')[0];m.SLUG=SLUG.split('/')[1];m.REF=SLUG;m.ID=ID
    try:m.run(read_latest=True,confirmed_read=True)
    finally:
        safe=CPU/'read_observations'/f'read-{n:02d}';safe.mkdir(parents=True,exist_ok=True)
        for name in ('RESOURCE_IDENTITY.json','RUN_STATUS.json','OUTPUT_MANIFEST.json','READONLY_QUERY_LEDGER.json','LATEST_BEFORE_STATUS.json','LATEST_AFTER_DOWNLOAD.json'):
            p=dest/'evidence_confirmed'/name
            if p.exists():shutil.copyfile(p,safe/name)
if __name__=='__main__':
    import sys
    collect(sys.argv[1])
