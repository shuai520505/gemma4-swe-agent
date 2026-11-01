"""Explicit public evidence allowlist; no credentials, giant notebooks or input assets."""
import base64,hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent;prefix='experiments/r2-infra-hardening-01/'
names=['README.md','FINAL_REPORT.md','stop_policy.py','hardened_runtime.py','hardened_worker.py','hardened_coordinator.py',
 'cpu_integration.py','test_stop_policy.py','build_cpu.py','collect_cpu.py','freeze_inputs.py','finalize.py','prepare_publication.py',
 'BUILD.json','ATTEMPT_01.json','PRIOR_STUDY_IDENTITIES.json','PROTECTED_ASSET_VERIFICATION.json',
 'CPU_INTEGRATION_RESULTS.json','CPU_EVIDENCE_INDEX.json','FINAL_VERIFICATION.json',
 'LEGACY_REGRESSION_FAILURE.txt','LOCAL_TEST_RESULTS.txt','cpu-notebook/kernel-metadata.json',
 'attempt-01/PLATFORM_STATUS.json','attempt-02/PLATFORM_STATUS.json']
names += [p.relative_to(D).as_posix() for p in sorted((D/'evidence').glob('*.json'))]
text=[]
for n in names:
    b=(D/n).read_bytes();text.append(dict(path=prefix+n,mode='100644',type='blob',content=b.decode('utf8')))
binary=[]
for attempt in ['attempt-01','attempt-02']:
    n=attempt+'/r2-infra-cpu-hardening-01.zip';b=(D/n).read_bytes()
    binary.append(dict(path=prefix+n,base64=base64.b64encode(b).decode(),sha256=hashlib.sha256(b).hexdigest()))
payload=json.dumps(dict(text=text,binary=binary),ensure_ascii=True)
(D/'PUBLICATION_PAYLOAD.local.json').write_text(payload,encoding='utf8')
print(json.dumps(dict(text_files=len(text),binary_files=len(binary),chars=len(payload))))
