"""Reuse CPU-proven corrected_files and existing single-dispatch GPU controller."""
import json
from pathlib import Path
import types
from ..real_gemma_abba01.GPU_NOTEBOOK import ROOT,PRIOR,sha,write,MODEL_SOURCE
from ..real_gemma_abba01.repair import corrected_files

HERE=Path(__file__).resolve().parent
ORIGINAL=HERE.parent/'real_gemma_abba01'
SLUG='wudangdexiaodoashi/gemma4-u-re-actionfirst-abba02'
ID='U-RE-V01-ACTION-FIRST-01-GPU02'

def factory():
    path=ORIGINAL/'GPU_NOTEBOOK.py';source=path.read_text(encoding='utf-8')
    begin=source.index('    old=json.loads(');end=source.index('    reg=dict(',begin)
    # Reuse the actual CPU-accepted exhaustive source-pin closure,not a new list.
    replacement='''    files=corrected_files()
    files['u_re/v01/experiments/action_priority_01/real_gemma_abba01/GPU_AUTHORIZATION.json']=(HERE/'GPU_AUTHORIZATION.json').read_bytes()
    lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    for name,wanted in lock['source_pins'].items():
        assert sha(files[(PRIOR/name).relative_to(ROOT).as_posix()])==wanted,name
    for arm,name in (('A','u_re/v01/submission_noegv.zip'),('B','u_re/v01/experiments/action_priority_01/submission_action_v01.zip')):
        assert sha(files[name])==lock['arms'][arm]['ZIP_sha256']
        import zipfile,io
        with zipfile.ZipFile(io.BytesIO(files[name])) as candidate:
            assert candidate.testzip() is None
            directory='u_re/v01/candidate_noegv/' if arm=='A' else 'u_re/v01/experiments/action_priority_01/candidate_action_v01/'
            for member in candidate.namelist():assert files[directory+member]==candidate.read(member)
'''
    source=source[:begin]+replacement+source[end:]
    source=source.replace("Path('/kaggle/working/u_re_actionfirst_abba01')","Path('/kaggle/working/u_re_actionfirst_abba02')")
    m=types.ModuleType('gpu02_approved_builder');m.__file__=str(path);exec(compile(source,str(path),'exec'),m.__dict__)
    m.HERE=HERE;m.ROOT=ROOT;m.PRIOR=PRIOR;m.ID=ID;m.SLUG=SLUG;m.corrected_files=corrected_files
    return m

def launcher():
    path=ORIGINAL/'launch.py';source=path.read_text(encoding='utf-8')
    line='from .GPU_NOTEBOOK import HERE,ROOT,SLUG,ID,MODEL_SOURCE,controller_module,sha,write'
    assert source.count(line)==1;source=source.replace(line,'')
    m=types.ModuleType('gpu02_existing_launcher');m.__file__=str(path);exec(compile(source,str(path),'exec'),m.__dict__)
    for k,v in dict(HERE=HERE,ROOT=ROOT,SLUG=SLUG,ID=ID,MODEL_SOURCE=MODEL_SOURCE,controller_module=factory().controller_module,sha=sha,write=write).items():setattr(m,k,v)
    return m

def collect(private_root):
    path=ORIGINAL/'collect.py';source=path.read_text(encoding='utf-8')
    source=source.replace('from .GPU_NOTEBOOK import HERE,ROOT,SLUG','')
    source=source.replace("'u_re_actionfirst_abba01.zip'","'u_re_actionfirst_abba02.zip'")
    m=types.ModuleType('gpu02_existing_readonly');m.__file__=str(path);exec(compile(source,str(path),'exec'),m.__dict__)
    m.HERE=HERE;m.ROOT=ROOT;m.SLUG=SLUG;m.collect(private_root)

if __name__=='__main__':
    import sys
    if sys.argv[1]=='preflight':launcher().preflight()
    elif sys.argv[1]=='build':factory().build()
    elif sys.argv[1]=='launch':launcher().launch()
    elif sys.argv[1]=='collect':collect(sys.argv[2])
