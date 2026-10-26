"""Conservative metadata-only eligibility gate, no baselines or answer inspection."""
from collections import Counter
import hashlib
import json
from pathlib import Path

from .build import HERE, ROOT, frozen_write, sha

PROTOCOL = 'u_re/v04/experiments/evidence_guided_repair_01/GPU_REPLICATION_PROTOCOL.json'
ADMISSION = 'u_re/v04/experiments/prospective_admission_01/ADMISSION_PROTOCOL_LOCK.json'
TASK_SHA = 'e4b3fd60f69dbc2b9213e54eeb9636db78aefe92c1d06269d73d9f5f8f3c8ad6'
PREFIX = 'EGRD-V022-MEER-ADOPTION:17:'


def audit_pool():
    p=json.loads((ROOT/PROTOCOL).read_bytes());admission=json.loads((ROOT/ADMISSION).read_bytes())
    assert admission['inherited_protocol_sha256']==sha((ROOT/PROTOCOL).read_bytes())
    for name,digest in p['sources'].items():assert sha((ROOT/name).read_bytes())==digest
    raw=(ROOT.parent/'official-inputs/tasks.jsonl').read_bytes()
    assert sha(raw)==TASK_SHA==admission['tasks_file_sha256']
    previous=set(p['excluded_ids']);reserved={r['instance_id'] for r in p['ranked_candidates']}
    assert len(previous)==124 and len(reserved)==5 and not previous&reserved
    metadata=[]
    for line in raw.splitlines():
        if not line.strip():continue
        row=json.loads(line)
        # Only metadata is projected. Reference patch and evaluator fields are
        # neither inspected, compared nor used to choose tasks.
        identity=row['instance_id']
        reasons=[]
        if identity in previous:reasons.append('PRESERVED_HISTORICAL_EXCLUSION_OR_RESERVATION')
        if identity in reserved:reasons.append('PR29_PR30_RESERVED_OR_ANALYZED_PROSPECTIVE_IDENTITY')
        metadata.append(dict(instance_id=identity,repo=row['repo'],base_commit=row['base_commit'],
            issue_sha256=sha(row['problem_statement'].encode()),task_record_sha256=sha(line),
            excluded_reasons=reasons,admission='NOT_ADMITTED',baseline='NOT_RUN'))
    assert len(metadata)==129 and len({r['instance_id'] for r in metadata})==129
    assert {r['instance_id'] for r in metadata}==previous|reserved
    by_id={r['instance_id']:r for r in metadata}
    for old in p['ranked_candidates']:
        assert all(by_id[old['instance_id']][k]==old[k] for k in ('repo','base_commit','issue_sha256'))
    eligible=[r for r in metadata if not r['excluded_reasons']]
    eligible.sort(key=lambda r:(hashlib.sha256((PREFIX+r['instance_id']).encode()).hexdigest(),r['instance_id']))
    return dict(experiment='EGRD-V022-MEER-ADOPTION',source_tasks_sha256=TASK_SHA,source_count=129,
        repositories=dict(Counter(r['repo'] for r in metadata)),seed=17,ranking_prefix=PREFIX,
        ordering='SHA256(prefix+instance_id), then instance_id; frozen before any new baseline',
        historical_protocol_sha256=sha((ROOT/PROTOCOL).read_bytes()),
        historical_admission_lock_sha256=sha((ROOT/ADMISSION).read_bytes()),
        inherited_excluded_count=124,preserved_remaining_reservations=5,
        independent_candidates=len(eligible),ranked_candidates=eligible,
        source_record_metadata=metadata,selection='First two formally eligible native negative baselines; no release/refill',
        max_baselines=16,new_baselines_run=0,
        alias_gate='NOT_RUN_NO_UNEXPOSED_CANDIDATES; do not claim snapshot/content alias clearance',
        source_expansion='NOT_VERIFIED: no additional independently verified task source available',
        status='TASK_POOL_EXHAUSTED_BY_HISTORICAL_EXPOSURE_AND_RESERVATIONS')


def build():
    pool=audit_pool()
    frozen_write(HERE/'TASK_POOL_LOCK.json',(json.dumps(pool,indent=2,sort_keys=True)+'\n').encode())
    selected=dict(status='NOT_ADMITTED',selected_count=0,selected_tasks=[],native_baselines_run=0,
        reason='No unexposed/unreserved candidate remains in the verified 129-record source; no replacement source verified',
        snapshot_issue_overlay_environment_identity_complete=False,
        historical_NOT_RUN_reservations_released=False)
    frozen_write(HERE/'SELECTED_TASKS.json',(json.dumps(selected,indent=2,sort_keys=True)+'\n').encode())
    print(json.dumps({k:pool[k] for k in ('source_count','independent_candidates','new_baselines_run')}))
    return pool


if __name__=='__main__':build()
