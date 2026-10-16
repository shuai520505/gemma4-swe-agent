"""Preregister two complete-pair batches around the unchanged r12 runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import random

from experiments.prepare import ROOT, archive_bytes, write_new
from harness_v2.batch import require_cpu_gate, split_pairs
from harness_v2.integrity import verify_baseline

EXPERIMENT = 'harness-v2-formal-paired-01'
SEED = 20261016
SELECTION = {'requests_7309': 'malformed header parsing',
             'fastapi_14258': 'router self-inclusion validation',
             'rich_3052': 'case-insensitive CLI choices',
             'httpx_3672': 'HTTP server connection lifecycle'}
EXCLUDED = {'fastapi_15661','fastapi_15589','requests_7315','rich_3777','rich_4006'}


def sha(data): return hashlib.sha256(data).hexdigest()


def prepare(wheel_hashes):
    verify_baseline()
    r12=json.loads((ROOT/'harness_v2/registrations/r12.json').read_text())
    gate=ROOT/'docs/validation/harness-v2/official-cpu-r12.json'
    require_cpu_gate(gate,r12,ROOT)
    for name,digest in r12['source_hashes'].items():
        assert sha((ROOT/name).read_bytes())==digest,'r12 source changed'
    tasks={r['instance_id']:r for r in map(json.loads,(ROOT.parent/'official-inputs/tasks.jsonl').read_text(encoding='utf-8').splitlines())}
    selected=[]
    for ident,category in SELECTION.items():
        assert ident not in EXCLUDED
        row=tasks[ident]
        selected.append(dict(instance_id=ident,category=category,repo=row['repo'],
            base_commit=row['base_commit'],problem_sha256=sha(row['problem_statement'].encode())))
    random.Random(SEED).shuffle(selected)
    schedule=[]
    for i,row in enumerate(selected):
        arms=('v0','v1') if i%2==0 else ('v1','v0')
        first=len(schedule)+1
        schedule.extend(dict(index=first+j,arm=arm,**row) for j,arm in enumerate(arms))
    batches=split_pairs(schedule)
    assert len(batches)==2 and all(len(b)==4 for b in batches)
    candidate_zips={arm:sha((ROOT/f'candidates/{arm}/submission.zip').read_bytes()) for arm in ('v0','v1')}
    wheels=json.loads(Path(wheel_hashes).read_text())
    protocol=dict(experiment_id=EXPERIMENT,status='preregistered_not_executed',
        harness_version='2.0.3',runtime_revision='r12',seed=SEED,experimental_unit='task pair',
        task_selection='One new task per available public repository, selected by original Issue only; no gold/test patch inspection',
        excluded_tasks=sorted(EXCLUDED),schedule=schedule,batches=batches,
        model=r12['model'],budget=r12['budget'],candidate_zip_sha256=candidate_zips,
        source_hashes=r12['source_hashes'],wheel_hashes=wheels,
        generation=dict(max_output_tokens=16384,thinking_budget=4096,other_sampling='pinned official defaults; no arm-specific override',generation_seed=None),
        context=dict(max_model_len=32768,safety_tokens=1024,token_threshold=8192,compaction_interval=5,overlap_size=1,event_retention_size=4,max_stdout_chars=2000,max_file_chars=4000,max_file_lines=120),
        analysis=dict(complete_pairs_required_for_comparison=True,unknown_and_not_run_are_not_failures=True,
            complete_resolution_rate_requires_all_eight_known=True,exploratory_only=True,
            report=['resolution_rate','patch_application','collection_failures','model_and_tool_calls','tokens','durations','timeouts','censored_observations','paired_wins']),
        stopping='Stop only the affected Notebook batch on unknown, infrastructure error or unconfirmed cleanup. Other batch uses a fresh container. Never splice retries.',
        inherited_batch_summary='Frozen r12 run_batch writes development-only summary labels and null rates. Formal postprocessing uses raw results and this separate protocol, never those labels as performance evidence.',
        competition_score=None)
    directory=ROOT/'experiments/formal-paired-01'
    write_new(directory/'protocol.json',(json.dumps(protocol,indent=2)+'\n').encode())
    files={name:(ROOT/name).read_bytes() for name in r12['source_hashes']}
    files['cpu_gate.json']=gate.read_bytes()
    files['wheel_hashes.json']=(json.dumps(wheels,indent=2)+'\n').encode()
    files['formal_protocol.json']=(directory/'protocol.json').read_bytes()
    plans={}
    for letter,rows in zip(('a','b'),batches):
        plan=dict(r12,experiment_id=EXPERIMENT,revision='paired01-'+letter,
            purpose='formal paired prompt comparison; separate protocol',tasks=rows,
            formal_comparison_status='preregistered_not_executed')
        plans[letter]=plan
        data=(json.dumps(plan,indent=2)+'\n').encode()
        files['batch_'+letter+'.json']=data
        write_new(ROOT/f'harness_v2/registrations/paired01-{letter}.json',data)
    payload=archive_bytes(files)
    base=ROOT/'artifacts/formal-paired-01'
    write_new(base/'input/paired-01.bundle',payload)
    meta=dict(id='wudangdexiaodoashi/gemma4-formal-paired-01-input',title='Gemma4 Formal Paired 01 Input',isPrivate=True,licenses=[dict(name='CC0-1.0')])
    write_new(base/'input/dataset-metadata.json',(json.dumps(meta,indent=2)+'\n').encode())
    old=json.loads((ROOT/'artifacts/harness-v2/r12/gpu-kernel/gpu.ipynb').read_text())
    notebook_hashes={}
    for letter in ('a','b'):
        nb=json.loads(json.dumps(old))
        setup=f'''import os,sys,json,hashlib,zipfile,subprocess,shutil,time
from pathlib import Path
from datetime import datetime,timezone
BATCH={letter!r}
RUN_DIR=Path('/kaggle/working/formal_paired_01')/BATCH/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
payloads=list(Path('/kaggle/input').rglob('paired-01.bundle'));assert len(payloads)==1
assert hashlib.sha256(payloads[0].read_bytes()).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(payloads[0]) as z:
    assert z.testzip() is None
    assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    z.extractall(SOURCE)
PLAN=json.loads((SOURCE/('batch_'+BATCH+'.json')).read_text());plan=PLAN
for name,digest in PLAN['source_hashes'].items():assert hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()==digest
(SOURCE/'infra_plan.json').write_text(json.dumps(PLAN,indent=2))
sys.path.insert(0,str(SOURCE))
from harness_v2.evidence import atomic_json,bundle
from harness_v2.batch import require_cpu_gate,run_batch
bundle_run=bundle
CPU_GATE=json.loads((SOURCE/'cpu_gate.json').read_text())
require_cpu_gate(SOURCE/'cpu_gate.json',PLAN,SOURCE)
SESSION_STARTED=time.monotonic()
MODEL_NAME='gemma-4-31b-it-qat-w4a16-ct'
server_instance=None
profile=dict(task_wall_minutes=25.5,max_tasks=4)
'''
        nb['cells'][0]['source']='# Formal paired experiment 01 / batch '+letter.upper()+'\nFour frozen runs; two complete task pairs. No reference answers in Agent input.'
        nb['cells'][1]['source']=setup
        # An external admission check does not alter the CPU-tested r12 worker.
        nb['cells'][2]['source']+='''
expected_wheels=json.loads((SOURCE/'wheel_hashes.json').read_text())
actual_wheels={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}
assert actual_wheels==expected_wheels,'Official wheel bytes changed; do not admit this batch'
atomic_json(RUN_DIR/'wheel_hashes.json',actual_wheels)
'''
        for c in nb['cells']:
            if c['cell_type']=='code': compile(c['source'],'<formal-notebook>','exec',flags=__import__('ast').PyCF_ALLOW_TOP_LEVEL_AWAIT)
            c['id']=sha(c['source'].encode())[:12]
        data=(json.dumps(nb,indent=1)+'\n').encode()
        write_new(base/('kernel-'+letter)/'formal.ipynb',data)
        meta=json.loads((ROOT/'artifacts/harness-v2/r12/gpu-kernel/kernel-metadata.json').read_text())
        meta.update(id='wudangdexiaodoashi/gemma4-formal-paired-01-'+letter,
            title='Gemma4 Formal Paired 01 '+letter.upper(),code_file='formal.ipynb',
            dataset_sources=['metric/gemma-4-developer-agent-wheelhouse','wudangdexiaodoashi/gemma4-formal-paired-01-input'])
        write_new(base/('kernel-'+letter)/'kernel-metadata.json',(json.dumps(meta,indent=2)+'\n').encode())
        notebook_hashes[letter]=sha(data)
    registration=dict(experiment_id=EXPERIMENT,protocol_sha256=sha((directory/'protocol.json').read_bytes()),
        bundle_sha256=sha(payload),notebook_sha256=notebook_hashes,status='not_executed_at_registration')
    write_new(directory/'notebooks.json',(json.dumps(registration,indent=2)+'\n').encode())
    return registration


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('wheel_hashes');a=p.parse_args()
    print(json.dumps(prepare(a.wheel_hashes),indent=2))
