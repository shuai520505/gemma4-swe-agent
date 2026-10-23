"""Existing accepted CPU Notebook template + durable one-dispatch controls."""
import ast,base64,inspect,io,json,types,zipfile
from .common import HERE,ROOT,PRIOR,BASE,ID,PACKAGE,sha,write
from u_re.v02.experiments.env_recovery_admission_01 import notebook as accepted
from u_re.v04.experiments.evidence_guided_repair_01 import notebook as egr

def freeze():
    assert not (HERE/'ADMISSION_PROTOCOL_LOCK.json').exists()
    from u_re.v04.experiments.evidence_guided_repair_01.audit import audit_cpu
    proof=json.loads((PRIOR/'CPU_END_TO_END_ACCEPTANCE.json').read_bytes())
    assert audit_cpu(proof['raw_archive_path'],proof['attempt'])==proof
    protocol=(PRIOR/'GPU_REPLICATION_PROTOCOL.json').read_bytes();write(HERE/'GPU_REPLICATION_PROTOCOL.json',protocol)
    env=ROOT/'u_re/v02/experiments/env_recovery_admission_01/V02B_ENVIRONMENT_LOCK.json';write(HERE/'ENVIRONMENT_LOCK.json',env.read_bytes())
    order=[r['instance_id'] for r in json.loads(protocol)['ranked_candidates']]
    assert order==['fastapi_13713','fastapi_14297','fastapi_14459','fastapi_14306','fastapi_14455']
    write(HERE/'ADMISSION_PROTOCOL_LOCK.json',dict(experiment_id=ID,source_base=BASE,inherited_protocol_sha256=sha(protocol),environment_sha256=sha(env.read_bytes()),order=order,max_checks=5,target_tasks=2,selection='First two eligible in frozen order, plus mandatory offline Issue/failure relation review',execution_sources={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in (HERE/'screen.py',HERE/'identity.py',HERE/'common.py')},tasks_file_sha256='e4b3fd60f69dbc2b9213e54eeb9636db78aefe92c1d06269d73d9f5f8f3c8ad6',GPU_authorized=False,formal_submission=False))

def build_screen(attempt):
    assert not (HERE/attempt/'BUILD.json').exists()
    with zipfile.ZipFile(PRIOR/'payload.zip') as z:files={n:z.read(n) for n in z.namelist() if n!='gpu_registration.json'}
    for name in ('__init__.py','common.py','identity.py','screen.py','ADMISSION_PROTOCOL_LOCK.json','GPU_REPLICATION_PROTOCOL.json','ENVIRONMENT_LOCK.json'):
        p=HERE/name;files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    catalog=ROOT/'u_re/v01/experiments/mechanism_02/TASK_POOL_METADATA.json';files[catalog.relative_to(ROOT).as_posix()]=catalog.read_bytes()
    from u_re.v01.experiments.action_priority_01.real_gemma_abba02 import import_closure
    closure=types.FunctionType(import_closure.complete.__code__,dict(import_closure.complete.__globals__,ENTRYPOINTS=(PACKAGE+'.screen',)))
    files,graph=closure(files)
    # Reuse the original CPU unpack/install/execute/finally-bundle template.
    code=inspect.getsource(accepted.build)
    code=code[:code.index('    assert not')]+"    files,graph=PREPARED_FILES,IMPORT_GRAPH\n"+code[code.index('    old=json.loads'):]
    code=code.replace('gemma4-u-re-v02b-','gemma4-u-re-v04adm-').replace("'v02b-'+attempt","'v04adm-'+attempt")
    code=code.replace("sha((HERE/('V02B_PROTOCOL_LOCK.json' if entry=='screen' else 'RECOVERY_PROTOCOL.json')).read_bytes())","sha((HERE/'ADMISSION_PROTOCOL_LOCK.json').read_bytes())")
    ns=dict(accepted.__dict__,HERE=HERE,ROOT=ROOT,ID=ID,PACKAGE=PACKAGE,PREPARED_FILES=files,IMPORT_GRAPH=graph,validate_attempt=validate_screen)
    exec(compile(code,'<Reused-accepted-CPU-screen-template>','exec'),ns);ns['build'](attempt,'screen')

def validate_screen(attempt):
    d=HERE/attempt;b=json.loads((d/'BUILD.json').read_bytes());raw=(d/'payload.zip').read_bytes()
    assert sha(raw)==b['payload_sha256'] and not b['configuration']['GPU'] and b['configuration']['Agent_runs']==0
    nb=json.loads((d/'notebook/study.ipynb').read_bytes());assert sha((d/'notebook/study.ipynb').read_bytes())==b['Notebook_sha256']
    assert sha(json.dumps(nb).encode())==b['wire_sha256']
    line=next(l for l in nb['cells'][0]['source'].splitlines() if l.startswith("payload=__import__('base64').b64decode("))
    assert base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))==raw
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        for n,h in b['payload_members'].items():assert sha(z.read(n))==h
        prefix=HERE.relative_to(ROOT).as_posix()+'/'
        protocol=json.loads(z.read(prefix+'ADMISSION_PROTOCOL_LOCK.json'))
        assert sha(z.read(prefix+'GPU_REPLICATION_PROTOCOL.json'))==protocol['inherited_protocol_sha256']
        assert sha(z.read(prefix+'ENVIRONMENT_LOCK.json'))==protocol['environment_sha256']
        assert sha(z.read(prefix+'ADMISSION_PROTOCOL_LOCK.json'))==b['selection_protocol_sha256']
        for n,h in protocol['execution_sources'].items():assert sha(z.read(n))==h
        for n in z.namelist():
            if n.endswith('.py'):compile(z.read(n),n,'exec')
    return True

def factory(attempt,production=False):
    code=inspect.getsource(accepted.factory).replace('gemma4-u-re-v02b-','gemma4-u-re-v04adm-').replace("'v02b-'+attempt","'v04adm-'+attempt")
    code=code.replace('Current attached V02b task explicitly authorizes CPU verified dependency recovery,diagnostic reevaluation,max24 new native screens and final CPU acceptance. No GPU,Gemma or formal Submission authorized by this CPU dispatch.','Current V04 prospective task authorizes CPU original native screening in the fixed five-task order, first two eligible, and final packaged CPU engineering acceptance; no GPU,real Gemma or Competition Submission.')
    ns=dict(accepted.__dict__,HERE=HERE,ROOT=ROOT,ID=ID,validate_attempt=validate_screen)
    exec(compile(code,'<Reused-CPU-durable-V04-admission>','exec'),ns)
    return ns['factory'](attempt)

if __name__=='__main__':
    import sys
    cmd=sys.argv[1];attempt=sys.argv[2] if len(sys.argv)>2 else 'screen01'
    if cmd=='freeze':freeze()
    elif cmd=='build':build_screen(attempt)
    elif cmd=='launch':factory(attempt).launch()
    elif cmd=='collect':factory(attempt).collect(sys.argv[3])
