"""Verify one canonical original CPU archive; expand only useful new evidence."""
import hashlib
import json
from pathlib import Path,PurePosixPath
import sys
import zipfile
from .build import HERE,write


def collect(revision):
    root=HERE/'results'/revision
    archives=list((root/'download').rglob('*.zip'))
    assert len(archives)==1,archives
    raw=archives[0].read_bytes();write(root/'raw.zip',raw)
    with zipfile.ZipFile(root/'raw.zip') as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('evidence_manifest.json'))
        for name,value in manifest.items():
            data=z.read(name)
            assert len(data)==value['bytes'] and hashlib.sha256(data).hexdigest()==value['sha256'],name
        for name in z.namelist():
            p=PurePosixPath(name)
            assert not p.is_absolute() and '..' not in p.parts
            if name in ('cpu.log','installation.log','wheel_hashes.json','task_wheel_hashes.json') or name.startswith('validation/'):
                if any(s in p.parts for s in ('baseline','sandboxes','sandbox_tmp','__pycache__')):
                    continue
                write(root/name,z.read(name))
        result=dict(raw_archive_sha256=hashlib.sha256(raw).hexdigest(),raw_bytes=len(raw),CRC=True,
            manifest_verified_files=len(manifest),gate=json.loads(z.read('validation/cpu_gate.json')),
            source_registry=json.loads(z.read('source/u_re/v01/runtime_registration.json'))['source_base'],
            extraction='Canonical raw ZIP retains complete original source and evidence; only validation/logs expanded. No original overwrite.')
    write(root/'COLLECTION.json',(json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in result.items() if k!='gate'},indent=2))
    print(json.dumps(result['gate'],indent=2))


if __name__=='__main__':
    collect(sys.argv[1])
