"""Re-derive final shared-payload CPU gate from version-bound raw evidence."""
import inspect,json,types
from .selection import HERE,ROOT,write
from u_re.v01.experiments.action_priority_01.real_gemma_abba03 import cpu_acceptance as proven

def audit(archive,attempt='cpu-e2e01'):
    source=inspect.getsource(proven.audit)
    source=source.replace("attempt+'.zip'", "'v02-'+attempt+'.zip'")
    source=source.replace("'GPU03_PAYLOAD_MANIFEST.json'","'PAYLOAD_MANIFEST.json'")
    source=source.replace("(PRIOR/'ABBA_EXPERIMENT_LOCK.json')","(HERE/'EXPERIMENT_LOCK.json')")
    source=source.replace('GPU03_PAYLOAD_END_TO_END_CPU_PASS','V02_PAYLOAD_END_TO_END_CPU_PASS')
    module=types.ModuleType('v02_raw_cpu_audit');module.__dict__.update(proven.__dict__);module.HERE=HERE;module.ROOT=ROOT
    exec(compile(source,'<GPU03-derived-CPU-evidence-audit>','exec'),module.__dict__)
    proof=module.audit(archive,attempt)
    assert len(proof['baseline_checks'])==4
    return proof

def seal(archive,attempt='cpu-e2e01'):
    write(HERE/'CPU_END_TO_END_ACCEPTANCE.json',audit(archive,attempt))

def verify():
    expected=json.loads((HERE/'CPU_END_TO_END_ACCEPTANCE.json').read_bytes())
    actual=audit(expected['raw_archive_path'])
    assert actual==expected,'Require actual raw CPU evidence, not a changed flag'
    return actual

if __name__=='__main__':
    import sys
    seal(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else 'cpu-e2e01')
