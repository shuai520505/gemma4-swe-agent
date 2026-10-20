"""One separately frozen CPU-only diagnostic build, no candidate/historical writes."""
import ast
import base64
import io
import json
from pathlib import Path
import subprocess
import zipfile
from u_re.v01.build import archive, sha, write, ROOT

HERE=Path(__file__).resolve().parent
MODULE='u_re.v01.infrastructure.requests_7433_fixture_01'


def build():
    reference=ROOT/'u_re/v01/notebooks/cpu03/study.ipynb'
    old=json.loads(reference.read_text())
    setup=old['cells'][0]['source']
    line=next(s for s in setup.splitlines() if s.startswith("payload=__import__('base64').b64decode("))
    encoded=ast.literal_eval(line[len("payload=__import__('base64').b64decode("):-1])
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as z:
        assert z.testzip() is None
        files={n:z.read(n) for n in z.namelist()}
    current=json.loads((ROOT/'u_re/v01/results/cpu03/validation/task_identities.json').read_text())['requests_7433']
    write(HERE/'expected_task.json',(json.dumps(current,indent=2)+'\n').encode())
    # Primary-source downloads and local toy evidence are static inspection only;
    # they must never be uploaded as an executable provider/dependency.
    for p in [*HERE.glob('*.py'),*(HERE/'tests').glob('*.py')]:
        files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    files[(HERE/'expected_task.json').relative_to(ROOT).as_posix()]=(HERE/'expected_task.json').read_bytes()
    reg=dict(base='cd7fe8e19950003b59819c7accf7292ce2e151b9',GPU=False,model_inference=False,Agent_runs=0,
             inherited_cpu03_notebook_sha256=sha(reference.read_bytes()),
             source_hashes={n:sha(b) for n,b in files.items()},
             instructions='One native Requests clean baseline; passive post-native diagnostics; synthetic fixture study outside workspace. No repair/dependency injection.')
    write(HERE/'registrations/cpu01.json',(json.dumps(reg,indent=2)+'\n').encode())
    files[(HERE/'runtime_registration.json').relative_to(ROOT).as_posix()]=(HERE/'registrations/cpu01.json').read_bytes()
    payload=archive(files)
    start=setup.index("payload=__import__('base64').b64decode(")
    end=setup.index('with zipfile.ZipFile',start)
    setup=setup[:start]+"payload=__import__('base64').b64decode("+repr(base64.b64encode(payload).decode())+")\nassert hashlib.sha256(payload).hexdigest()=="+repr(sha(payload))+"\n"+setup[end:]
    setup=setup.replace("Path('/kaggle/working/u_re_v01')/'cpu03'/","Path('/kaggle/working/u_re_fixture_01')/'cpu01'/")
    relative=HERE.relative_to(ROOT).as_posix()
    setup+='\nFIXTURE_REG=json.loads((SOURCE/'+repr(relative+'/runtime_registration.json')+').read_text())\nassert FIXTURE_REG["GPU"] is False\nfor n,h in FIXTURE_REG["source_hashes"].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n\n'
    setup+="(SOURCE/"+repr(relative+'/runtime_paths.json')+").write_text(json.dumps(dict(wheelhouse=str(WHEELHOUSE_DIR))))\n"
    from s1.prepare import INSTALL,IMAGE
    execute=INSTALL+"\nwith (RUN_DIR/'cpu.log').open('x') as log:\n    result=subprocess.run([sys.executable,'-m',"+repr(MODULE+'.diagnose')+",str(RUN_DIR/'validation')],cwd=SOURCE,stdout=log,stderr=subprocess.STDOUT,timeout=1800)\nprint('FIXTURE_DIAGNOSTIC_EXIT',result.returncode,flush=True)\nassert result.returncode==0,'Preserve failed diagnostic evidence'\n"
    code="from harness_v2.evidence import bundle\ntry:\n"+''.join('    '+line+'\n' for line in execute.splitlines())+"finally: print('FIXTURE_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for s in (setup,code):
        compile(s,'<CPU-only fixture diagnostic>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=s,outputs=[],execution_count=None,id=sha(s.encode())[:12]))
    nb=(json.dumps(dict(cells=cells,metadata=old['metadata'],nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
    meta=dict(id='wudangdexiaodoashi/gemma4-u-re-requests-fixture-cpu01',title='gemma4-u-re-requests-fixture-cpu01',
              code_file='study.ipynb',language='python',kernel_type='notebook',is_private=True,
              enable_gpu=False,enable_tpu=False,enable_internet=False,
              competition_sources=['gemma-4-developer-agent'],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],
              model_sources=[],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original')
    write(HERE/'notebooks/cpu01/study.ipynb',nb)
    write(HERE/'notebooks/cpu01/kernel-metadata.json',(json.dumps(meta,indent=2)+'\n').encode())
    freeze=dict(kernel=meta['id'],GPU=False,model_inference=False,
                notebook_sha256=sha(nb),payload_sha256=sha(payload),
                metadata_sha256=sha((HERE/'notebooks/cpu01/kernel-metadata.json').read_bytes()),
                parent=reg['base'],git_source_at_build=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    write(HERE/'registrations/cpu01_build.json',(json.dumps(freeze,indent=2)+'\n').encode())
    print(json.dumps(freeze,indent=2))


if __name__=='__main__':build()
