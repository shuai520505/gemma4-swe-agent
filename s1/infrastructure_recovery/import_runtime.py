"""Loaded by a research-only sandbox .pth; observes Python module execution."""
import atexit
import hashlib
import json
import marshal
import os
from pathlib import Path
import sys
import time

directory=os.environ.get('S1_IMPORT_AUDIT_DIR')
if os.environ.get('S1_IMPORT_AUDIT_DIR_B64'):
    directory=__import__('base64').b64decode(os.environ['S1_IMPORT_AUDIT_DIR_B64']).decode()
targets=tuple(filter(None,os.environ.get('S1_IMPORT_AUDIT_MODULES','').split(',')))
executed={}


def capture(event,args):
    if event!='exec' or not args:return
    code=args[0];filename=getattr(code,'co_filename','')
    if any(('/'+target.split('.')[0]+'/') in filename.replace('\\','/')
           or filename.endswith('/'+target.replace('.','/')+'.py') for target in targets):
        executed[filename]=dict(filename=filename,code_sha256=hashlib.sha256(marshal.dumps(code)).hexdigest(),
            meaning='module code object executed; not a claim that a repair assertion passed')


def save(stage):
    if not directory:return
    try:
        out=Path(directory);out.mkdir(parents=True,exist_ok=True)
        modules={}
        for name in targets:
            module=sys.modules.get(name)
            value=getattr(module,'__file__',None) if module is not None else None
            path=Path(value).resolve() if value else None
            modules[name]=dict(imported=module is not None,file=value,realpath=str(path) if path else None,
                source_sha256=hashlib.sha256(path.read_bytes()).hexdigest() if path and path.is_file() else None)
        payload=dict(pid=os.getpid(),stage=stage,recorded_monotonic=time.monotonic(),
            python=sys.executable,cwd=os.getcwd(),sys_path=sys.path,modules=modules,
            executed_modules=list(executed.values()))
        path=out/(str(os.getpid())+'-'+stage+'.json')
        tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(payload,indent=2));os.replace(tmp,path)
    except Exception:
        # Observation cannot turn a command success into failure. Missing evidence
        # is handled conservatively by the host audit, never as verified imports.
        pass


if directory:
    save('startup')
    sys.addaudithook(capture)
    atexit.register(save,'exit')
