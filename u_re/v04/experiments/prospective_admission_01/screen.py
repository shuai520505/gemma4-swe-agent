"""Original empty-patch native screening; no Agent or model, frozen order."""
import asyncio,importlib,inspect,json,sys
from pathlib import Path
from .common import HERE,ROOT,ID,sha
from .identity import tree_digest,overlay_content_digest,conflicts
from u_re.v02.experiments.env_recovery_admission_01.runtime import install_extras,fingerprint,native
from u_re.v02.experiments.env_recovery_admission_01.policy import classify

async def run(output):
    import torch
    from s1.task_identity import find_data,identify
    from swegemma.models import load_tasks
    from harness_v2.evidence import atomic_json
    assert sys.platform=='linux' and torch.cuda.device_count()==0
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    protocol=json.loads((HERE/'ADMISSION_PROTOCOL_LOCK.json').read_bytes())
    inherited=json.loads((HERE/'GPU_REPLICATION_PROTOCOL.json').read_bytes())
    environment=json.loads((HERE/'ENVIRONMENT_LOCK.json').read_bytes())
    assert sha((HERE/'GPU_REPLICATION_PROTOCOL.json').read_bytes())==protocol['inherited_protocol_sha256']
    assert sha((HERE/'ENVIRONMENT_LOCK.json').read_bytes())==protocol['environment_sha256']
    for n,h in protocol['execution_sources'].items():assert sha((ROOT/n).read_bytes())==h,n
    data=find_data();assert sha((data/'tasks.jsonl').read_bytes())==protocol['tasks_file_sha256']
    records={r['instance_id']:r for r in map(json.loads,(data/'tasks.jsonl').read_text().splitlines())}
    sources={n:sha(Path(inspect.getfile(importlib.import_module(n))).read_bytes()) for n in environment['native_Verifier_source_sha256']}
    assert sources==environment['native_Verifier_source_sha256'];atomic_json(output/'OFFICIAL_VERIFIER_IDENTITIES.json',sources)
    before=install_extras(output);assert before==environment['fingerprint']
    atomic_json(output/'ENVIRONMENT_BEFORE.json',before)
    metadata=json.loads((ROOT/'u_re/v01/experiments/mechanism_02/TASK_POOL_METADATA.json').read_bytes())['rows']
    tasks={t.instance_id:t for t in load_tasks(data/'tasks.jsonl')}
    identities=identify(data,[r['instance_id'] for r in metadata])
    approved=json.loads((ROOT/'u_re/v02/experiments/env_recovery_admission_01/APPROVED_INPUT_IDENTITIES.json').read_bytes())
    queue=inherited['ranked_candidates'];ids=[r['instance_id'] for r in queue]
    assert ids==protocol['order'] and len(ids)==5 and len(set(identities))==129
    for row in metadata:
        ident=row['instance_id'];assert identities[ident]==approved[ident],('Original input drift',ident)
        for key in ('repo','base_commit','issue_sha256'):assert identities[ident][key]==row[key]
        paths=[data/n for n in identities[ident]['input_files'] if n.endswith(('.tgz','.tar.gz'))]
        assert len(paths)==1,'Resolve snapshot/base separately rather than assume alias semantics'
        identities[ident]['snapshot_tree_sha256']=tree_digest(paths[0])
        identities[ident]['test_overlay_content_sha256']=overlay_content_digest(records[ident].get('test_patch') or '')
    aliases=conflicts(identities,ids)
    atomic_json(output/'TASK_IDENTITY_LOCK.json',dict(all129=identities,prospective_ids=ids,conflicts=aliases,checked_before_baselines=True,tree_scope='Tar member path/type/executable/content; ignore archive headers/root-prefix and .git metadata; symlinks hashed without following'))
    rows=[];selected=[];stop=None
    if aliases:stop=dict(category='INTEGRITY_FAILURE',reason='Snapshot/Issue/base/test-content alias conflict',conflicts=aliases)
    def persist(done=False):
        atomic_json(output/'TASK_ADMISSION_RESULTS.json',dict(experiment_id=ID,status='IN_PROGRESS' if not done else 'V04_ADMISSION_BLOCKED' if stop else 'TWO_PROVISIONALLY_ELIGIBLE_ISSUE_REVIEW_REQUIRED' if len(selected)==2 else 'V04_TASK_POOL_INSUFFICIENT',checked=sum(r['status']!='NOT_RUN' for r in rows),rows=rows,selected_provisional=selected,stop=stop,GPU=False,Gemma_calls=0,Agent_runs=0,protocol_sha256=sha((HERE/'ADMISSION_PROTOCOL_LOCK.json').read_bytes())))
    persist()
    for rank,item in enumerate(queue,1):
        ident=item['instance_id'];row=dict(instance_id=ident,rank=rank,status='NOT_RUN',category=None,eligible=None,reason=None)
        if stop or len(selected)==2:
            row['reason']='Stopped by integrity/unknown' if stop else 'First two provisional eligible reached; require offline Issue review';rows.append(row);continue
        assert fingerprint()==before
        expected={k:v for k,v in identities[ident].items() if k not in ('snapshot_tree_sha256','test_overlay_content_sha256')}
        directory=output/f'{rank:02d}-{ident}';evidence,audit=await native(data,ident,directory,expected)
        source=json.loads((directory/'PRIVATE_BASE_SOURCE.json').read_bytes()) if (directory/'PRIVATE_BASE_SOURCE.json').exists() else {}
        versions=json.loads((directory/'INTERPRETER.json').read_bytes()).get('versions',{}) if (directory/'INTERPRETER.json').exists() else {}
        if (directory/'MISSING_DEPENDENCY_PROBE.json').exists():versions.update(json.loads((directory/'MISSING_DEPENDENCY_PROBE.json').read_bytes())['versions'])
        decision=classify(evidence,audit,source,tasks[ident].problem_statement,versions)
        mapping={'TARGET_BEHAVIOR_FAILURE':'TARGET_BEHAVIOR_FAILURE','NON_DISCRIMINATING':'NON_DISCRIMINATING','A':'ENVIRONMENT_BLOCKED','B':'CONDITIONAL_TARGET_FAILURE','C':'ENVIRONMENT_BLOCKED','D':'UNKNOWN_FAILURE','E':'INTEGRITY_FAILURE'}
        decision['category']=mapping[decision['category']]
        if decision['eligible'] and evidence['counts'].get('errors')!=0:
            decision=dict(status='STOP',category='UNKNOWN_FAILURE',eligible=None,reason='Nonzero JUnit errors cannot be admitted by this protocol')
        if fingerprint()!=before:decision=dict(status='STOP',category='INTEGRITY_FAILURE',eligible=None,reason='Environment drift')
        row.update(evidence,**decision,rank=rank,issue_relation='OFFLINE_REVIEW_REQUIRED',raw_directory=directory.name)
        if row['eligible']:selected.append(ident)
        if row['status']=='STOP':stop=dict(task=ident,category=row['category'],reason=row['reason'])
        rows.append(row);persist();print(json.dumps(dict(task=ident,status=row['status'],category=row['category'],counts=row['counts'])),flush=True)
    atomic_json(output/'ENVIRONMENT_AFTER.json',fingerprint());assert fingerprint()==before
    persist(True)

if __name__=='__main__':
    import sys
    asyncio.run(run(sys.argv[1]))
