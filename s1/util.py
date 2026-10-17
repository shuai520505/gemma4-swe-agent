import hashlib
import io
import json
from pathlib import Path
import zipfile


def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def sha(raw):return hashlib.sha256(raw).hexdigest()


def save(path,data):
    from experiments.prepare import write_new
    write_new(Path(path),(json.dumps(data,indent=2)+'\n').encode())


def archive(files):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,raw in sorted(files.items()):
            info=zipfile.ZipInfo(name,(2020,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,raw)
    return buf.getvalue()
