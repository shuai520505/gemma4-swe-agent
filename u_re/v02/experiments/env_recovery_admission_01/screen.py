"""Prospective max24 new native baselines in one frozen recovered environment."""
import asyncio,importlib,inspect,json,sys
from pathlib import Path
from .dependencies import HERE,ROOT,ID,sha
from .runtime import native,fingerprint,install_extras
from .policy import classify

async def run(output):
    import torch
    assert sys.platform=='linux' and sys.version_info[:2]==(3,12) and torch.cuda.device_count()==0
    from s1.task_identity import find_data
    from swegemma.models import load_tasks
    from harness_v2.evidence import atomic_json
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    protocol=json.loads((HERE/'V02B_PROTOCOL_LOCK.json').read_bytes());environment=json.loads((HERE/'V02B_ENVIRONMENT_LOCK.json').read_bytes());pool=json.loads((HERE/'TASK_POOL_FREEZE.json').read_bytes())
    assert protocol['max_new_checks']==24 and protocol['target_total']==4
    assert sha((HERE/'TASK_POOL_FREEZE.json').read_bytes())==protocol['pool_sha256']
    assert sha((HERE/'V02B_ENVIRONMENT_LOCK.json').read_bytes())==protocol['environment_lock_sha256']
    for n,h in protocol['execution_sources'].items():assert sha((HERE/n).read_bytes())==h,('Screen source drift',n)
    expected=json.loads((HERE/'APPROVED_INPUT_IDENTITIES.json').read_bytes());data=find_data()
    assert sha((data/'tasks.jsonl').read_bytes())==protocol['approved_tasks_file_sha256']
    sources={n:sha(Path(inspect.getfile(importlib.import_module(n))).read_bytes()) for n in environment['native_Verifier_source_sha256']}
    assert sources==environment['native_Verifier_source_sha256'];atomic_json(output/'official_source_hashes.json',sources)
    current=install_extras(output);assert current==environment['fingerprint'],'Recovered environment fingerprint drift before screening'
    atomic_json(output/'ENVIRONMENT_FINGERPRINT.json',current)
    tasks={t.instance_id:t for t in load_tasks(data/'tasks.jsonl')}
    carry=protocol['carry_migration'];selected=[carry] if carry['eligible'] else []
    rows=[];stop=None;checked=0
    queue=pool['next_max24_in_order'];assert len(queue)==24
    def persist(progress):
        atomic_json(output/'TASK_ADMISSION_LEDGER.json',dict(experiment_id=ID,status='IN_PROGRESS' if progress else 'FOUR_TASKS_ADMITTED' if len(selected)==4 and stop is None else 'STOPPED' if stop else 'TASKS_INSUFFICIENT',checked_new=checked,carry=carry,selected=selected,rows=rows,stop=stop,screening_in_progress=progress,environment_lock_sha256=protocol['environment_lock_sha256'],protocol_sha256=sha((HERE/'V02B_PROTOCOL_LOCK.json').read_bytes()),GPU=False,Agent_runs=0,Gemma_calls=0))
    persist(True)
    for rank,item in enumerate(queue,1):
        ident=item['instance_id'];row=dict(item,screen_rank=rank,status='NOT_RUN',category=None,eligible=None,counts=None,reason=None)
        if stop or len(selected)==4:
            row['reason']=stop or 'First_four_total_eligible_selected';rows.append(row);continue
        assert fingerprint()==current,'Environment drift between tasks'
        directory=output/f'{rank:02d}-{ident}';evidence,audit=await native(data,ident,directory,expected[ident]);checked+=1
        source=json.loads((directory/'PRIVATE_BASE_SOURCE.json').read_bytes()) if (directory/'PRIVATE_BASE_SOURCE.json').exists() else {}
        interpreter=json.loads((directory/'INTERPRETER.json').read_bytes()) if (directory/'INTERPRETER.json').exists() else {'versions':{}}
        versions=interpreter['versions']
        if (directory/'MISSING_DEPENDENCY_PROBE.json').exists():versions.update(json.loads((directory/'MISSING_DEPENDENCY_PROBE.json').read_bytes())['versions'])
        decision=classify(evidence,audit,source,tasks[ident].problem_statement,versions)
        row.update(evidence,**decision,role='PROSPECTIVE_NEW',raw_directory=directory.name)
        if fingerprint()!=current:row.update(status='STOP',category='E',eligible=None,reason='Environment mutated during native test')
        if row['status']=='BASELINE_ELIGIBLE':selected.append(row)
        if row['status']=='STOP':stop=dict(task=ident,category=row['category'],reason=row['reason'])
        rows.append(row);persist(True)
        print(json.dumps(dict(task=ident,status=row['status'],category=row['category'],counts=row['counts'])),flush=True)
    persist(False)
    atomic_json(output/'FINAL_ENVIRONMENT_FINGERPRINT.json',fingerprint())
    print(json.dumps(dict(checked_new=checked,selected_total=len(selected),stop=stop)),flush=True)

if __name__=='__main__':
    import sys
    asyncio.run(run(sys.argv[1]))
