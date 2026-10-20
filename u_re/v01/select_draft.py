"""Metadata-only deterministic draft selection; no reference repairs consumed."""
import hashlib
import json
from pathlib import Path
from .build import HERE,write


def select(tasks_path,exclusions):
    excluded=set(json.loads(Path(exclusions).read_text())['excluded_task_ids'])
    rows=[]
    for line in Path(tasks_path).read_text(encoding='utf-8').splitlines():
        raw=json.loads(line)
        # Restrict the consumer to identity/Issue fields. No evaluator patch,
        # reference solution or test content is accessed or fed to a candidate.
        row={k:raw[k] for k in ('instance_id','repo','base_commit','problem_statement')}
        if row['instance_id'] not in excluded:
            rows.append(row)
    rows.sort(key=lambda r:hashlib.sha256(('U-RE-V0.1:17:'+r['instance_id']).encode()).hexdigest())
    selected=[];repos=set()
    for row in rows:
        if row['repo'] in repos:
            continue
        repos.add(row['repo']);i=len(selected)
        selected.append(dict(instance_id=row['instance_id'],repo=row['repo'],base_commit=row['base_commit'],
            issue_sha256=hashlib.sha256(row['problem_statement'].encode()).hexdigest(),
            metadata_sha256=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            order=['A','B'] if i%2==0 else ['B','A'],snapshot_identity='CPU_HASH_BINDING_PENDING',
            clean_Verifier_admission='NOT_RUN',prior_own_model_exposure='No hit in recorded metadata exclusion audit; not proof of absence from model pretraining.'))
        if len(selected)==2:
            break
    result=dict(experiment_id='U-RE-V01-MECHANISM-01-DRAFT',status='DRAFT_NOT_REGISTERED_FOR_EXECUTION',
        selected=selected,pool_remaining_after_conservative_exclusions=len(rows),
        rule='Rank all remaining IDs by SHA256(U-RE-V0.1:17:+ID); take first two distinct repositories. No difficulty/outcome/reference-patch filtering.',
        execute=False,GPU_authorized=False,if_insufficient_or_environment_fails='Stop draft promotion; no post-result task substitution')
    write(HERE/'GPU_TASK_SELECTION_DRAFT.json',(json.dumps(result,indent=2)+'\n').encode())
    return result


if __name__=='__main__':
    import sys
    print(json.dumps(select(sys.argv[1],sys.argv[2]),indent=2))
