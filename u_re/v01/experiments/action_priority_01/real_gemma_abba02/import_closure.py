"""Include repository imports,including imports inside functions,from actual entrypoints."""
import ast
from importlib.util import resolve_name
from pathlib import Path
from .notebook import ROOT,sha

ENTRYPOINTS=('u_re.v01.experiments.action_priority_01.real_gemma_abba01.session',
             'u_re.v01.experiments.action_priority_01.real_gemma_abba01.worker')

def complete(files):
    files=dict(files);queue=list(ENTRYPOINTS);seen=set();edges=[];added=[]
    def locate(module):
        for name in (module.replace('.','/')+'.py',module.replace('.','/')+'/__init__.py'):
            if name in files:return name,files[name]
            if (ROOT/name).is_file():return name,(ROOT/name).read_bytes()
        return None
    def parents(name):
        parts=Path(name).parts[:-1]
        for i in range(1,len(parts)+1):
            parent=Path(*parts[:i])/'__init__.py';n=parent.as_posix()
            if n not in files:files[n]=(ROOT/n).read_bytes() if (ROOT/n).is_file() else b'';added.append(n)
    while queue:
        module=queue.pop(0)
        if module in seen:continue
        found=locate(module)
        if not found:continue # External stdlib/approved wheel modules are pinned separately.
        seen.add(module);name,raw=found
        if name not in files:files[name]=raw;added.append(name)
        parents(name)
        package=module if name.endswith('/__init__.py') else module.rpartition('.')[0]
        for node in ast.walk(ast.parse(raw,filename=name)):
            targets=[]
            if isinstance(node,ast.Import):targets=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom):
                base=resolve_name('.'*node.level+(node.module or ''),package) if node.level else (node.module or '')
                targets=[base]+[base+'.'+a.name for a in node.names if a.name!='*']
            for target in targets:
                if locate(target):edges.append(dict(importer=module,imported=target,line=node.lineno));queue.append(target)
    graph=dict(roots=list(ENTRYPOINTS),modules=sorted(seen),edges=edges,added_files=sorted(set(added)),
        added_hashes={n:sha(files[n]) for n in sorted(set(added))},
        scope='Static repository Import/ImportFrom throughout AST,including lazy function bodies;runtime CPU entrypoint checks complement dynamic imports')
    return files,graph
