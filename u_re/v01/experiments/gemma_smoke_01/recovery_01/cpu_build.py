"""Minimal source-scoped adaptation of the tested CPU builder/dispatch; no GPU API."""
import hashlib
import json
from pathlib import Path
import types

HERE=Path(__file__).resolve().parent;SMOKE=HERE.parent;ROOT=SMOKE.parents[3]
CPU=HERE/'cpu02';ID='U-RE-GEMMA-SMOKE-CPU02';SLUG='wudangdexiaodoashi/gemma4-u-re-smoke01-cpu02'

def factory():
    original=SMOKE/'cpu_notebook.py';text=original.read_text(encoding='utf-8')
    substitutions={"CPU=HERE/'cpu01'":"CPU=HERE/'recovery_01/cpu02'",
        "EXECUTION_ID='U-RE-GEMMA-SMOKE-CPU01'":"EXECUTION_ID='U-RE-GEMMA-SMOKE-CPU02'",
        "SLUG='wudangdexiaodoashi/gemma4-u-re-smoke01-cpu01'":"SLUG='wudangdexiaodoashi/gemma4-u-re-smoke01-cpu02'",
        'Agent_runs=6':'Agent_runs=8',
        "Path('/kaggle/working/u_re_smoke_cpu01')":"Path('/kaggle/working/u_re_smoke_cpu02')",
        "'u_re.v01.experiments.gemma_smoke_01.cpu_interfaces',str(RUN_DIR/'validation')":"'u_re.v01.experiments.gemma_smoke_01.recovery_01.cpu_entry',str(RUN_DIR/'validation')"}
    for old,new in substitutions.items():
        assert old in text,old;text=text.replace(old,new)
    needle="files['u_re/v01/submission_noegv.zip']=(ROOT/'u_re/v01/submission_noegv.zip').read_bytes()"
    replacement=needle+"\n    for p in (HERE/'recovery_01').glob('*.py'):\n        files[p.relative_to(ROOT).as_posix()]=p.read_bytes()"
    assert text.count(needle)==1;text=text.replace(needle,replacement)
    module=types.ModuleType('recovery_cpu_factory');module.__file__=str(original)
    exec(compile(text,str(original),'exec'),module.__dict__)
    return module,dict(original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
        adapted_source_sha256=hashlib.sha256(text.encode()).hexdigest(),substitutions=substitutions,
        extra_payload='recovery_01/*.py only, no result/evaluator data')

def build():
    module,changes=factory();module.build()
    module.write(CPU/'BUILD_ADAPTATIONS.json',changes)

def launch():
    module,_=factory()
    # Existing tested launcher, no source rewrite; only independently scoped bindings.
    original=SMOKE/'cpu_launch_once.py'
    run=types.ModuleType('recovery_cpu_launcher');run.__file__=str(original);run.__package__='u_re.v01.experiments.gemma_smoke_01'
    exec(compile(original.read_bytes(),str(original),'exec'),run.__dict__)
    for k,v in dict(CPU=CPU,HERE=SMOKE,ROOT=ROOT,SLUG=SLUG,EXECUTION_ID=ID,controller_module=module.controller_module).items():setattr(run,k,v)
    run.launch()

if __name__=='__main__':
    import sys
    if sys.argv[1:] == ['launch']:launch()
    else:build()
