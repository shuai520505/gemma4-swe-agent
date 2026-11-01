"""Post-run diagnostic cases, explicitly exploratory, no outcome-driven reruns."""
import ast,hashlib,json,re,sys,tarfile,zipfile
from pathlib import Path
D=Path(__file__).resolve().parent
def source(task,suffix):
    with tarfile.open(D/'assets/snapshots'/f'{task}.tgz') as t:
        m=next(m for m in t.getmembers() if m.name.endswith('/'+suffix))
        return t.extractfile(m).read().decode()
def patched(s,patch,path):
    lines=patch.splitlines(keepends=True);active=False;out=[];at=0;i=0;original=s.splitlines(keepends=True)
    while i<len(lines):
        l=lines[i]
        if l.startswith('diff --git '):active=l.rstrip().endswith(' b/'+path)
        if active and l.startswith('@@ '):
            m=re.match(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@',l);start=int(m[1])-1
            out.extend(original[at:start]);at=start;i+=1
            while i<len(lines) and not lines[i].startswith(('diff --git ','@@ ')):
                l=lines[i]
                if l.startswith(' '):assert original[at]==l[1:],(at,repr(original[at]),repr(l));out.append(l[1:]);at+=1
                elif l.startswith('-'):assert original[at]==l[1:];at+=1
                elif l.startswith('+'):out.append(l[1:])
                i+=1
            continue
        i+=1
    out.extend(original[at:]);return ''.join(out)
def main():
    # Use actual pinned pure-Python docutils wheel, not a stand-in StringList.
    wheel=next((D/'assets/wheels').glob('docutils-*.whl'));sys.path.insert(0,str(wheel))
    from docutils.statemachine import StringList
    original=source('sphinx-doc__sphinx-11445','sphinx/util/rst.py')
    observations=[]
    for arm,index in [('original',None),('R2',5),('A',6)]:
        text=original if index is None else patched(original,(next((D/'results').glob(f'{index:02d}_*/agent.patch'))).read_text(encoding='utf8'),'sphinx/util/rst.py')
        tree=ast.parse(text);selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepend_prolog' or isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id in ['docinfo_re','SECTIONING_CHARS'] for x in n.targets)]
        ns=dict(re=re,StringList=StringList);exec(compile(ast.Module(body=selected,type_ignores=[]),'<actual-upstream-and-frozen-patch>','exec'),ns)
        for title in [':mod:`mypackage2`',':py:mod:`mypackage2`',':std:ref:`mypackage2`']:
            for char in ['=','-','~','^','*','+','#']:
                content=StringList([title,char*len(title),'','Content']);ns['prepend_prolog'](content,'.. |psf| replace:: Python Software Foundation')
                adjacent=content.index(title)+1<len(content) and content[content.index(title)+1]==char*len(title)
                observations.append(dict(arm=arm,case=title+' underline '+char,title_and_underline_adjacent=adjacent,lines=list(content)))
        content=StringList([':Author: John Doe',':Date: 2026-01-01','','Title','=====']);ns['prepend_prolog'](content,'.. |psf| replace:: Python Software Foundation')
        observations.append(dict(arm=arm,case='ordinary docinfo retained before prolog',passed=content[0]==':Author: John Doe' and content[1]==':Date: 2026-01-01',lines=list(content)))
    result=dict(evidence_type='CPU_VERIFIED',scope='Actual prepend_prolog AST and docutils StringList with exact frozen production patches. Post-run exploratory counterexamples, not new model runs or changed trusted tests.',original_source_sha256=hashlib.sha256(original.encode()).hexdigest(),docutils_wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),observations=observations)
    (D/'POST_RUN_CPU_SEMANTIC_DIAGNOSTICS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    runtime=D/'review-runtime';runtime.mkdir(exist_ok=True)
    package=runtime/'original-sympy-source.zip'
    with tarfile.open(D/'assets/snapshots/sympy__sympy-24661.tgz') as t,zipfile.ZipFile(package,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for m in t.getmembers():
            if m.isfile() and '/sympy/' in m.name and m.name.endswith('.py'):
                z.writestr('sympy/'+m.name.split('/sympy/',1)[1],t.extractfile(m).read())
    sys.path[:0]=[str(package),str(next((D/'assets/wheels').glob('mpmath-*.whl')))]
    import sympy
    from sympy.parsing import sympy_parser as parser
    original_parser=source('sympy__sympy-24661','sympy/parsing/sympy_parser.py')
    cases=[]
    for arm,index in [('original',None),('A',7),('R2',8)]:
        text=original_parser if index is None else patched(original_parser,next((D/'results').glob(f'{index:02d}_*/agent.patch')).read_text(encoding='utf8'),'sympy/parsing/sympy_parser.py')
        node=next(n for n in ast.parse(text).body if isinstance(n,ast.ClassDef) and n.name=='EvaluateFalseTransformer')
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<frozen-transformer>','exec'),parser.__dict__)
        for expression,cls in [('1 < 2',sympy.Lt),('1 <= 2',sympy.Le),('1 > 2',sympy.Gt),('1 >= 2',sympy.Ge),('1 == 2',sympy.Eq),('1 != 2',sympy.Ne)]:
            value=parser.parse_expr(expression,evaluate=False)
            cases.append(dict(arm=arm,expression=expression,result=str(value),passed=isinstance(value,cls)))
        for expression in ['1 < 2 < 3','1 < 2 < 0','x < y < z','1 + 2','(1 + 2) < 4']:
            try:cases.append(dict(arm=arm,expression=expression,result=str(parser.parse_expr(expression,evaluate=False)),type=type(parser.parse_expr(expression,evaluate=False)).__name__))
            except Exception as exc:cases.append(dict(arm=arm,expression=expression,error=type(exc).__name__))
        cases.append(dict(arm=arm,case='evaluate=True preserves evaluated SymPy true',passed=parser.parse_expr('1 < 2') is sympy.true))
    result['sympy']=dict(version=sympy.__version__,scope='Exact original source imported from private local ZIP, unchanged frozen transformer compiled in memory; Windows CPU Python '+sys.version.split()[0]+', not a replacement for native Linux test receipt.',cases=cases)
    (D/'POST_RUN_CPU_SEMANTIC_DIAGNOSTICS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(sphinx_counts={arm:sum(r.get('title_and_underline_adjacent',False) for r in observations if r['arm']==arm) for arm in ['original','R2','A']},sympy_single_relation_passes={arm:sum(r.get('passed',False) for r in cases if r['arm']==arm) for arm in ['original','R2','A']}),indent=2))
if __name__=='__main__':main()
