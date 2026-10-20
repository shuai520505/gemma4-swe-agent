"""Deterministic main-only candidate plus CPU-only official Notebook payload."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile
from s1.util import archive,sha_file
from experiments.prepare import write_new

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PARENT=ROOT/'s2/egv_agenttool_t500_v01'
SMOKE=ROOT/'s2/experiments/t500_agenttool_smoke_01'


def emit(path,data):write_new(path,(json.dumps(data,indent=2)+'\n').encode())


def package():
    names=['agent.yaml','eval_config.yaml','prompts/main.md','sub_agents/egv_verifier.yaml','sub_agents/egv_verifier.md']
    files={n:(HERE/'candidate'/n).read_bytes() for n in names}
    original={n:(PARENT/'candidate'/n).read_bytes() for n in names}
    changed=[n for n in names if files[n]!=original[n]]
    assert changed==['prompts/main.md']
    assert b'{' not in files['prompts/main.md']
    assert len(files['prompts/main.md'].split())<=950
    assert sha_file(PARENT/'submission.zip')=='13968b67844d1041bfb79b9f11fc21ae66fb36aee5b00d3b91c526d5d35da329'
    raw=archive(files);write_new(HERE/'submission.zip',raw)
    emit(HERE/'candidate.json',dict(name='S2-T500-EarlyEGV-Closure-V0.1',base_commit='59eda9c0c100e77fdd6aacee90feb4823f2cfe4b',
        directory='s2/egv_agenttool_t500_early_v01/candidate',zip_sha256=hashlib.sha256(raw).hexdigest(),
        members={n:hashlib.sha256(b).hexdigest() for n,b in files.items()},changed_members=changed,
        parent_zip_sha256=sha_file(PARENT/'submission.zip'),model='gemma-4-31b-it-qat-w4a16-ct',
        budget=dict(seconds=500,counted_tools=60,command_seconds=120),
        generation=dict(output_tokens=16384,thinking_budget=4096,seed=17,include_thoughts=None),
        treatment='Joint early-delegation/investigation/closure workflow in Main Prompt; contributions not separately identified',
        GPU_authorized=False,formal_submission_authorized=False,LoRA=False))


def build(revision):
    package()
    previous=json.loads((SMOKE/'notebooks/gpu01/study.ipynb').read_text())
    setup=previous['cells'][0]['source']
    line=next(s for s in setup.splitlines() if s.startswith("payload=__import__('base64').b64decode("))
    encoded=ast.literal_eval(line[len("payload=__import__('base64').b64decode("):-1])
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as z:
        assert z.testzip() is None
        files={n:z.read(n) for n in z.namelist()}
    # Legacy code is the immutable official-CPU-accepted payload, not rebuilt
    # from historical working-tree copies with different registration files.
    for n in ('s2/smoke_authorization.json','s2/smoke_cpu_gate.json','s2/smoke_protocol.json'):
        files.pop(n,None)
    for p in HERE.rglob('*'):
        rel=p.relative_to(HERE)
        if p.is_file() and not {'_local','results','notebooks','registrations','__pycache__'}.intersection(rel.parts) and (p.suffix=='.py' or 'candidate' in rel.parts or p.name in ('candidate.json','submission.zip')):
            files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    reg=dict(revision=revision,GPU=False,Gemma_inference=False,source_hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()},
        parent_source='59eda9c smoke GPU payload; candidate/runtime frozen',candidate=json.loads((HERE/'candidate.json').read_text()))
    emit(HERE/'registrations'/f'{revision}.json',reg)
    files['s2/early_registration.json']=(HERE/'registrations'/f'{revision}.json').read_bytes()
    payload=archive(files)
    start=setup.index("payload=__import__('base64').b64decode(");end=setup.index('with zipfile.ZipFile',start)
    setup=setup[:start]+"payload=__import__('base64').b64decode("+repr(base64.b64encode(payload).decode())+")\nassert hashlib.sha256(payload).hexdigest()=="+repr(hashlib.sha256(payload).hexdigest())+"\n"+setup[end:]
    setup=setup[:setup.index('\nPLAN=')]
    setup=setup.replace("Path('/kaggle/working/s2_t500_agenttool_smoke_01')/'gpu01'/", "Path('/kaggle/working/s2_t500_early_v01')/"+repr(revision)+"/")
    setup+="\nEARLY=json.loads((SOURCE/'s2/early_registration.json').read_text())\nfor n,h in EARLY['source_hashes'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n\nprint('EARLY_SOURCES_VERIFIED',flush=True)\n"
    install=previous['cells'][1]['source'];install=install[:install.index('    from s2.experiments.t500_agenttool_smoke_01.session import run')]
    install=install.replace('timeout=300','timeout=1800')
    install+="    with (RUN_DIR/'cpu.log').open('x') as log:\n        result=subprocess.run([sys.executable,'-m','s2.egv_agenttool_t500_early_v01.cpu',str(RUN_DIR/'validation')],stdout=log,stderr=subprocess.STDOUT,timeout=5400)\n    assert result.returncode==0,(RUN_DIR/'cpu.log').read_text()[-8000:]\nfinally:print('EARLY_CPU_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for s in (setup,install):
        compile(s,'<early CPU Notebook>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=s,outputs=[],execution_count=None,id=hashlib.sha256(s.encode()).hexdigest()[:12]))
    raw=(json.dumps(dict(cells=cells,metadata=previous['metadata'],nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
    assert len(raw)<900000
    folder=HERE/'notebooks'/revision;write_new(folder/'study.ipynb',raw)
    meta=json.loads((SMOKE/'notebooks/cpu02/kernel-metadata.json').read_text());slug='gemma4-s2-early-egv-'+revision
    meta.update(id='wudangdexiaodoashi/'+slug,title=slug,enable_gpu=False);meta.pop('machine_shape',None)
    emit(folder/'kernel-metadata.json',meta)
    emit(HERE/(revision+'_freeze.json'),dict(kernel=meta['id'],notebook_sha256=sha_file(folder/'study.ipynb'),
        metadata_sha256=sha_file(folder/'kernel-metadata.json'),payload_sha256=hashlib.sha256(payload).hexdigest(),GPU=False))
    print(folder)


if __name__=='__main__':build(sys.argv[1])
