"""Reuse PR29 byte/source/version CPU auditor with frozen PR26 JUnit counts."""
import inspect,json
from .common import HERE,ROOT,PRIOR,write
from .audit import native_counts

def audit(archive,attempt='cpu-e2e03'):
    from u_re.v04.experiments.evidence_guided_repair_01 import audit as accepted
    code=inspect.getsource(accepted.audit_cpu)
    code=code.replace("'v04-'+attempt+'.zip'","'v04adm-'+attempt+'.zip'")
    code=code.replace("(HERE/'CANDIDATE_BUILD_MANIFEST.json')","(PRIOR/'CANDIDATE_BUILD_MANIFEST.json')")
    code=code.replace("(HERE/'GPU03_PAYLOAD_MANIFEST.json')","(HERE/attempt/'PAYLOAD_MANIFEST.json')")
    code=code.replace('V04_EGR_PAYLOAD_END_TO_END_CPU_PASS','V04_PROSPECTIVE_PAYLOAD_END_TO_END_CPU_PASS')
    code=code.replace('V04_EGR_CPU_READY','V04_EGR_GPU_READY')
    code=code.replace("counts(z.read(root+'phase2.junit.xml'))","native_counts(z,root)")
    namespace=dict(accepted.__dict__,HERE=HERE,ROOT=ROOT,PRIOR=PRIOR,native_counts=native_counts)
    exec(compile(code,'<Reused-actual-CPU-source-and-candidate-audit>','exec'),namespace)
    proof=namespace['audit_cpu'](archive,attempt)
    proof['baselines']=[dict(row,role='NEW_FORMALLY_ADMITTED_TASK_RECHECK') for row in proof['baselines']]
    assert [r['task'] for r in proof['baselines']]==['fastapi_14297','fastapi_14459']
    proof['formal_task_lock_sha256']=namespace['sha']((HERE/'SELECTED_TASKS.json').read_bytes())
    proof['requires_new_GPU_authorization']=True
    return proof

if __name__=='__main__':
    import sys
    proof=audit(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else 'cpu-e2e03')
    write(HERE/'CPU_END_TO_END_ACCEPTANCE.json',proof);print(json.dumps(proof))
