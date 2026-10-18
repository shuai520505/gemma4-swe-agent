"""Read only existing SDK log paths, before temporary server cleanup can remove them."""
import hashlib
from pathlib import Path
import shutil
from harness_v2.evidence import atomic_json


def capture_logs(server,directory,*,phase):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    records=[]
    for key,value in getattr(server,'__dict__',{}).items():
        if 'log' not in key.lower():continue
        path=getattr(value,'name',value)
        if not isinstance(path,(str,Path)):continue
        try:
            file=Path(path)
            if not file.is_file():continue
            target=directory/(phase+'-'+key.strip('_')+'.log')
            shutil.copyfile(file,target)
            records.append(dict(attribute=key,source_path=str(file),file=target.name,
                bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
        except OSError as exc:records.append(dict(attribute=key,error=repr(exc)))
    try:atomic_json(directory/(phase+'.json'),dict(files=records,request_specific_abort_confirmation=False,
        scope='SDK log file export only; no inferred abort acknowledgement'))
    except OSError:pass
    return records
