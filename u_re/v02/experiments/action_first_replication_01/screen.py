"""Minimal parameter adapter to the CPU-accepted native empty-patch screener."""
import asyncio
import json
import types
from pathlib import Path
from .selection import HERE, ROOT, ID, sha

PRIOR=ROOT/'u_re/v01/experiments/action_priority_01/integrated_cpu_01'

async def run(output):
    from s1.task_identity import find_data,identify
    pool=json.loads((HERE/'TASK_POOL_FREEZE.json').read_bytes())
    # Byte alias check is performed before invoking even the first baseline.
    data=find_data()
    catalog=json.loads((ROOT/'u_re/v01/experiments/mechanism_02/TASK_POOL_METADATA.json').read_bytes())['rows']
    identities=identify(data,[r['instance_id'] for r in catalog])
    snapshots={}
    for ident,row in identities.items():
        for name,h in row['input_files'].items():
            if name.endswith('.tgz'):
                snapshots.setdefault(h,[]).append(ident)
    prospective={r['instance_id'] for r in pool['next_max16_in_order']}
    conflicts=[ids for ids in snapshots.values() if len(set(ids))>1 and prospective.intersection(ids)]
    assert not conflicts,('Snapshot aliases; stop before screening',conflicts)
    for row in pool['next_max16_in_order']:
        for key in ('repo','base_commit','issue_sha256'): assert identities[row['instance_id']][key]==row[key]
    # Preserve all original evidence, classification, provenance and cleanup code.
    source=(PRIOR/'screen.py').read_text(encoding='utf-8')
    source=source.replace('HERE=Path(__file__).resolve().parent', 'HERE=STUDY;PRIOR=PINNED_PRIOR')
    source=source.replace("(HERE/'CPU_GATE_PIN.json')", "(PRIOR/'CPU_GATE_PIN.json')").replace("(HERE/'ACCEPTED_CPU_ACCEPTANCE.json')", "(PRIOR/'ACCEPTED_CPU_ACCEPTANCE.json')").replace('(HERE/name).read_bytes()', '(PRIOR/name).read_bytes()')
    source=source.replace("pool['next_max8_in_order']", "pool['next_max16_in_order']").replace("protocol['screen_order']", "[r['instance_id'] for r in pool['next_max16_in_order']]")
    source=source.replace('len(ranked)==8','len(ranked)==16').replace("pool['max_checks']==8 and pool['selected_qualified_tasks']==[]", "protocol['max_checks']==16 and protocol['target_tasks']==4")
    source=source.replace("(HERE/'PROTOCOL.json')", "(HERE/'REPLICATION_PROTOCOL.json')")
    source=source.replace("json.loads((HERE/'EXPECTED_TASK_RECORDS.json').read_bytes())", "EXPECTED_IDENTITIES")
    source=source.replace('len(selected)==2','len(selected)==4').replace('first_two_eligible_selected','first_four_eligible_selected').replace('TWO_TASKS_ADMITTED','FOUR_TASKS_ADMITTED')
    source=source.replace("HERE.parents[2]/'candidate_noegv'", "REPOSITORY/'u_re/v01/candidate_noegv'")
    source=source.replace("'U-RE-V01-ACTION-FIRST-01'", repr(ID))
    m=types.ModuleType('v02_native_screener');m.__file__=str(PRIOR/'screen.py');m.__package__='u_re.v01.experiments.action_priority_01.integrated_cpu_01'
    m.STUDY=HERE;m.PINNED_PRIOR=PRIOR;m.REPOSITORY=ROOT;m.EXPECTED_IDENTITIES=identities
    exec(compile(source,m.__file__,'exec'),m.__dict__)
    await m.run(output)
    from harness_v2.evidence import atomic_json
    atomic_json(Path(output)/'SNAPSHOT_ALIAS_CHECK.json',dict(all_task_identities=identities,conflicts=conflicts,checked_before_baselines=True))

if __name__=='__main__':
    import sys
    asyncio.run(run(sys.argv[1]))
