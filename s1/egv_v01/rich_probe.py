"""Evaluator-only read-only diagnostics, never included in the submission ZIP.

Runs the SAME public native test file with transparent Python tracing. Native
Phase2 is separately retained and never replaced with these observations.
"""
import collections
import difflib
import hashlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import re
import sys


def main():
    wheel=os.environ.get('EGV_PYGMENTS_WHEEL')
    if wheel:sys.path.insert(0,wheel)
    import pygments
    import pytest
    from pygments.styles.monokai import MonokaiStyle
    from pygments.styles.default import DefaultStyle
    from pygments.token import Token
    import rich.markdown
    import rich.syntax
    from rich.console import Console
    target=Path('tests/test_markdown.py').resolve()
    observed={};branches=collections.Counter();styles=collections.Counter()
    def trace(frame,event,arg):
        file=frame.f_code.co_filename.replace('\\','/')
        if event=='exception' and Path(file).resolve()==target and frame.f_code.co_name in ('test_markdown_render','test_inline_code'):
            observed[frame.f_code.co_name]={k:v for k,v in frame.f_locals.items() if isinstance(v,str)}
        if event=='call' and file.endswith('/rich/markdown.py') and frame.f_code.co_name=='on_text':
            branches[type(frame.f_locals.get('self')).__name__+'.on_text']+=1
        if event=='return' and file.endswith('/rich/syntax.py') and frame.f_code.co_name=='get_style_for_token':
            styles[str(frame.f_locals.get('token_type'))+' => '+str(arg)]+=1
        return trace
    source_files=[Path('rich/markdown.py'),target]
    before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    sys.settrace(trace)
    try:code=pytest.main(['tests/test_markdown.py','-p','no:anyio','-o','timeout=0','-o','python_classes=Test* *Test','-q'])
    finally:sys.settrace(None)
    ansi=re.compile(r'\x1b\[[0-9;]*m')
    comparisons={}
    for name,values in observed.items():
        expected=values['expected'];actual=values.get('rendered_markdown',values.get('result'))
        assert actual is not None
        comparisons[name]=dict(strings=values,plain_equal=ansi.sub('',actual)==ansi.sub('',expected),
            actual_sgr=dict(collections.Counter(ansi.findall(actual))),expected_sgr=dict(collections.Counter(ansi.findall(expected))),
            character_diff=list(difflib.ndiff([expected],[actual])))
    snapshots={}
    for obj in (rich.markdown.Markdown.__init__,rich.markdown.MarkdownContext.__init__,rich.syntax.PygmentsSyntaxTheme.get_style_for_token):
        snapshots[obj.__qualname__]=inspect.getsource(obj)
    output=dict(scope='Read-only CPU diagnostic, not a model repair or replacement score',pytest_exit_code=code,
        python=sys.executable,sys_path=sys.path,workspace=str(Path.cwd().resolve()),
        environment={k:os.environ.get(k) for k in ('TERM','COLORTERM','NO_COLOR','FORCE_COLOR','PYTHONSAFEPATH','PYTHONNOUSERSITE')},
        package_versions={n:importlib.metadata.version(n) for n in ('rich','pygments','pytest','markdown-it-py')},
        pygments_actual_version=pygments.__version__,pygments_file=pygments.__file__,
        markdown_file=rich.markdown.__file__,markdown_realpath=str(Path(rich.markdown.__file__).resolve()),
        source_before=before,source_after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
        expected_actual=comparisons,target_branch_calls=dict(branches),syntax_style_returns=dict(styles),
        declared_styles={cls.__name__:{str(t):cls.style_for_token(t) for t in (Token.Name.Tag,Token.Operator,Token.Name,Token.Name.Function,Token.Text)} for cls in (MonokaiStyle,DefaultStyle)},
        source_snippets=snapshots,test_render_source=target.read_text(),
        Console_explicit_truecolor=dict(color_system=Console(color_system='truecolor').color_system,is_terminal=Console(color_system='truecolor').is_terminal))
    assert output['source_before']==output['source_after'],'Diagnostic changed source/test bytes'
    Path(os.environ['EGV_DIAG_OUTPUT']).write_text(json.dumps(output,indent=2))


if __name__=='__main__':main()
