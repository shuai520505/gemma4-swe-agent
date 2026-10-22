"""Scoped reuse of proven CPU packaging, durable dispatch and read recovery."""
import json
from pathlib import Path
import types

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CPU=HERE/'cpu01'
SMOKE=ROOT/'u_re/v01/experiments/gemma_smoke_01'
ID='U-RE-ACTION-FIRST-CPU01';SLUG='wudangdexiaodoashi/gemma4-u-re-action-first-cpu01'


def factory():
    original=SMOKE/'cpu_notebook.py';source=original.read_text(encoding='utf-8')
    needle="files['u_re/v01/submission_noegv.zip']=(ROOT/'u_re/v01/submission_noegv.zip').read_bytes()"
    extra="""
    for n in ('build.py','cpu_acceptance.py','ACTION_FIRST_INSTRUCTION_BLOCK.md','CANDIDATE_AUDIT.json','submission_action_v01.zip'):
        p=ROOT/'u_re/v01/experiments/action_priority_01'/n;files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    for p in (ROOT/'u_re/v01/experiments/action_priority_01/candidate_action_v01').rglob('*'):
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    files['u_re/v01/experiments/action_priority_01/__init__.py']=b''
    files['u_re/v01/build.py']=(ROOT/'u_re/v01/build.py').read_bytes()
    files['u_re/v01/submission_full.zip']=(ROOT/'u_re/v01/submission_full.zip').read_bytes()
    for p in (ROOT/'u_re/v01/candidate_full').rglob('*'):
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
"""
    assert source.count(needle)==1;source=source.replace(needle,needle+extra)
    source=source.replace('Agent_runs=6','Agent_runs=2')
    source=source.replace("Path('/kaggle/working/u_re_smoke_cpu01')","Path('/kaggle/working/u_re_action_first_cpu01')")
    source=source.replace("'u_re.v01.experiments.gemma_smoke_01.cpu_interfaces'","'u_re.v01.experiments.action_priority_01.cpu_acceptance'")
    m=types.ModuleType('action_first_cpu_builder');m.__file__=str(original)
    exec(compile(source,str(original),'exec'),m.__dict__)
    m.CPU=CPU;m.EXECUTION_ID=ID;m.SLUG=SLUG
    return m


def launch():
    module=factory();original=SMOKE/'cpu_launch_once.py'
    text=original.read_text(encoding='utf-8').replace(
        'Current human instruction: 你可以使用kaggle的notebook来完成这个任务; interpreted CPU-only official interface validation, no GPU/Gemma authorization.',
        'Current human instruction for Action-First: 你可以在kaggle上建立notebook运行. One CPU-only synthetic official Compiler/ADK acceptance; no GPU,realGemma,competitionTask or formal submission.')
    m=types.ModuleType('action_first_cpu_launcher');m.__file__=str(original);m.__package__='u_re.v01.experiments.gemma_smoke_01'
    exec(compile(text,str(original),'exec'),m.__dict__)
    for k,v in dict(CPU=CPU,SLUG=SLUG,EXECUTION_ID=ID,controller_module=module.controller_module).items():setattr(m,k,v)
    m.launch()


if __name__=='__main__':
    import sys
    if sys.argv[1:]==['launch']:launch()
    else:factory().build()
