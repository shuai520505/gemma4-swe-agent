"""New CPU payload, standalone declarative ZIP, and immutable preparation IDs."""
import ast
import base64
import difflib
import hashlib
import io
import json
from pathlib import Path
import zipfile
from experiments.prepare import write_new
from s1.util import archive, sha_file

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
PARENT=ROOT/'s1/experiments/egv_mechanism_smoke_01'


def dump(path,data):
    write_new(path,(json.dumps(data,indent=2)+'\n').encode())


def package():
    files={p.relative_to(HERE/'candidate').as_posix():p.read_bytes() for p in (HERE/'candidate').rglob('*') if p.is_file()}
    assert set(files)=={'agent.yaml','eval_config.yaml','prompts/main.md','sub_agents/egv_verifier.yaml','sub_agents/egv_verifier.md'}
    assert all(b'{' not in b for n,b in files.items() if n.endswith('.md'))
    raw=archive(files);write_new(HERE/'submission.zip',raw)
    dump(HERE/'candidate.json',dict(name='S2-EGV-AgentTool-T500-V0.1',parent_commit='c979394af8521ed62d9fcca990a260d715f1042c',
        zip_sha256=hashlib.sha256(raw).hexdigest(),members={n:hashlib.sha256(b).hexdigest() for n,b in files.items()},
        model='gemma-4-31b-it-qat-w4a16-ct',generation=dict(output16384=16384,thinking4096=4096,seed=17,include_thoughts=None),
        shared_budget=dict(agent_seconds=500,counted_tool_calls=60,command_seconds=120),GPU_executed=False,
        architecture='Official declarative ADK AgentTool; not an external controller',permission='Auditable, not enforced read-only'))


def cpu(revision, module='s2.egv_agenttool_t500_v01.cpu'):
    package()
    protocol=json.loads((PARENT/'protocol.json').read_text())
    with zipfile.ZipFile(PARENT/'results/gpu/raw.zip') as z:
        files={n:z.read('source/'+n) for n in protocol['source_hashes']}
        for n,h in protocol['source_hashes'].items():assert hashlib.sha256(files[n]).hexdigest()==h,n
        for n in ('s1/registration.json','s1/gpu_protocol.json','s1/cpu_gate.json'):
            files[n]=z.read('source/'+n)
    for p in HERE.rglob('*'):
        if p.is_file() and not {'_local','results','notebooks','__pycache__','registrations'}.intersection(p.relative_to(HERE).parts) and (p.suffix=='.py' or 'candidate' in p.relative_to(HERE).parts or p.name in ('candidate.json','submission.zip','TASK_REUSE_INPUT.json')):
            files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    reg=dict(revision=revision,GPU=False,source_hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()},
             wheel_hashes=protocol['wheel_hashes'],task_wheel_hashes=protocol['task_wheel_hashes'],
             parent_cpu_archive=sha_file(PARENT/'results/cpu03/raw.zip'),candidate=json.loads((HERE/'candidate.json').read_text()))
    dump(HERE/f'registrations/{revision}.json',reg)
    files['s2/registration.json']=(HERE/f'registrations/{revision}.json').read_bytes()
    payload=archive(files)
    previous=json.loads((PARENT/'notebooks/cpu03/study.ipynb').read_text())
    setup=previous['cells'][0]['source'];start=setup.index("payload=__import__('base64').b64decode(");end=setup.index('with zipfile.ZipFile',start)
    setup=setup[:start]+"payload=__import__('base64').b64decode("+repr(base64.b64encode(payload).decode())+")\nassert hashlib.sha256(payload).hexdigest()=="+repr(hashlib.sha256(payload).hexdigest())+"\n"+setup[end:]
    setup=setup.replace('s1_egv_mechanism_smoke_01','s2_egv_agenttool_t500_v01').replace("/'cpu03'/",'/'+repr(revision)+'/')
    setup+="\nS2REG=json.loads((SOURCE/'s2/registration.json').read_text())\nfor n,h in S2REG['source_hashes'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n\n"
    # Preserve the organizer wheelhouse install and exception/finally bundling.
    execute=previous['cells'][1]['source'].replace('s1.experiments.egv_mechanism_smoke_01.cpu',module).replace('EGV_MECHANISM_CPU_EVIDENCE','S2_CPU_EVIDENCE')
    if module.endswith('.environments'):execute=execute.replace('timeout=3600','timeout=18000')
    cells=[]
    for s in (setup,execute):
        compile(s,'<CPU notebook>', 'exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=s,outputs=[],execution_count=None,id=hashlib.sha256(s.encode()).hexdigest()[:12]))
    raw=(json.dumps(dict(cells=cells,metadata=previous['metadata'],nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
    folder=HERE/'notebooks'/revision;write_new(folder/'study.ipynb',raw)
    metadata=json.loads((PARENT/'notebooks/cpu03/kernel-metadata.json').read_text())
    metadata.update(id='wudangdexiaodoashi/gemma4-s2-t500-'+revision,title='gemma4-s2-t500-'+revision,enable_gpu=False)
    dump(folder/'kernel-metadata.json',metadata)
    dump(HERE/f'{revision}_notebook.json',dict(kernel=metadata['id'],notebook_sha256=hashlib.sha256(raw).hexdigest(),
         payload_sha256=hashlib.sha256(payload).hexdigest(),status_at_preparation='not_executed',GPU=False))
    print(folder)


if __name__=='__main__':
    import sys
    cpu(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else 's2.egv_agenttool_t500_v01.cpu')
