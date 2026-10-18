"""CPU-only official image payload. This module cannot dispatch a GPU run."""
import ast
import base64
import json
from pathlib import Path
import zipfile
from experiments.prepare import write_new
from s1.prepare import IMAGE,INSTALL
from s1.util import archive,save,sha

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent


def build(revision):
    assert revision.startswith('cpu')
    prior=ROOT/'s1/experiments/e3_structured_smoke_04'
    registration=json.loads((prior/'registration_cpu02.json').read_text())
    with zipfile.ZipFile(prior/'results/cpu02/raw.zip') as z:
        files={n:z.read('source/'+n) for n in registration['source_hashes']}
    for n,h in registration['source_hashes'].items():assert sha(files[n])==h
    for file in HERE.rglob('*'):
        if not file.is_file() or {'_local','results','notebooks','__pycache__'}.intersection(file.relative_to(HERE).parts):continue
        if file.suffix in ('.py','.patch') or file.name in ('candidate.json','submission.zip') or 'candidate' in file.relative_to(HERE).parts:
            files[file.relative_to(ROOT).as_posix()]=file.read_bytes()
    registration=dict(registration,egv_identity='S1-EGV-V0.1',egv_parent='f9e9e61276a375e886b57839879e9490144d01a3',
        source_hashes={n:sha(b) for n,b in sorted(files.items())},GPU_permitted=False)
    save(HERE/('registration_'+revision+'.json'),registration)
    files['s1/registration.json']=(HERE/('registration_'+revision+'.json')).read_bytes()
    payload=archive(files)
    old=json.loads((prior/'notebooks/cpu02/study.ipynb').read_text())
    setup=old['cells'][0]['source']
    start=setup.index("payload=__import__('base64').b64decode(")
    end=setup.index('with zipfile.ZipFile',start)
    setup=setup[:start]+"payload=__import__('base64').b64decode("+repr(base64.b64encode(payload).decode())+")\nassert hashlib.sha256(payload).hexdigest()=="+repr(sha(payload))+"\n"+setup[end:]
    setup=setup.replace('s1_e3_structured_smoke_04','s1_egv_v01').replace("/'cpu02'/","/"+repr(revision)+"/")
    execute="p=subprocess.run([sys.executable,'-m','s1.egv_v01.cpu',str(RUN_DIR/'validation')],cwd=SOURCE,capture_output=True,text=True,timeout=3600)\n(RUN_DIR/'runner.stdout.log').write_text(p.stdout)\n(RUN_DIR/'runner.stderr.log').write_text(p.stderr)\nprint(p.stdout+p.stderr,flush=True)\nassert p.returncode==0,'EGV CPU gate or attribution incomplete'\n"
    code='from harness_v2.evidence import bundle\ntry:\n'+''.join('    '+line+'\n' for line in (INSTALL+'\n'+execute).splitlines())+"finally:print('EGV_CPU_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for source in (setup,code):
        compile(source,'<CPU notebook>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=source,outputs=[],execution_count=None,id=sha(source.encode())[:12]))
    raw=(json.dumps(dict(cells=cells,metadata=old['metadata'],nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
    folder=HERE/'notebooks'/revision
    write_new(folder/'study.ipynb',raw)
    slug='gemma4-s1-egv01-'+revision
    save(folder/'kernel-metadata.json',dict(id='wudangdexiaodoashi/'+slug,title=slug,code_file='study.ipynb',language='python',kernel_type='notebook',is_private=True,enable_gpu=False,enable_tpu=False,enable_internet=False,competition_sources=['gemma-4-developer-agent'],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],model_sources=[],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original'))
    save(HERE/(revision+'_notebook.json'),dict(kernel='wudangdexiaodoashi/'+slug,notebook_sha256=sha(raw),payload_sha256=sha(payload),status_at_preparation='not_executed',GPU=False))
    print(folder)


if __name__=='__main__':
    import sys
    build(sys.argv[1])
