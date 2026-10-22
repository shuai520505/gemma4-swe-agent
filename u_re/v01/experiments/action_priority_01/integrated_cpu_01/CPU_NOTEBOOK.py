"""Reuse approved CPU builder,one-shot dispatch and identity-pinned collection."""
import json
from pathlib import Path
import types

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
SMOKE=ROOT/'u_re/v01/experiments/gemma_smoke_01'


def identity(attempt):
    assert attempt in ('runner01','runner02','runner03','screen01')
    return HERE/attempt,'U-RE-ACTION-FIRST-INTEGRATED-'+attempt.upper(),'wudangdexiaodoashi/gemma4-u-re-integrated-'+attempt


def factory(attempt):
    CPU,ID,SLUG=identity(attempt);original=SMOKE/'cpu_notebook.py';source=original.read_text(encoding='utf-8')
    prefix='u_re/v01/experiments/action_priority_01/integrated_cpu_01/'
    extra="""
    prefix='u_re/v01/experiments/action_priority_01/integrated_cpu_01/'
    files['u_re/v01/experiments/action_priority_01/__init__.py']=b''
    files[prefix+'__init__.py']=b''
    for p in (ROOT/prefix).glob('*.py'):
        if p.name not in ('CPU_NOTEBOOK.py','release.py','test_local.py'):files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    for name in ('chroot_boundary.py',):
        p=ROOT/'u_re/v01/experiments/action_priority_01/gpu_readiness_01'/name;files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    files['u_re/v01/experiments/action_priority_01/gpu_readiness_01/__init__.py']=b''
    files[prefix+'landlock_exec.py']=(ROOT/'u_re/v01/experiments/gemma_smoke_01/recovery_01/landlock_exec.py').read_bytes()
    for name in ('TASK_POOL_FREEZE.json',):
        p=ROOT/'u_re/v01/experiments/action_priority_01/gpu_readiness_01'/name;files[prefix+name]=p.read_bytes()
    files[prefix+'PROTOCOL.json']=(ROOT/prefix/'PROTOCOL.json').read_bytes()
    files[prefix+'SMOKE_PLAN.json']=(HERE/'SMOKE_PLAN.json').read_bytes()
"""
    needle="files['u_re/v01/submission_noegv.zip']=(ROOT/'u_re/v01/submission_noegv.zip').read_bytes()"
    assert source.count(needle)==1;source=source.replace(needle,needle+extra)
    runs=0 if attempt=='screen01' else 4
    source=source.replace('Agent_runs=6','Agent_runs='+str(runs)).replace("expected_candidates_in_order=['noegv_synthetic_interfaces_only']","expected_candidates_in_order=[]")
    source=source.replace("sha((HERE/'SMOKE_PLAN.json').read_bytes())","sha((ROOT/'"+prefix+"PROTOCOL.json').read_bytes())")
    source=source.replace("Path('/kaggle/working/u_re_smoke_cpu01')","Path('/kaggle/working/u_re_integrated_"+attempt+"')")
    module='screen' if attempt=='screen01' else 'acceptance'
    source=source.replace("'u_re.v01.experiments.gemma_smoke_01.cpu_interfaces'","'u_re.v01.experiments.action_priority_01.integrated_cpu_01."+module+"'")
    source=source.replace('timeout=1800)\nprint','timeout=6500)\nprint')
    # Runtime rehash all124 approved task wheels before any task or dependency copy.
    check="""\nplan=json.loads((SOURCE/'u_re/v01/experiments/action_priority_01/integrated_cpu_01/SMOKE_PLAN.json').read_bytes())
from s1.task_identity import find_data
data=find_data()
actual_task={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (data/'wheels').glob('*.whl')}
assert actual_task=={n:v['sha256'] for n,v in plan['task_wheels'].items()},'Task wheel drift'
(RUN_DIR/'task_wheel_hashes.json').write_text(json.dumps(actual_task,indent=2))
"""
    source=source.replace("execute=INSTALL+'''", "execute=INSTALL+"+repr(check)+"+'''")
    m=types.ModuleType('integrated_cpu_builder');m.__file__=str(original);exec(compile(source,str(original),'exec'),m.__dict__)
    m.CPU=CPU;m.EXECUTION_ID=ID;m.SLUG=SLUG
    return m


def launch(attempt):
    CPU,ID,SLUG=identity(attempt);builder=factory(attempt);original=SMOKE/'cpu_launch_once.py';source=original.read_text(encoding='utf-8')
    source=source.replace("timeout='3600'","timeout='7200'")
    source=source.replace('Current human instruction: 你可以使用kaggle的notebook来完成这个任务; interpreted CPU-only official interface validation, no GPU/Gemma authorization.',
        'Human task: U-RE Action-First full Runner isolation acceptance and real SWE baseline admission. CPU Notebook execution and versioned fixes explicitly authorized. This '+ID+' is one CPU-only save; scripted HTTP only for synthetic acceptance; no Gemma,GPU or Submission. Task screening gated by accepted integrated Runner evidence,original order,max8 total.')
    m=types.ModuleType('integrated_cpu_launcher');m.__file__=str(original);m.__package__='u_re.v01.experiments.gemma_smoke_01'
    exec(compile(source,str(original),'exec'),m.__dict__)
    for k,v in dict(CPU=CPU,EXECUTION_ID=ID,SLUG=SLUG,controller_module=builder.controller_module).items():setattr(m,k,v)
    m.launch()


def collect(attempt,private_root):
    CPU,ID,SLUG=identity(attempt)
    path=ROOT/'u_re/v01/experiments/action_priority_01/gpu_readiness_01/collect_capabilities.py'
    text=path.read_text(encoding='utf-8').replace('from .cpu_probe_notebook import CPU,ROOT,SLUG','CPU=None;ROOT=None;SLUG=None')
    text=text.replace("('u_re_isolation_cap01.zip','u_re_isolation_canary01.zip')", "('u_re_integrated_"+attempt+".zip',)")
    m=types.ModuleType('integrated_readonly');m.__file__=str(path);exec(compile(text,str(path),'exec'),m.__dict__);m.ROOT=ROOT
    m.collect(private_root,cpu=CPU,slug=SLUG,archive='u_re_integrated_'+attempt+'.zip')


if __name__=='__main__':
    import sys
    command,attempt=sys.argv[1:3]
    if command=='build':factory(attempt).build()
    elif command=='launch':launch(attempt)
    elif command=='collect':collect(attempt,sys.argv[3])
