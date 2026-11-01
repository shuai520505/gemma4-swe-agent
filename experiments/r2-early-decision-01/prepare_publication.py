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
names += ['APPROVED_EVALUATION_AMENDMENT.json','INTEGRATION_AMENDMENT_03.json',
 'BASELINE_SPEC_ANOMALY.json','EVALUATOR_IMPLEMENTATION.md','audit_exact_node_identity.py','EXACT_NODE_IDENTITY_AUDIT.json',
 'check_stop_contract.py','STOP_RULE_CONTRACT.json','CPU_FROZEN_RECEIPT_MANIFEST.json',
 'CPU_FINAL_ATTEMPT_01.json','CPU_FINAL_ATTEMPT_02.json','CPU_FINAL_ATTEMPT_03.json',
 'package_runtime_transport.py','RUNTIME_TRANSPORT_IDENTITY.json','build_overlay_cpu.py','finalize_cpu_receipts.py',
 'build_gpu.py','dispatch_gpu_once.py','watch_gpu.py','record_running_checkpoint.py','GPU_DISPATCH_PACKAGE_MANIFEST.json',
 'analyze_gpu.py','review_cpu.py','finalize_gpu_audit.py','GPU_SESSION_EVIDENCE_INDEX.json',
 'GPU_BEHAVIOR_METRICS.json','GPU_RESOURCE_AND_IDENTITY_AUDIT.json','GPU_TOOL_ERROR_AUDIT.json',
 'POST_RUN_CPU_SEMANTIC_DIAGNOSTICS.json','INDEPENDENT_SEMANTIC_REVIEW.json','PROTOCOL_DEVIATIONS.json',
 'R2A_GPU_RESULTS.json','R2A_GPU_FINAL_REPORT.md',
 'gpu-notebook/BUILD.json','gpu-notebook/kernel-metadata.json','gpu-notebook/GPU_AUTHORIZATION.json',
 'gpu-notebook/DISPATCH_ACCEPTANCE.json','gpu-notebook/GPU_PLATFORM_TERMINAL.json',
 'gpu-notebook/QUOTA_IMMEDIATELY_BEFORE_DISPATCH.json','gpu-notebook/QUOTA_AFTER_TERMINAL.json',
 'gpu-notebook/dispatch/ONE_SHOT_CLAIM.json','gpu-notebook/dispatch/REQUEST_SENT.json',
 'gpu-notebook/dispatch/HTTP.json','gpu-notebook/dispatch/DISPATCH_RECORD.json']
names += [p.relative_to(D).as_posix() for p in sorted((D/'cpu-receipts').glob('*.json'))]
names += [p.relative_to(D).as_posix() for p in sorted((D/'results').rglob('*')) if p.is_file() and p.suffix in ['.json','.patch']]
for version in range(1,9):
    name=f'CPU_ATTEMPT_{version:02d}_SUMMARY.json'
    if (D/name).exists():names.append(name)
rows=[]
remote=json.loads((D/'REMOTE_STUDY_BLOBS.local.json').read_bytes()) if (D/'REMOTE_STUDY_BLOBS.local.json').exists() else {}
for name in names:
    p=D/name
    if not p.is_file():raise RuntimeError('Missing required publication input: '+name)
    raw=p.read_bytes();path='experiments/r2-early-decision-01/'+name
    git_sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if remote.get(path)==git_sha or name=='results/receipts/execution__PAIR_RESULTS.json':continue
    rows.append(dict(path=path,mode='100644',type='blob',content=raw.decode('utf8')))
binary=[]
for name in ('R2','A'):
    raw=(D/'candidates'/(name+'.zip')).read_bytes()
    path='experiments/r2-early-decision-01/candidates/'+name+'.zip'
    if remote.get(path)==hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest():continue
    binary.append(dict(path='experiments/r2-early-decision-01/candidates/'+name+'.zip',base64=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()))
(D/'PUBLICATION_PAYLOAD.local.json').write_text(json.dumps(dict(text=rows,binary=binary),ensure_ascii=True),encoding='utf8')
print(json.dumps(dict(text_files=len(rows),binary_files=len(binary),bytes=(D/'PUBLICATION_PAYLOAD.local.json').stat().st_size)))
