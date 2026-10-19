"""Host installation/classification; no Agent tool or workspace source changes."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess


def install(venv):
    venv=Path(venv).resolve()
    python=venv/('Scripts/python.exe' if __import__('os').name=='nt' else 'bin/python3')
    result=subprocess.run([str(python),'-c','import json,sysconfig; print(json.dumps(sysconfig.get_paths()["purelib"]))'],
        capture_output=True,text=True,check=True,timeout=30)
    site=Path(json.loads(result.stdout)).resolve()
    assert site.is_relative_to(venv),'Audit installation outside sandbox denied'
    site.mkdir(parents=True,exist_ok=True)
    code=Path(__file__).with_name('import_runtime.py').read_bytes()
    (site/'_s1_import_audit.py').write_bytes(code)
    (site/'000_s1_import_audit.pth').write_text('import _s1_import_audit\n')
    return dict(site=str(site),observer_sha256=hashlib.sha256(code).hexdigest())


def classify(records,workspace):
    workspace=Path(workspace).resolve()
    exits=[r for r in records if r.get('stage')=='exit']
    if not exits:return dict(status='unknown',reason='No final process import evidence; exit0 alone is insufficient')
    modules=[]
    for row in exits:
        for name,info in row.get('modules',{}).items():
            if not info.get('imported'):continue
            path=Path(info['realpath']) if info.get('realpath') else None
            loaded_here=bool(path and path.is_relative_to(workspace))
            executed=bool(path and any(Path(e['filename']).resolve()==path for e in row.get('executed_modules',[])))
            modules.append(dict(module=name,realpath=str(path) if path else None,
                source_sha256=info.get('source_sha256'),within_workspace=loaded_here,
                module_code_executed=executed,pid=row['pid']))
    if not modules:return dict(status='not_imported',modules=[],behavior_verified=False)
    if any(not m['within_workspace'] for m in modules):status='outside_workspace'
    elif all(m['module_code_executed'] for m in modules):status='workspace_source_executed'
    else:status='workspace_import_only'
    return dict(status=status,modules=modules,behavior_verified=False,
        meaning='Import/module execution provenance only; passing behavior assertions require separate evidence')


def shell_prefix(directory,modules):
    # Native subprocess translates /tmp and /workspace inside command strings;
    # encode this host evidence path so it cannot be accidentally remapped.
    encoded=__import__('base64').b64encode(str(directory).encode()).decode()
    return 'export S1_IMPORT_AUDIT_DIR_B64='+shlex.quote(encoded)+'; export S1_IMPORT_AUDIT_MODULES='+shlex.quote(','.join(modules))+'; '
