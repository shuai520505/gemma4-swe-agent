"""Opaque single-file transport avoids auto-expansion and remote small-file copying."""
import hashlib,json,shutil,zipfile
from pathlib import Path
D=Path(__file__).resolve().parent
source=D/'cpu-archive-v8/r2a-cpu-admission-01.zip'
with zipfile.ZipFile(source) as z:
    assert z.testzip() is None
    summary=json.loads(z.read('CPU_ADMISSION_SUMMARY.json'))
out=D/'runtime-upload';out.mkdir(exist_ok=True)
target=out/'R2A_LINUX_RUNTIME.bin';shutil.copyfile(source,target)
identity=dict(sha256=hashlib.sha256(target.read_bytes()).hexdigest(),bytes=target.stat().st_size,
    format='ZIP bytes with opaque extension; extract only after SHA256 verification',
    source_notebook='wudangdexiaodoashi/r2a-native-cpu-admission-01',source_recorded_version=8,
    original_admission=summary['status'],is_admitted=False,
    purpose='Runtime/source assets for CPU diagnostic and subsequent admission; not repair or readiness evidence')
(out/'RUNTIME_TRANSPORT_IDENTITY.json').write_text(json.dumps(identity,indent=2)+'\n')
(D/'RUNTIME_TRANSPORT_IDENTITY.json').write_text(json.dumps(identity,indent=2)+'\n')
(out/'dataset-metadata.json').write_text(json.dumps(dict(id='wudangdexiaodoashi/r2a-linux-runtime-inputs-20261101',title='R2A Linux Runtime Inputs 20261101',licenses=[dict(name='other')],description='Private CPU research assets, original sources, pinned dependencies and evaluator-only public test specifications. Original admission failed; not a repaired task or reference answer. No model weights or API credentials.'),indent=2))
print(json.dumps(identity))
