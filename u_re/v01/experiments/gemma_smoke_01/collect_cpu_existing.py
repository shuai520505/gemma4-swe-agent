"""Reuse CPU02 read-only reconciliation; never imports any save/launch function."""
import json
from pathlib import Path
import shutil
import types
from .cpu_notebook import CPU,ROOT,SLUG,write

def collect(private_root):
    private_root=Path(private_root).resolve()
    assert not private_root.is_relative_to(ROOT),'Raw outputs stay outside public checkout'
    receipt=json.loads((CPU/'execution/HTTP_RECEIPT.json').read_text(encoding='utf-8'))
    assert receipt['Notebook_id']==140042899 and receipt['accepted_version']==1
    write(CPU/'BUILD_FREEZE.json',json.loads((CPU/'BUILD.json').read_text(encoding='utf-8')))
    original=ROOT/'u_re/v01/experiments/fastapi_pilot_01/attempts/cpu02/reconciliation_01/recover.py'
    raw=original.read_text(encoding='utf-8')
    old="item.file_name.endswith('.zip') and 'cpu02/' in item.file_name and '/source/' not in item.file_name"
    assert raw.count(old)==1
    raw=raw.replace(old,"item.file_name == 'u_re_smoke_cpu01.zip'")
    m=types.ModuleType('smoke_readonly_recovery');m.__file__=str(original)
    exec(compile(raw,str(original),'exec'),m.__dict__)
    number=len(list((CPU/'read_observations').glob('read-*')))+1
    assert number<=6,'Bounded read-only observation budget exhausted'
    target=private_root/f'read-{number:02d}';target.mkdir(parents=True,exist_ok=False)
    m.HERE=target;m.CPU02=CPU;m.OWNER=SLUG.split('/')[0];m.SLUG=SLUG.split('/')[1];m.REF=SLUG;m.ID=140042899
    try:m.run(read_latest=True,confirmed_read=True)
    finally:
        safe=CPU/'read_observations'/f'read-{number:02d}';safe.mkdir(parents=True)
        for name in ('RESOURCE_IDENTITY.json','RUN_STATUS.json','OUTPUT_MANIFEST.json','READONLY_QUERY_LEDGER.json',
                     'LATEST_BEFORE_STATUS.json','LATEST_AFTER_DOWNLOAD.json','OUTPUT_LISTING.json','FINAL_DECISION.md'):
            p=target/'evidence_confirmed'/name
            if p.is_file():shutil.copyfile(p,safe/name)
        write(safe/'PRIVATE_EVIDENCE_INDEX.json',dict(private_directory=str(target),
            original_recovery_source=str(original.relative_to(ROOT)),new_SaveKernel_calls=0))

if __name__=='__main__':
    import sys
    collect(sys.argv[1])
