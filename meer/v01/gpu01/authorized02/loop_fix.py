"""CPU-only Notebook-loop regression proof; shared production stays unchanged."""
import ast,hashlib,json,sys
import zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from .read_preflight import HERE,GPU,save

def sha(b):return hashlib.sha256(b).hexdigest()

def build_cpu():
    directory=HERE/'cpu-awaitfix01';assert not directory.exists()
    old=GPU/'cpu-binding01'
    nb=json.loads((old/'notebook/study.ipynb').read_bytes())
    nb['cells'][0]['source']=nb['cells'][0]['source'].replace('meer-v01-cpu-binding01','meer-v01-cpu-awaitfix01')
    text=nb['cells'][1]['source']
    start=text.index("    with (RUN_DIR/'cpu.log').open('x') as log:")
    end=text.index('\nfinally:',start)
    replacement='''    import asyncio,contextlib
    from meer.v01.gpu01.cpu_validation import run
    loop=asyncio.get_running_loop()
    assert loop.is_running()
    with (RUN_DIR/'cpu.log').open('x') as log:
        with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
            await run(RUN_DIR/'validation')
    (RUN_DIR/'NOTEBOOK_LOOP_ACCEPTANCE.json').write_text(json.dumps(dict(
        status='TOP_LEVEL_AWAIT_OFFICIAL_WORKER_CPU_PASS',CPU_MODEL='SCRIPTED_ONLY',
        running_notebook_loop_observed=True,real_Gemma_requests=0,
        invocation='await run(...) in existing notebook event loop',
        shared_GPU_payload_sha256='38170bc0d6684ea09097d106cb0a4fbcf5fbc67a0b7c061f139ae99bccc558b5')))
'''
    nb['cells'][1]['source']=text[:start]+replacement+text[end:]
    for cell in nb['cells']:
        compile(cell['source'],'<Notebook-top-level-await-regression>', 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cell['id']=sha(cell['source'].encode())[:12]
    raw=(json.dumps(nb,indent=1)+'\n').encode()
    metadata=json.loads((old/'notebook/kernel-metadata.json').read_bytes())
    metadata.update(id='wudangdexiaodoashi/meer-v01-cpu-awaitfix01',title='meer-v01-cpu-awaitfix01')
    directory.joinpath('notebook').mkdir(parents=True)
    (directory/'notebook/study.ipynb').write_bytes(raw);save(directory/'notebook/kernel-metadata.json',metadata)
    b=json.loads((old/'BUILD.json').read_bytes())
    b.update(Notebook_sha256=sha(raw),wire_sha256=sha(json.dumps(nb).encode()),
             slug=metadata['id'],execution_id='MEER-GPU-BINDING-CPU-cpu-awaitfix01')
    save(directory/'BUILD.json',b)
    save(directory/'CPU_SCOPE_AUTHORIZATION.json',dict(evidence_source='Existing project owner authorization for ordinary CPU engineering repair/validation',
         GPU=False,real_Gemma=False,formal_submission=False,reason='Real GPU outer asyncio.run failed before inference; validate direct top-level await using unchanged accepted shared-worker CPU payload'))
    print(json.dumps(dict(CPU_only=True,Notebook_sha256=sha(raw),payload_sha256=b['payload_sha256'])))

def cpu_factory():
    from kaggle import api
    from kaggle.cli import main
    from meer.v01 import notebook as original
    import inspect,contextlib,io
    directory=HERE/'cpu-awaitfix01'
    code=inspect.getsource(original.factory)
    code=code.replace('agent_runs==4','agent_runs==3').replace('agent_runs=4','agent_runs=3')
    from meer.v01.gpu01.cpu_notebook import validate
    ns=dict(original.__dict__,HERE=HERE,ID='MEER-GPU-BINDING-CPU',validate=lambda attempt:validate_cpu())
    exec(compile(code,'<accepted-CPU-controller-awaitfix>','exec'),ns)
    # Factory retains its original bounded identity/slug checks and CPU-only send guard.
    return ns['factory']('cpu-awaitfix01')

def launch_cpu():cpu_factory().launch()

def collect_cpu():
    from .read_preflight import PRIVATE
    cpu_factory().collect(str(PRIVATE/'cpu-awaitfix01'))

def validate_cpu():
    directory=HERE/'cpu-awaitfix01';b=json.loads((directory/'BUILD.json').read_bytes())
    raw=(directory/'notebook/study.ipynb').read_bytes();assert sha(raw)==b['Notebook_sha256']
    assert sha(json.dumps(json.loads(raw)).encode())==b['wire_sha256']
    return True

def audit_cpu(private_read):
    directory=HERE/'cpu-awaitfix01'
    base=Path(private_read)/'evidence_confirmed'
    manifest=json.loads((base/'OUTPUT_MANIFEST.json').read_bytes())
    identity=json.loads((base/'RESOURCE_IDENTITY.json').read_bytes())
    assert identity['state']=='IDENTITY_CONFIRMED' and identity['metadata']['id']==140784340
    assert identity['metadata']['enable_gpu'] is False
    assert manifest['status']=='COMPLETE' and manifest['version_bound_before_after']
    entry=next(r for r in manifest['files'] if r['file']=='meer-v01-cpu-awaitfix01.zip')
    path=base/'output'/entry['file'];assert sha(path.read_bytes())==entry['sha256']
    shared=json.loads((GPU/'PAYLOAD_BUILD.json').read_bytes())
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        for n,h in shared['payload_members'].items():assert sha(z.read('source/'+n))==h,n
        loop=json.loads(z.read('NOTEBOOK_LOOP_ACCEPTANCE.json'))
        assert loop['status']=='TOP_LEVEL_AWAIT_OFFICIAL_WORKER_CPU_PASS'
        assert loop['running_notebook_loop_observed'] and loop['CPU_MODEL']=='SCRIPTED_ONLY'
        result=json.loads(z.read('validation/CPU_ACCEPTANCE.json'))
        assert result['status']=='MEER_GPU_WORKER_CPU_PASS' and result['real_Gemma_requests']==0
        assert [r['arm'] for r in result['records']]==list('ABC')
        for r in result['records']:
            prefix='validation/'+r['arm']+'/'
            raw=z.read(prefix+'worker/official_result.json')
            xml=z.read(prefix+'worker/verifier/phase2.junit.xml')
            assert sha(raw)==r['TaskResult_sha256'] and sha(xml)==r['JUnit_sha256']
            assert json.loads(raw)['resolved'] is True
            tree=ET.fromstring(xml);assert list(tree.iter('testcase')) and not list(tree.iter('failure')) and not list(tree.iter('error'))
            assert r['cleanup_complete'] and json.loads(z.read(prefix+'TRANSPORT_CLEANUP.json'))['complete']
        assert result['records'][1]['mechanism_verdicts']==['CONTRADICTED','SUPPORTED','OBSERVED']
        assert result['records'][2]['mechanism_verdicts']==['UNKNOWN']*3
    proof=dict(status='TOP_LEVEL_AWAIT_OFFICIAL_WORKER_CPU_PASS',Notebook_id=140784340,version=1,
          archive_sha256=entry['sha256'],archive_bytes=entry['bytes'],private_archive_path=str(path.resolve()),
          CPU_MODEL='SCRIPTED_ONLY',real_Gemma_requests=0,shared_GPU_payload_sha256=shared['payload_sha256'],
          shared_production_members_verified=len(shared['payload_members']),synthetic_owned_sessions=3,
          actual_scripted_HTTP_requests=sum(r['actual_HTTP_requests'] for r in result['records']),cleanup=True,
          proof_scope='Actual existing Notebook loop awaited the unchanged official Worker/Guard/Skill/native synthetic chain; not a real GPU model-load proof')
    save(HERE/'CPU_AWAIT_FIX_ACCEPTANCE.json',proof)
    print(json.dumps(proof));return proof

if __name__=='__main__':
    if sys.argv[1]=='build':build_cpu()
    elif sys.argv[1]=='launch':launch_cpu()
    elif sys.argv[1]=='collect':collect_cpu()
    elif sys.argv[1]=='audit':audit_cpu(sys.argv[2])
