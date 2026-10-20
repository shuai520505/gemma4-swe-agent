"""Separate CPU environment preparation; preserves already-running CPU01."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile
from s1.util import archive,sha_file
from experiments.prepare import write_new

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def emit(path,d):write_new(path,(json.dumps(d,indent=2)+'\n').encode())


def main():
    parent=json.loads((ROOT/'s2/egv_agenttool_t500_v01/GPU_PROTOCOL_T500_DRAFT.json').read_text())
    reserved={r['instance_id'] for r in parent['selected']}
    pool=json.loads((ROOT/'s2/egv_agenttool_v01/TASK_POOL_PREREGISTRATION.json').read_text())
    screening=json.loads((ROOT/'s2/egv_agenttool_v01/results/env01/validation/environment_gate.json').read_text())
    screened={r['instance_id']:r for r in screening['records']}
    excluded=set(pool['excluded'])|reserved|{'rich_3471','fastapi_15800'}
    # Pool order was fixed before Early Prompt design; one eligible task per
    # repository outside reserved/exposed tasks, with no reference-fix access.
    selected=[];repos=set()
    for row in pool['pool']:
        if row['instance_id'] not in excluded and row['repo'] not in repos and screened[row['instance_id']]['eligible']:
            selected.append(row);repos.add(row['repo'])
            if len(selected)==2:break
    assert [r['instance_id'] for r in selected]==['rich_3676','fastapi_14492']
    tasks={}
    for row in selected:
        task=row['instance_id'];tasks.update(json.loads((ROOT/f's2/egv_agenttool_v01/results/env01/validation/{task}/task_inputs.json').read_text()))
    registration=dict(experiment_id='S2-T500-EARLYEGV-MECHANISM-01',selection='First two old-pool-order CPU-eligible nonexposed/nonreserved tasks from different repositories; no reference repair used.',
        excluded=sorted(excluded),reserved_eight_tasks=sorted(reserved),selected=selected,task_inputs=tasks,
        proposed_order=[dict(task=selected[0]['instance_id'],arms=['A','B']),dict(task=selected[1]['instance_id'],arms=['B','A'])],
        A='frozen S2-T500',B='Main-Prompt-only EarlyEGV-Closure',GPU_authorized=False,
        reference_repair_read=False,algorithm_exposure_at_selection='CPU baselines only; no model trajectories for either task found in prior registered runs',
        model_and_quota_pending=True,substitution_after_selection=False)
    emit(HERE/'TASK_SELECTION_PREREGISTRATION.json',registration)
    nb=json.loads((HERE/'notebooks/cpu01/study.ipynb').read_text());setup=nb['cells'][0]['source']
    line=next(s for s in setup.splitlines() if s.startswith("payload=__import__('base64').b64decode("))
    encoded=ast.literal_eval(line[len("payload=__import__('base64').b64decode("):-1])
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as z:
        files={n:z.read(n) for n in z.namelist()}
    for p in (HERE/'environments.py',HERE/'prepare_environment.py'):files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    files['s2/early_task_pool.json']=(HERE/'TASK_SELECTION_PREREGISTRATION.json').read_bytes()
    old=json.loads(files.pop('s2/early_registration.json'))
    reg=dict(old,revision='env01',source_hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()})
    emit(HERE/'registrations/env01.json',reg)
    files['s2/early_registration.json']=(HERE/'registrations/env01.json').read_bytes()
    payload=archive(files)
    start=setup.index("payload=__import__('base64').b64decode(");end=setup.index('with zipfile.ZipFile',start)
    setup=setup[:start]+"payload=__import__('base64').b64decode("+repr(base64.b64encode(payload).decode())+")\nassert hashlib.sha256(payload).hexdigest()=="+repr(hashlib.sha256(payload).hexdigest())+"\n"+setup[end:]
    setup=setup.replace("/'cpu01'/","/'env01'/")
    execute=nb['cells'][1]['source'].replace('s2.egv_agenttool_t500_early_v01.cpu','s2.egv_agenttool_t500_early_v01.environments').replace('timeout=5400','timeout=900')
    cells=[]
    for s in (setup,execute):
        compile(s,'<environment CPU>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=s,outputs=[],execution_count=None,id=hashlib.sha256(s.encode()).hexdigest()[:12]))
    folder=HERE/'notebooks/env01';write_new(folder/'study.ipynb',(json.dumps(dict(cells=cells,metadata=nb['metadata'],nbformat=4,nbformat_minor=5),indent=1)+'\n').encode())
    meta=json.loads((HERE/'notebooks/cpu01/kernel-metadata.json').read_text());meta.update(id='wudangdexiaodoashi/gemma4-s2-early-egv-env01',title='gemma4-s2-early-egv-env01')
    assert meta['enable_gpu'] is False
    emit(folder/'kernel-metadata.json',meta)
    emit(HERE/'env01_freeze.json',dict(kernel=meta['id'],GPU=False,notebook_sha256=sha_file(folder/'study.ipynb'),
        payload_sha256=hashlib.sha256(payload).hexdigest(),task_registration_sha256=sha_file(HERE/'TASK_SELECTION_PREREGISTRATION.json')))
    print(folder)


if __name__=='__main__':main()
