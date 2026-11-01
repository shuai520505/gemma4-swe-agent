"""Explicit allowlist: no private trusted specs, runtime distributions or upload logs."""
import base64,hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent
names=['README.md','PROTOCOL_AMENDMENT.json','INTEGRATION_AMENDMENT_01.json','INTEGRATION_AMENDMENT_02.json',
 'TASK_IDENTITY_LOCK.json','EXECUTION_PLAN.json','ISSUES.agent.json','EXPOSURE_AND_SELECTION.json',
 'SOURCE_ACQUISITION.json','OFFICIAL_COMMIT_IDENTITIES.json','XARRAY_ARCHIVAL_ORIGINAL.json','ASSET_MANIFEST.json',
 'PACKAGE_IDENTITY.json','CANDIDATE_A.diff','prepare.py','acquire_assets.py','verify_source_trees.py',
 'freeze_package_identity.py','r2a_runtime.py','r2a_worker.py','r2a_coordinator.py','cpu_worker_replay.py','build_cpu.py',
 'audit_native_matcher.py','NATIVE_MATCHER_AUDIT.json','EVALUATOR_TRUST_GATE.md','verify_frozen_inputs.py',
 'FROZEN_INPUT_VERIFICATION.json','collect_cpu_evidence.py','prepare_publication.py','STUDY_STATUS.json','FINAL_STATUS.md',
 'PENDING_EVALUATION_AMENDMENT.json','independent_exact_evaluator.py']
for version in range(1,9):
    name=f'CPU_ATTEMPT_{version:02d}_SUMMARY.json'
    if (D/name).exists():names.append(name)
rows=[]
for name in names:
    p=D/name
    if not p.is_file():raise RuntimeError('Missing required publication input: '+name)
    raw=p.read_bytes();rows.append(dict(path='experiments/r2-early-decision-01/'+name,mode='100644',type='blob',content=raw.decode('utf8')))
binary=[]
for name in ('R2','A'):
    raw=(D/'candidates'/(name+'.zip')).read_bytes()
    binary.append(dict(path='experiments/r2-early-decision-01/candidates/'+name+'.zip',base64=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()))
(D/'PUBLICATION_PAYLOAD.local.json').write_text(json.dumps(dict(text=rows,binary=binary),ensure_ascii=True),encoding='utf8')
print(json.dumps(dict(text_files=len(rows),binary_files=len(binary),bytes=(D/'PUBLICATION_PAYLOAD.local.json').stat().st_size)))
