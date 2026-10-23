"""CPU-only packaging/dispatch/collection; reuse existing durable controls."""
import ast,base64,inspect,io,json,types,zipfile
from .common import HERE,ROOT,ID,PACKAGE,BASE,CONTROL_SHA,sha,write
from u_re.v03.experiments.context_budget_01 import notebook as prior
from u_re.v01.experiments.action_priority_01.real_gemma_abba03 import notebook as proven

def build_payload():
    assert not (HERE/'payload.zip').exists(),'Version rather than overwrite an accepted production payload'
    prior.verify_cpu()
    lock=json.loads((prior.HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes());candidate=json.loads((HERE/'CANDIDATE_BUILD_MANIFEST.json').read_bytes())
    lock.update(experiment_id=ID,order=[dict(run=1,instance_id='fastapi_5077',arm='A'),dict(run=2,instance_id='fastapi_5077',arm='B'),dict(run=3,instance_id='fastapi_11355',arm='B'),dict(run=4,instance_id='fastapi_11355',arm='A')])
    lock['arms']={'A':dict(name='Frozen Action-First',ZIP_sha256=CONTROL_SHA),'B':dict(name='Evidence-Guided Repair V04',ZIP_sha256=candidate['treatment_ZIP_sha256'])}
    write(HERE/'ABBA_EXPERIMENT_LOCK.json',lock)
    # These are development-only native environment rechecks, not future GPU samples.
    write(HERE/'ADMISSION_RECONCILIATION.json',dict(status='EVIDENCE_RECONCILED_TWO_TASKS_ADMITTED',tasks=[dict(instance_id=t['instance_id'],role='DEVELOPMENT_ONLY_CPU_ENVIRONMENT_RECHECK') for t in lock['tasks']]))
    with zipfile.ZipFile(prior.HERE/'payload.zip') as z:files={n:z.read(n) for n in z.namelist() if n!='gpu_registration.json'}
    for n in ['u_re/v04/__init__.py','u_re/v04/experiments/__init__.py']:files[n]=(ROOT/n).read_bytes()
    for name in ('__init__.py','common.py','worker.py','session.py','ABBA_EXPERIMENT_LOCK.json','ADMISSION_RECONCILIATION.json','EGR_PROMPT_LOCK.json','EGR_INSTRUCTION_BLOCK.md','CANDIDATE_BUILD_MANIFEST.json','submission_egr_v04.zip'):
        p=HERE/name;files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    for p in (HERE/'candidate_egr_v04').rglob('*'):
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    reg=dict(execution_id=ID,production_entry=PACKAGE+'.session.run',worker_entry=PACKAGE+'.worker',files={n:sha(b) for n,b in files.items()},wheel_hashes=lock['official_wheels'])
    files['gpu_registration.json']=(json.dumps(reg,indent=2)+'\n').encode();stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(files.items()):
            info=zipfile.ZipInfo(n,(2026,10,23,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
    raw=stream.getvalue();write(HERE/'payload.zip',raw)
    write(HERE/'GPU03_PAYLOAD_MANIFEST.json',dict(payload_sha256=sha(raw),bytes=len(raw),**reg,source_base=BASE,CPU_transport_in_payload=False,GPU_authorized=False))
    print('V04_PAYLOAD',sha(raw))

def build_cpu(attempt):
    d=HERE/attempt;assert not (d/'BUILD.json').exists()
    source=inspect.getsource(proven.make_notebook)
    source=source.replace("run_name='u_re_actionfirst_abba03' if gpu else directory.name","run_name='V04_GPU_NOT_AUTHORIZED' if gpu else 'v04-'+directory.name")
    source=source.replace("'wudangdexiaodoashi/gemma4-u-re-abba03-'+directory.name","'wudangdexiaodoashi/gemma4-u-re-v04-'+directory.name")
    source=source.replace("aux=(HERE/'cpu_transport.py').read_bytes()","aux=CPU_TRANSPORT_FILE.read_bytes()")
    aux=(HERE/'cpu_transport.py').read_bytes().replace(b'ORIGINAL_CPU_TRANSPORT_BASE64',base64.b64encode((proven.HERE/'cpu_transport.py').read_bytes()))
    write(d/'CPU_ONLY_TRANSPORT.py',aux)
    ns=dict(proven.__dict__,HERE=HERE,ID=ID,PACKAGE=PACKAGE,CPU_TRANSPORT_FILE=d/'CPU_ONLY_TRANSPORT.py')
    exec(compile(source,'<Reused-CPU-sealed-builder>','exec'),ns);ns['make_notebook']('CPU_DRY_RUN',d)
    b=json.loads((d/'BUILD.json').read_bytes());b['configuration']['Agent_runs']=2;write(d/'BUILD.json',b)
    validate(attempt)
def validate(attempt):
    assert types.FunctionType(prior.validate.__code__,dict(prior.__dict__,HERE=HERE))(attempt)
    b=json.loads((HERE/attempt/'BUILD.json').read_bytes());assert not b['configuration']['GPU'] and b['configuration']['Gemma_calls']==0
    return True
def factory(attempt):
    code=inspect.getsource(prior.cpu_factory).replace("gemma4-u-re-v03-","gemma4-u-re-v04-").replace("'v03-'+attempt","'v04-'+attempt")
    code=code.replace('Current V03 instruction explicitly authorizes packaged CPU production acceptance of both context policies using two owned scripted sessions and two frozen native baselines. No GPU or Gemma or Submission.','Current V04 instruction authorizes CPU-only final-package acceptance of frozen Action-First and EGR instructions with two owned scripted Agent runs and development-only baseline rechecks. No GPU/Gemma/Competition Submission.')
    ns=dict(prior.__dict__,HERE=HERE,ROOT=ROOT,ID=ID,validate=validate)
    exec(compile(code,'<Reused-durable-V04-CPU-controller>','exec'),ns);return ns['cpu_factory'](attempt)
if __name__=='__main__':
    import sys
    cmd=sys.argv[1];attempt=sys.argv[2] if len(sys.argv)>2 else 'cpu-e2e01'
    if cmd=='payload':build_payload()
    elif cmd=='build':build_cpu(attempt)
    elif cmd=='launch':factory(attempt).launch()
    elif cmd=='collect':factory(attempt).collect(sys.argv[3])
