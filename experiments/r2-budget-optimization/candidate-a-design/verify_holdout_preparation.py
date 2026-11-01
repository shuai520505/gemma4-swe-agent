"""Check identities, fail-closed results and unresolved session slots independently."""
import hashlib,json,random
from pathlib import Path

D=Path(__file__).resolve().parent;O=D/'holdout-preparation';B=D.parent;ROOT=B.parents[1]
read=lambda p:json.loads(p.read_bytes())
sha=lambda b:hashlib.sha256(b).hexdigest()
registry=read(O/'EXPOSURE_REGISTRY.json');pool=read(O/'PUBLIC_POOL_IDENTITIES.json')
gate=read(O/'PREPARATION_GATE.json');native=read(O/'NATIVE_CPU_CONTRACT_RESULT.json')
slots=read(O/'SESSION_ORDER_TEMPLATE.json');rules=read(O/'HOLDOUT_SELECTION_RULES.json')
for p,h in (read(B/'FROZEN_INPUT_IDENTITIES.json')|read(B/'HISTORY_ADDITIONAL_IDENTITIES.json')).items():assert sha(Path(p).read_bytes())==h,p
published=read(B/'publication/PUBLIC_EXPECTED.json')
for p,row in published.items():assert sha((ROOT/p).read_bytes())==row['sha256'],p
for record in registry['inventory']:assert sha(Path(record['path']).read_bytes())==record['sha256'],record['path']
for p,h in gate['input_hashes'].items():assert sha((D/p).read_bytes())==h,p
assert not registry['read_errors'] and len(pool['rows'])==129
ids={x['instance_id'] for x in pool['rows']}
assert ids<=set(registry['excluded_ids']) and registry['remaining_count']==0 and not rules['selected_task_ids']
assert all(set(row)=={'instance_id','repo','base_commit','issue_sha256'} for row in pool['rows'])
assert len(slots['sessions'])==8 and all(s['instance_id'] is None and s['status']=='NOT_RUN' for s in slots['sessions'])
orders=['R2_A','R2_A','A_R2','A_R2'];random.Random(20261031).shuffle(orders);assert orders==slots['paired_orders']
assert len(native['junit_cases'])==8 and all(c['actual']==c['expected'] and c['passed'] for c in native['junit_cases'])
assert native['missing_spec_guard']['resolved'] is False and not native['missing_spec_guard']['sandbox_started']
assert native['native_resolved'] is None and native['complete_verify_task_lifecycle']=='NOT_RUN'
assert gate['status']=='PREPARATION_BLOCKED_HOLDOUT_AND_NATIVE_RUNTIME' and not gate['frozen_full_task_session_order']
assert sha(Path(native['official_verification_file']).read_bytes())==native['official_verification_sha256']
result={'status':'PASS_BLOCKED_STATE_AND_IMMUTABILITY_VERIFIED','historical_inputs_unchanged':74,'previously_published_files_unchanged':len(published),'historical_source_registries_rehashed':len(registry['inventory']),'projected_pool_rows':129,'eligible_tasks':0,'session_slots_NOT_RUN':8,'native_contract_cases_passed':8,'genuine_native_task_evaluation':'NOT_RUN','originals_modified':False,'GPU_requests':0,'model_requests':0,'formal_submissions':0}
(O/'PREPARATION_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(result))
