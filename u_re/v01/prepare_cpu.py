"""Build a new immutable CPU-only Notebook; no GPU execution capability."""
import ast
import base64
import io
import json
from pathlib import Path
import sys
import zipfile
from .build import HERE,ROOT,S0,S1,sha,write,archive,git_bytes


def build(revision,stage):
    assert revision.startswith('cpu') and stage in ('smoke','full')
    old=json.loads((ROOT/'s1/egv_v01/notebooks/cpu03/study.ipynb').read_text())
    setup=old['cells'][0]['source']
    line=next(s for s in setup.splitlines() if s.startswith("payload=__import__('base64').b64decode("))
    encoded=ast.literal_eval(line[len("payload=__import__('base64').b64decode("):-1])
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as z:
        assert z.testzip() is None;files={n:z.read(n) for n in z.namelist()}
    previous=json.loads(files['s1/registration.json'])
    for n,h in previous['source_hashes'].items():
        assert sha(files[n])==h,n
    for file in HERE.rglob('*'):
        rel=file.relative_to(HERE)
        if file.is_file() and not {'results','notebooks','_local','__pycache__'}.intersection(rel.parts):
            if file.suffix=='.py' or file.name in ('CANDIDATES.json','submission_full.zip','submission_noegv.zip') or rel.parts[0].startswith('candidate_'):
                files[file.relative_to(ROOT).as_posix()]=file.read_bytes()
    files['u_re/v01/reference_prompts/s0.txt']=git_bytes(S0,'candidates/s0/submission/prompts/system.md')
    files['u_re/v01/reference_prompts/s1.txt']=git_bytes(S1,'s1/egv_v01/candidate/prompts/system.md')
    # Static tests compare the actual three compositional Prompt source files.
    for p in (HERE/'prompts').glob('*.md'):
        files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    reg=dict(revision=revision,stage=stage,source_base=S1,GPU=False,model_inference=False,
        source_hashes={n:sha(b) for n,b in files.items()},candidate=json.loads((HERE/'CANDIDATES.json').read_text()),
        official_wheel_hashes=previous['wheel_hashes'])
    write(HERE/'registrations'/f'{revision}.json',(json.dumps(reg,indent=2)+'\n').encode())
    files['u_re/v01/runtime_registration.json']=(HERE/'registrations'/f'{revision}.json').read_bytes()
    payload=archive(files)
    start=setup.index("payload=__import__('base64').b64decode(");end=setup.index('with zipfile.ZipFile',start)
    setup=setup[:start]+"payload=__import__('base64').b64decode("+repr(base64.b64encode(payload).decode())+")\nassert hashlib.sha256(payload).hexdigest()=="+repr(sha(payload))+"\n"+setup[end:]
    setup=setup.replace("Path('/kaggle/working/s1_egv_v01')/'cpu03'/", "Path('/kaggle/working/u_re_v01')/"+repr(revision)+"/")
    setup=setup[:setup.index("os.environ.update(VLLM_WORKER")]
    setup+="\nURE=json.loads((SOURCE/'u_re/v01/runtime_registration.json').read_text())\nassert URE['GPU'] is False\nfor n,h in URE['source_hashes'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n\nprint('URE_CPU_SOURCES_VERIFIED',flush=True)\n"
    from s1.prepare import INSTALL,IMAGE,MODEL_REF
    execute=INSTALL+"\nwith (RUN_DIR/'cpu.log').open('x') as log:\n    result=subprocess.run([sys.executable,'-m','u_re.v01.cpu',str(RUN_DIR/'validation'),"+repr(stage)+"],cwd=SOURCE,stdout=log,stderr=subprocess.STDOUT,timeout=3000)\nprint('URE_CPU_EXIT',result.returncode,flush=True)\nassert result.returncode==0,'CPU acceptance failed: preserve evidence'\n"
    code="from harness_v2.evidence import bundle\ntry:\n"+''.join('    '+l+'\n' for l in execute.splitlines())+"finally:print('URE_CPU_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for s in (setup,code):
        compile(s,'<U-RE CPU Notebook>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=s,outputs=[],execution_count=None,id=sha(s.encode())[:12]))
    notebook=(json.dumps(dict(cells=cells,metadata=old['metadata'],nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
    slug='gemma4-u-re-v01-'+revision
    meta=dict(id='wudangdexiaodoashi/'+slug,title=slug,code_file='study.ipynb',language='python',kernel_type='notebook',
        is_private=True,enable_gpu=False,enable_tpu=False,enable_internet=False,competition_sources=['gemma-4-developer-agent'],
        dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],model_sources=[MODEL_REF],kernel_sources=[],
        docker_image=IMAGE,docker_image_pinning_type='original')
    folder=HERE/'notebooks'/revision;write(folder/'study.ipynb',notebook)
    write(folder/'kernel-metadata.json',(json.dumps(meta,indent=2)+'\n').encode())
    freeze=dict(kernel=meta['id'],stage=stage,GPU=False,notebook_sha256=sha(notebook),metadata_sha256=sha((folder/'kernel-metadata.json').read_bytes()),
        payload_sha256=sha(payload),candidate=reg['candidate'],execution_status='NOT_RUN')
    write(HERE/'registrations'/f'{revision}_build.json',(json.dumps(freeze,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in freeze.items() if k!='candidate'},indent=2))


if __name__=='__main__':
    build(sys.argv[1],sys.argv[2])
