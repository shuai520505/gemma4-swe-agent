"""Build only after two evidence-derived formal admissions; no GPU dispatch."""
import ast,base64,inspect,io,json,subprocess,types,zipfile
from .common import HERE,ROOT,PRIOR,ID,PACKAGE,BASE,sha,write
from . import notebook
from u_re.v04.experiments.evidence_guided_repair_01 import notebook as accepted

def build_payload():
    assert not (HERE/'payload.zip').exists()
    selected=json.loads((HERE/'SELECTED_TASKS.json').read_bytes());assert selected['status']=='TWO_TASKS_FORMALLY_ADMITTED' and len(selected['tasks'])==2
    normalized=json.loads((HERE/'NORMALIZED_ADMISSION_VIEW.json').read_bytes());assert normalized['status']=='TWO_TASKS_FORMALLY_ADMITTED' and normalized['stop'] is None
    lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    lock.update(experiment_id='U-RE-V04-EGR-REPLICATION',preparation_experiment=ID,tasks=selected['tasks'],environment_lock_sha256=sha((HERE/'ENVIRONMENT_LOCK.json').read_bytes()),order=[dict(run=2*i+j+1,instance_id=t['instance_id'],arm=a) for i,t in enumerate(selected['tasks']) for j,a in enumerate(('A','B') if i==0 else ('B','A'))])
    lock['selected_tasks_sha256']=sha((HERE/'SELECTED_TASKS.json').read_bytes());lock['GPU_authorized']=False
    write(HERE/'ABBA_EXPERIMENT_LOCK.json',lock)
    write(HERE/'ADMISSION_RECONCILIATION.json',dict(status='EVIDENCE_RECONCILED_TWO_TASKS_ADMITTED',tasks=[dict(instance_id=t['instance_id']) for t in selected['tasks']],normalized_admission_view_sha256=sha((HERE/'NORMALIZED_ADMISSION_VIEW.json').read_bytes())))
    with zipfile.ZipFile(PRIOR/'payload.zip') as z:files={n:z.read(n) for n in z.namelist() if n!='gpu_registration.json'}
    for name in ('__init__.py','common.py','worker.py','session.py','ABBA_EXPERIMENT_LOCK.json','ADMISSION_RECONCILIATION.json','ENVIRONMENT_LOCK.json'):
        p=HERE/name;files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    from u_re.v01.experiments.action_priority_01.real_gemma_abba02 import import_closure
    closure=types.FunctionType(import_closure.complete.__code__,dict(import_closure.complete.__globals__,ENTRYPOINTS=(PACKAGE+'.session',PACKAGE+'.worker')))
    files,graph=closure(files)
    reg=dict(execution_id=ID,production_entry=PACKAGE+'.session.run',worker_entry=PACKAGE+'.worker',files={n:sha(b) for n,b in files.items()},wheel_hashes=lock['official_wheels'])
    files['gpu_registration.json']=(json.dumps(reg,indent=2)+'\n').encode();buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(files.items()):
            info=zipfile.ZipInfo(n,(2026,10,23,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
    raw=buffer.getvalue();write(HERE/'payload.zip',raw)
    write(HERE/'GPU03_PAYLOAD_MANIFEST.json',dict(payload_sha256=sha(raw),bytes=len(raw),**reg,source_base=BASE,import_closure=graph,CPU_transport_in_payload=False,GPU_authorized=False))
    # External CPU-only transmission fixture, unchanged from PR29.
    write(HERE/'cpu_transport.py',(PRIOR/'cpu_transport.py').read_bytes())
    print(json.dumps(dict(payload_sha256=sha(raw),order=lock['order'],GPU_authorized=False)))

def build_cpu(attempt):
    code=inspect.getsource(accepted.build_cpu)
    code=code.replace('gemma4-u-re-v04-','gemma4-u-re-v04adm-').replace("'v04-'+directory.name","'v04adm-'+directory.name")
    ns=dict(accepted.__dict__,HERE=HERE,ROOT=ROOT,ID=ID,PACKAGE=PACKAGE,validate=validate)
    exec(compile(code,'<Reused-PR29-final-payload-CPU-builder>','exec'),ns);ns['build_cpu'](attempt)

def validate(attempt):
    return types.FunctionType(accepted.validate.__code__,dict(accepted.__dict__,HERE=HERE))(attempt)

def factory(attempt):
    code=inspect.getsource(accepted.factory)
    code=code.replace('gemma4-u-re-v04-','gemma4-u-re-v04adm-').replace("'v04-'+attempt","'v04adm-'+attempt")
    code=code.replace('Current V04 instruction authorizes CPU-only final-package acceptance of frozen Action-First and EGR instructions with two owned scripted Agent runs and development-only baseline rechecks. No GPU/Gemma/Competition Submission.','Current V04 prospective admission task authorizes final sealed-payload CPU acceptance of the two actually admitted tasks and two owned scripted Agent runs; no GPU,real Gemma or Competition Submission.')
    ns=dict(accepted.__dict__,HERE=HERE,ROOT=ROOT,ID=ID,validate=validate)
    exec(compile(code,'<Reused-final-CPU-one-dispatch-controller>','exec'),ns);return ns['factory'](attempt)

if __name__=='__main__':
    import sys
    cmd=sys.argv[1];attempt=sys.argv[2] if len(sys.argv)>2 else 'cpu-e2e01'
    if cmd=='payload':build_payload()
    elif cmd=='build':build_cpu(attempt)
    elif cmd=='launch':factory(attempt).launch()
    elif cmd=='collect':factory(attempt).collect(sys.argv[3])
