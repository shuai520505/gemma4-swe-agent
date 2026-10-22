"""Scoped reuse of proven CPU builder/one-shot dispatch, no GPU permission."""
from pathlib import Path
import types

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
CPU=HERE/'cap01';SMOKE=ROOT/'u_re/v01/experiments/gemma_smoke_01'
ID='U-RE-ACTION-FIRST-ISOLATION-CAP01'
SLUG='wudangdexiaodoashi/gemma4-u-re-isolation-cap01'


def factory():
    original=SMOKE/'cpu_notebook.py';source=original.read_text(encoding='utf-8')
    needle="files['u_re/v01/submission_noegv.zip']=(ROOT/'u_re/v01/submission_noegv.zip').read_bytes()"
    extra="\n    files['u_re/v01/experiments/action_priority_01/__init__.py']=b''\n    files['u_re/v01/experiments/action_priority_01/gpu_readiness_01/__init__.py']=b''\n    p=ROOT/'u_re/v01/experiments/action_priority_01/gpu_readiness_01/capability_probe.py';files[p.relative_to(ROOT).as_posix()]=p.read_bytes()\n"
    assert source.count(needle)==1;source=source.replace(needle,needle+extra)
    source=source.replace('Agent_runs=6','Agent_runs=0')
    source=source.replace("expected_candidates_in_order=['noegv_synthetic_interfaces_only']","expected_candidates_in_order=[]")
    source=source.replace("sha((HERE/'SMOKE_PLAN.json').read_bytes())","sha((ROOT/'u_re/v01/experiments/action_priority_01/gpu_readiness_01/CPU_PROBE_PROTOCOL.json').read_bytes())")
    source=source.replace("Path('/kaggle/working/u_re_smoke_cpu01')","Path('/kaggle/working/u_re_isolation_cap01')")
    source=source.replace("'u_re.v01.experiments.gemma_smoke_01.cpu_interfaces'","'u_re.v01.experiments.action_priority_01.gpu_readiness_01.capability_probe'")
    m=types.ModuleType('isolation_cap_builder');m.__file__=str(original)
    exec(compile(source,str(original),'exec'),m.__dict__)
    m.CPU=CPU;m.EXECUTION_ID=ID;m.SLUG=SLUG
    return m


def launch():
    module=factory();original=SMOKE/'cpu_launch_once.py';source=original.read_text(encoding='utf-8')
    source=source.replace('Current human instruction: 你可以使用kaggle的notebook来完成这个任务; interpreted CPU-only official interface validation, no GPU/Gemma authorization.',
        'Human instruction: Kaggle Notebook 执行授权与实验推进规则; actively create CPU Notebooks for minimal real environment/isolation probes. One CPU-only CAP01; zero Agent, task baseline, Gemma, GPU or formal submission.')
    m=types.ModuleType('isolation_cap_launcher');m.__file__=str(original);m.__package__='u_re.v01.experiments.gemma_smoke_01'
    exec(compile(source,str(original),'exec'),m.__dict__)
    for k,v in dict(CPU=CPU,SLUG=SLUG,EXECUTION_ID=ID,controller_module=module.controller_module).items():setattr(m,k,v)
    m.launch()


if __name__=='__main__':
    import sys
    if sys.argv[1:]==['launch']:launch()
    else:factory().build()
