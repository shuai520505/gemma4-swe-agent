"""Re-derive actual packaged CPU acceptance using the validated GPU03 auditor."""
import inspect,json,zipfile
from pathlib import Path
from .dependencies import HERE,ROOT,sha,write
from .production_notebook import PRODUCTION

def audit(archive,attempt='e2e02'):
    from u_re.v01.experiments.action_priority_01.real_gemma_abba03 import cpu_acceptance as proven
    source=inspect.getsource(proven.audit)
    source=source.replace("f['file']==attempt+'.zip'","f['file']=='v02b-'+attempt+'.zip'")
    source=source.replace("(HERE/'GPU03_PAYLOAD_MANIFEST.json')","(PRODUCTION/'GPU03_PAYLOAD_MANIFEST.json')")
    source=source.replace('GPU03_PAYLOAD_END_TO_END_CPU_PASS','V02B_PAYLOAD_END_TO_END_CPU_PASS')
    namespace=dict(proven.__dict__,HERE=HERE,ROOT=ROOT,PRIOR=PRODUCTION,PRODUCTION=PRODUCTION)
    exec(compile(source,'<Reused-GPU03-version-bound-raw-auditor>','exec'),namespace)
    proof=namespace['audit'](archive,attempt)
    with zipfile.ZipFile(archive) as z:
        before=json.loads(z.read('PRODUCTION_ENVIRONMENT_BEFORE.json'))
        after=json.loads(z.read('PRODUCTION_ENVIRONMENT_AFTER.json'))
        assert before==after==json.loads((HERE/'V02B_ENVIRONMENT_LOCK.json').read_bytes())['fingerprint']
        assert json.loads(z.read('results/CPU_ACCEPTANCE.json'))['native_real_baselines']==[t['identity']['instance_id'] for t in json.loads((HERE/'SELECTED_TASKS.json').read_bytes())['tasks']]
    proof.update(environment_unchanged=True,environment_lock_sha256=sha((HERE/'V02B_ENVIRONMENT_LOCK.json').read_bytes()),attempt=attempt,Agent_scope='One researcher-owned scripted synthetic task; four real SWE tasks used only for native empty-patch baselines',GPU_authorized=False)
    return proof

if __name__=='__main__':
    import sys
    proof=audit(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else 'e2e02')
    write(HERE/'CPU_END_TO_END_ACCEPTANCE.json',proof)
    print(json.dumps(dict(status=proof['status'],Notebook_id=proof['Notebook_id'],baselines=len(proof['baseline_checks']),HTTP_requests=proof['scripted_HTTP_requests'],payload_sha256=proof['payload_sha256'],archive_sha256=proof['raw_archive_sha256'])))
