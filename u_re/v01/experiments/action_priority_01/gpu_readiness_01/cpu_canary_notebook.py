"""Separate versioned CPU canary attempt after CAP01 proved prerequisites."""
from pathlib import Path
import types
from . import cpu_probe_notebook as cap

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];CPU=HERE/'canary01'
ID='U-RE-ACTION-FIRST-ISOLATION-CANARY01';SLUG='wudangdexiaodoashi/gemma4-u-re-isolation-canary01'


def factory():
    original=cap.SMOKE/'cpu_notebook.py';source=original.read_text(encoding='utf-8')
    needle="files['u_re/v01/submission_noegv.zip']=(ROOT/'u_re/v01/submission_noegv.zip').read_bytes()"
    extra="""
    prefix='u_re/v01/experiments/action_priority_01/gpu_readiness_01/'
    files['u_re/v01/experiments/action_priority_01/__init__.py']=b''
    files[prefix+'__init__.py']=b''
    for name in ('chroot_exec.py','chroot_boundary.py','canary_probe.py'):
        files[prefix+name]=(ROOT/prefix/name).read_bytes()
    files[prefix+'landlock_exec.py']=(ROOT/'u_re/v01/experiments/gemma_smoke_01/recovery_01/landlock_exec.py').read_bytes()
"""
    assert source.count(needle)==1;source=source.replace(needle,needle+extra)
    source=source.replace('Agent_runs=6','Agent_runs=0').replace("expected_candidates_in_order=['noegv_synthetic_interfaces_only']","expected_candidates_in_order=[]")
    source=source.replace("sha((HERE/'SMOKE_PLAN.json').read_bytes())","sha((ROOT/'u_re/v01/experiments/action_priority_01/gpu_readiness_01/CPU_CANARY_PROTOCOL.json').read_bytes())")
    source=source.replace("Path('/kaggle/working/u_re_smoke_cpu01')","Path('/kaggle/working/u_re_isolation_canary01')")
    source=source.replace("'u_re.v01.experiments.gemma_smoke_01.cpu_interfaces'","'u_re.v01.experiments.action_priority_01.gpu_readiness_01.canary_probe'")
    m=types.ModuleType('canary_cpu_builder');m.__file__=str(original)
    exec(compile(source,str(original),'exec'),m.__dict__);m.CPU=CPU;m.EXECUTION_ID=ID;m.SLUG=SLUG
    return m


def launch():
    module=factory();original=cap.SMOKE/'cpu_launch_once.py';source=original.read_text(encoding='utf-8')
    source=source.replace('Current human instruction: 你可以使用kaggle的notebook来完成这个任务; interpreted CPU-only official interface validation, no GPU/Gemma authorization.',
        'Human Kaggle Notebook execution rules authorize versioned CPU isolation/tool probes. CAP01 proves chroot and UID support. One CANARY01 CPU-only save; zero Agent,task baseline,Gemma,GPU,formal Submission.')
    m=types.ModuleType('canary_launcher');m.__file__=str(original);m.__package__='u_re.v01.experiments.gemma_smoke_01'
    exec(compile(source,str(original),'exec'),m.__dict__)
    for k,v in dict(CPU=CPU,SLUG=SLUG,EXECUTION_ID=ID,controller_module=module.controller_module).items():setattr(m,k,v)
    m.launch()


if __name__=='__main__':
    import sys
    if sys.argv[1:]==['launch']:launch()
    else:factory().build()
