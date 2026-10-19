"""Metadata-only task sampling; never read a reference repair to select tasks."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from s1.prepare import EXPOSED, SELECTED

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ID=re.compile(r'^(fastapi|rich|requests|httpx)_\d+$')
METADATA_ONLY={'ranking','complete_ranking','source_hashes','files','excluded','excluded_ids','exclusion_evidence'}


def main():
    seen=set(EXPOSED)
    for ids in SELECTED.values():seen.update(ids)
    evidence={i:['Curated s1.prepare EXPOSED/SELECTED'] for i in seen}
    def scan(value,source,field=None):
        if isinstance(value,dict):
            for k,v in value.items():
                if k in METADATA_ONLY:continue
                # Known actual task identity fields and explicit selected issue
                # registries; metadata rankings/opaque source hashes excluded.
                if k in ('instance_id','task_id','id','task') and isinstance(v,str) and ID.fullmatch(v):
                    seen.add(v);evidence.setdefault(v,[]).append(source+':'+k)
                if k=='public_issues' and isinstance(v,dict):
                    for ident in v:
                        if ID.fullmatch(ident):seen.add(ident);evidence.setdefault(ident,[]).append(source+':public_issues')
                scan(v,source,k)
        elif isinstance(value,list):
            for v in value:
                if field in ('selected','task_ids','tasks') and isinstance(v,str) and ID.fullmatch(v):
                    seen.add(v);evidence.setdefault(v,[]).append(source+':'+field)
                scan(v,source,field)
    for name in subprocess.check_output(['git','-c','core.longpaths=true','ls-files','-z','--','*.json'],cwd=ROOT).decode().split('\0'):
        if not name or name.startswith('s2/'):continue
        try:scan(json.loads((ROOT/name).read_text(encoding='utf-8')),name)
        except (ValueError,UnicodeError):continue
    rows=[json.loads(l) for l in (ROOT.parent/'official-inputs/tasks.jsonl').read_text(encoding='utf-8').splitlines()]
    prefix='S2-EGV-AGENTTOOL-MULTITASK-01|'
    rank=lambda row:hashlib.sha256((prefix+row['instance_id']).encode()).hexdigest()
    repos=sorted({row['repo'] for row in rows})
    pools={repo:sorted([x for x in rows if x['repo']==repo and x['instance_id'] not in seen],key=rank)[:8] for repo in repos}
    pool=[]
    for n in range(8):
        for repo in repos:
            if len(pools[repo])<=n:continue
            row=pools[repo][n]
            pool.append(dict(instance_id=row['instance_id'],repo=repo,base_commit=row['base_commit'],
                issue_sha256=hashlib.sha256(row['problem_statement'].encode()).hexdigest(),rank=rank(row)))
    result=dict(experiment_id='S2-EGV-AGENTTOOL-MULTITASK-01',status='PRE_GPU_CPU_ELIGIBILITY_POOL',
        selection_rule='Exclude actual instance_id/task_id/id/task and selected public_issues/task_ids plus curated S1 exposures from pre-S2 tracked JSON; skip only metadata/opaque/ranking/exclusion keys named in METADATA_ONLY. Previously hashing an ID in an unselected metadata ranking is not use for algorithm tuning. Per repo first8 by SHA256(experiment ID|task ID), sorted-repo round-robin. Screen all fixed pool; final first8 eligible with maximum4 per repo, skipping eligible tasks once repo cap reached. Fewer8 =>No-Go without expanding pool. Pool size fixed before any new baseline result, to allow environment filtering without outcome-based task replacement.',
        excluded=sorted(seen),exclusion_evidence=evidence,metadata_only_keys=sorted(METADATA_ONLY),pool=pool,
        order='First8 eligible indices1,4,5,8 A->B;2,3,6,7 B->A. Batches1-4/5-8 each2A-first/2B-first.',
        reference_repair_used=False,GPU_authorized=False)
    target=HERE/'TASK_POOL_PREREGISTRATION.json'
    assert not target.exists(),'Version previous proposal explicitly before revising a rule'
    target.write_text(json.dumps(result,indent=2)+'\n')
    print('Excluded',len(seen),'Fixed metadata pool',[(x['repo'],x['instance_id']) for x in pool])


if __name__=='__main__':main()
