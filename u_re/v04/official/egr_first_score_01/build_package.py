"""Frozen EGR packaging only; imports no harness, model or evaluator."""
import base64,hashlib,io,json,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
SLUG='wudangdexiaodoashi/u-re-egr-v04-first-official-score'
EXPECTED='07263740c5ee22bf6611d7fa31dafbc84d7fb50288d22355b9201cd6954a6840'
def build():
    raw=(ROOT/'u_re/v04/experiments/evidence_guided_repair_01/submission_egr_v04.zip').read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None and set(z.namelist())=={'agent.yaml','eval_config.yaml','prompts/system.md'}
        members={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}
    code=f"""import base64,hashlib,io,json,zipfile
from pathlib import Path
raw=base64.b64decode({base64.b64encode(raw).decode()!r})
assert hashlib.sha256(raw).hexdigest()=={EXPECTED!r}
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    assert z.testzip() is None
    assert set(z.namelist())==set({members!r})
    assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in {members!r}.items())
out=Path('/kaggle/working/submission.zip');out.write_bytes(raw)
assert out.read_bytes()==raw
Path('/kaggle/working/packaging.json').write_text(json.dumps(dict(candidate='U-RE-EGR-V0.4',sha256=hashlib.sha256(out.read_bytes()).hexdigest(),bytes=len(raw),members={members!r},model_inference=False),indent=2))
print('FROZEN_U_RE_EGR_PACKAGE_OK',hashlib.sha256(raw).hexdigest())
"""
    compile(code,'<package>','exec')
    nb=dict(nbformat=4,nbformat_minor=5,metadata={'kernelspec':{'name':'python3','language':'python','display_name':'Python 3'}},cells=[dict(cell_type='code',source=code,metadata={},outputs=[],execution_count=None,id='ure-egr-package')])
    data=(json.dumps(nb,indent=1)+'\n').encode();d=HERE/'notebook';d.mkdir(exist_ok=True)
    meta=dict(id=SLUG,title='U RE EGR V04 First Official Score',code_file='study.ipynb',language='python',kernel_type='notebook',is_private=True,enable_gpu=False,enable_tpu=False,enable_internet=False,competition_sources=['gemma-4-developer-agent'],dataset_sources=[],model_sources=[],kernel_sources=[],docker_image='gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461',docker_image_pinning_type='original')
    for path,value in ((d/'study.ipynb',data),(d/'kernel-metadata.json',(json.dumps(meta,indent=2)+'\n').encode())):
        with path.open('xb') as f:f.write(value)
    spec=dict(execution_id='U-RE-EGR-FIRST-SCORE-01',slug=SLUG,max_dispatches=1,Notebook_sha256=hashlib.sha256(data).hexdigest(),wire_sha256=hashlib.sha256(json.dumps(nb).encode()).hexdigest(),payload_sha256=EXPECTED,selection_protocol_sha256=hashlib.sha256((ROOT/'u_re/v04/experiments/evidence_guided_repair_01/EGR_PROMPT_LOCK.json').read_bytes()).hexdigest(),configuration=dict(GPU=False,TPU=False,internet=False,model_sources=[],Agent_runs=0,Gemma_calls=0,formal_submission=False),expected_candidates_in_order=['U-RE-EGR'],sdk_versions={'kaggle':'2.2.2','kagglesdk':'0.1.35'},candidate_members=members)
    with (HERE/'BUILD.json').open('x',encoding='utf-8') as f:json.dump(spec,f,indent=2)
    print(json.dumps(dict(slug=SLUG,candidate=EXPECTED,Notebook_sha256=spec['Notebook_sha256'])))
if __name__=='__main__':build()
