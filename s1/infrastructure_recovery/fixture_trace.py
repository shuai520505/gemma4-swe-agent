"""Read-only diagnostic pytest plugin: no fixtures, selection or assertion edits."""
import inspect
import json
import os
from pathlib import Path
import traceback

original=None


def record(request,argname,stage,error=None):
    try:
        definitions=getattr(request,'_arg2fixturedefs',{}).get(argname,()) or ()
        value=dict(stage=stage,argument=argname,request_fixture=getattr(request,'fixturename',None),
            request_type=type(request).__name__,definition_count=len(definitions),error=error,
            definitions=[dict(name=d.argname,baseid=d.baseid,file=inspect.getsourcefile(d.func),
                line=inspect.getsourcelines(d.func)[1]) for d in definitions],
            stack=[dict(file=f.filename,line=f.lineno,function=f.name) for f in traceback.extract_stack(limit=12)])
        with Path(os.environ['S1_FIXTURE_TRACE']).open('a') as out:out.write(json.dumps(value)+'\n')
    except Exception:pass


def pytest_configure(config):
    from _pytest.fixtures import FixtureRequest
    global original
    original=FixtureRequest._get_active_fixturedef
    def observed(self,argname):
        relevant=argname in ('httpbin','httpbin_secure')
        if relevant:record(self,argname,'enter')
        try:return original(self,argname)
        except BaseException as exc:
            if relevant:record(self,argname,'raise',type(exc).__name__+': '+str(exc))
            raise
    FixtureRequest._get_active_fixturedef=observed


def pytest_unconfigure(config):
    if original is not None:
        from _pytest.fixtures import FixtureRequest
        FixtureRequest._get_active_fixturedef=original
