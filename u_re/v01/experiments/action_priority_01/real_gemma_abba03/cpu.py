"""Versioned CPU Notebook control; exact GPU03 production payload,external mock."""
import types
from pathlib import Path
from ..real_gemma_abba02.cpu_repair import factory as repair_factory
from .notebook import HERE,ROOT,ID,make_notebook

def factory(version='cpu-e2e01'):
    cpu=HERE/version;slug='wudangdexiaodoashi/gemma4-u-re-abba03-'+version
    m=repair_factory(cpu=cpu,execution_id=ID+'-'+version,slug=slug)
    # Reuse the already proven CPU claim/observer/config/collector unchanged.
    def launch():
        original=ROOT/'u_re/v01/experiments/gemma_smoke_01/cpu_launch_once.py'
        source=original.read_text(encoding='utf-8').replace('from .cpu_notebook import CPU,HERE,ROOT,SLUG,EXECUTION_ID,controller_module,sha,write','')
        source=source.replace('Current human instruction: 你可以使用kaggle的notebook来完成这个任务; interpreted CPU-only official interface validation, no GPU/Gemma authorization.',
            'Current GPU03 task explicitly authorizes versioned Kaggle CPU end-to-end runs from the final shared production payload;two frozen trusted baselines plus one owned scripted synthetic Agent. CPU only,no Gemma/Submission.')
        t=types.ModuleType('gpu03_cpu_once');t.__file__=str(original)
        from .notebook import sha,write
        exec(compile(source,str(original),'exec'),t.__dict__)
        for k,v in dict(CPU=cpu,HERE=HERE,ROOT=ROOT,SLUG=slug,EXECUTION_ID=ID+'-'+version,controller_module=m.controller_module,sha=sha,write=write).items():setattr(t,k,v)
        from u_re.v01.experiments.fastapi_pilot_01 import auth_diagnose
        (cpu/'preflight').mkdir(parents=True,exist_ok=True);auth_diagnose.HERE=cpu/'preflight';auth_diagnose.diagnose()
        t.launch()
    def collect(private_root):
        old=ROOT/'u_re/v01/experiments/action_priority_01/gpu_readiness_01/collect_capabilities.py'
        source=old.read_text(encoding='utf-8').replace('from .cpu_probe_notebook import CPU,ROOT,SLUG','CPU=None;ROOT=None;SLUG=None')
        source=source.replace("('u_re_isolation_cap01.zip','u_re_isolation_canary01.zip')",repr((version+'.zip',)))
        t=types.ModuleType('gpu03_cpu_read');t.__file__=str(old);exec(compile(source,str(old),'exec'),t.__dict__);t.ROOT=ROOT
        t.collect(private_root,cpu=cpu,slug=slug,archive=version+'.zip')
    m.launch=launch;m.collect=collect;m.build=lambda:make_notebook('CPU_DRY_RUN',cpu)
    return m

if __name__=='__main__':
    import sys
    m=factory()
    if sys.argv[1]=='build':m.build()
    elif sys.argv[1]=='launch':m.launch()
    elif sys.argv[1]=='collect':m.collect(sys.argv[2])
