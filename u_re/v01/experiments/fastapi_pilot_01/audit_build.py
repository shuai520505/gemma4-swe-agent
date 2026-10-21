"""Audit frozen CPU-only upload bytes; no Kaggle requests or secret output."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile
from .register import HERE
from .auth_diagnose import inventory


def run():
    folder=HERE/'notebooks/cpu01'
    nb_raw=(folder/'study.ipynb').read_bytes();meta_raw=(folder/'kernel-metadata.json').read_bytes()
    nb=json.loads(nb_raw);meta=json.loads(meta_raw)
    frozen=json.loads((HERE/'registrations/cpu01_build.json').read_bytes())
    assert meta['enable_gpu'] is False and meta['enable_tpu'] is False
    assert meta['enable_internet'] is False and meta['model_sources']==[]
    assert hashlib.sha256(nb_raw).hexdigest()==frozen['notebook_sha256']
    assert hashlib.sha256(meta_raw).hexdigest()==frozen['metadata_sha256']
    setup=nb['cells'][0]['source']
    line=next(s for s in setup.splitlines() if s.startswith("payload=__import__('base64').b64decode("))
    value=ast.literal_eval(line[len("payload=__import__('base64').b64decode("):-1])
    payload=base64.b64decode(value)
    assert hashlib.sha256(payload).hexdigest()==frozen['payload_sha256']
    _,_,_,secrets=inventory()
    checked=[nb_raw,meta_raw]
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        assert z.testzip() is None
        for name in z.namelist():
            p=PurePosixPath(name)
            assert not p.is_absolute() and '..' not in p.parts
            assert not any(n in {'kaggle.json','access_token','credentials.json'} for n in p.parts)
            checked.append(z.read(name))
        count=len(z.namelist())
    for raw in checked:
        for secret in secrets:
            if secret:assert secret.encode() not in raw,'Credential detected; refuse upload'
    for cell in nb['cells']:
        compile(cell['source'],'<CPU-only build>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    code=nb['cells'][1]['source']
    assert 'u_re.v01.experiments.fastapi_pilot_01.screen' in code
    assert all(x not in code for x in ('vllm','evaluate_task(','kernels_push','submit_patch('))
    record=dict(CPU_only=True,GPU=False,TPU=False,model_sources=[],internet=False,
                payload_member_count=count,payload_sha256=frozen['payload_sha256'],
                notebook_sha256=frozen['notebook_sha256'],metadata_sha256=frozen['metadata_sha256'],
                credential_bytes_detected=False,model_or_Agent_execution=False,
                baseline_results_not_mocked=True)
    out=HERE/'evidence/CPU_BUILD_AUDIT.json'
    with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
    print(json.dumps(record))


if __name__=='__main__':run()
