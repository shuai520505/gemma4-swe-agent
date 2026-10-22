"""CPU-only actual entrypoint repair;no GPU retry dispatcher."""
from pathlib import Path
import types
from ..real_gemma_abba01 import repair as original
from .import_closure import complete
from .notebook import HERE,ROOT,PRIOR,write

CPU=HERE/'repair_cpu01';ID='U-RE-ACTION-FIRST-GPU02-IMPORT-REPAIR01'
SLUG='wudangdexiaodoashi/gemma4-u-re-abba02-import-repair01'

def corrected_files():
    files,graph=complete(original.corrected_files())
    write(HERE/'IMPORT_CLOSURE.json',graph)
    files['u_re/v01/experiments/action_priority_01/real_gemma_abba02/__init__.py']=b''
    p=HERE/'cpu_probe.py';files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    return files

def factory(*,cpu=CPU,execution_id=ID,slug=SLUG,probe_module='cpu_probe',archive='u_re_abba02_import_repair01',files_factory=corrected_files):
    path=Path(original.__file__);source=path.read_text(encoding='utf-8')
    # The proven CPU builder handles install/metadata/claim/collection unchanged.
    source=source.replace('from .GPU_NOTEBOOK import HERE,ROOT,PRIOR,sha,write','')
    begin=source.index('def corrected_files():');end=source.index('\ndef build():',begin)
    source=source[:begin]+source[end:]
    source=source.replace('u_re_abba_repair_cpu01',archive)
    source=source.replace('Agent_runs=0,Gemma_calls=0','Agent_runs=1,Gemma_calls=0')
    source=source.replace("'u_re.v01.experiments.action_priority_01.real_gemma_abba01.repair_probe'",repr('u_re.v01.experiments.action_priority_01.real_gemma_abba02.'+probe_module))
    source=source.replace('Current human ABBA task Section8 explicitly permits CPU-only engineering repair after GPU startup failure. One targeted package/Compiler/boundary CPU probe;zero Agent,Gemma,GPU or task baseline. Original failed GPU preserved;no GPU retry authorized.',
        'Current GPU02 human instruction explicitly permits ordinary CPU Notebook engineering repairs. One CPU-only import closure and exact preflight/synthetic worker test;two frozen real native baseline rechecks,one owned scripted Agent,zero real Gemma/GPU/Submission. No GPU03 authorization.')
    if probe_module=='cpu_probe_v2':source=source.replace('two frozen real native baseline rechecks','zero repeated real native baselines (both passed in repair01)')
    m=types.ModuleType('gpu02_cpu_repair');m.__file__=str(path);m.HERE=HERE.parent/'real_gemma_abba01'
    exec(compile(source,str(path),'exec'),m.__dict__)
    from ..real_gemma_abba01.GPU_NOTEBOOK import sha
    for k,v in dict(HERE=HERE.parent/'real_gemma_abba01',ROOT=ROOT,PRIOR=PRIOR,sha=sha,write=write,CPU=cpu,ID=execution_id,SLUG=slug,corrected_files=files_factory).items():setattr(m,k,v)
    original_controller=m.controller_module
    def controller_module():
        controller=original_controller();check=controller.checked_config
        def checked(spec):
            assert spec['configuration']['Agent_runs']==1,'Only one owned scripted CPU Agent'
            normalized=dict(spec,configuration=dict(spec['configuration'],Agent_runs=0))
            check(normalized) # All original CPU/network/no-model/identity guards remain.
        controller.checked_config=checked
        return controller
    m.controller_module=controller_module
    return m

if __name__=='__main__':
    import sys
    if sys.argv[1]=='build':factory().build()
    elif sys.argv[1]=='launch':factory().launch()
    elif sys.argv[1]=='collect':factory().collect(sys.argv[2])
