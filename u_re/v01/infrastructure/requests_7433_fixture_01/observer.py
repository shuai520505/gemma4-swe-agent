"""Research-only passive lookup observer. Defines NO fixtures and preserves errors.

Loaded only by a separately labelled diagnostic probe AFTER native Phase 2.
The native Verifier command itself never loads this observer.
"""
import hashlib
import inspect
import json
import os
from pathlib import Path
import traceback

original = None


def emit(value):
    with Path(os.environ['URE_FIXTURE_TRACE']).open('a') as out:
        out.write(json.dumps(value, default=str)+'\n')


def describe(d):
    file = inspect.getsourcefile(d.func)
    return dict(name=d.argname, baseid=d.baseid, scope=d.scope, arguments=d.argnames,
                file=file, line=inspect.getsourcelines(d.func)[1],
                file_sha256=hashlib.sha256(Path(file).read_bytes()).hexdigest() if file else None)


def pytest_configure(config):
    from _pytest.fixtures import FixtureRequest
    global original
    original = FixtureRequest._get_active_fixturedef
    def observed(self, argname):
        relevant = argname in ('httpbin', 'httpbin_secure')
        if relevant:
            defs = getattr(self, '_arg2fixturedefs', {}).get(argname, ()) or ()
            emit(dict(stage='lookup', argument=argname, requesting_fixture=getattr(self,'fixturename',None),
                      request_type=type(self).__name__, definitions=[describe(d) for d in defs],
                      stack=[dict(file=f.filename,line=f.lineno,function=f.name) for f in traceback.extract_stack(limit=16)]))
        try:
            return original(self, argname)
        except BaseException as exc:
            if relevant:
                emit(dict(stage='lookup_error', argument=argname, exception_type=type(exc).__name__,
                          requesting_fixture=getattr(self,'fixturename',None), exception_repr=repr(exc)))
            raise
    FixtureRequest._get_active_fixturedef = observed


def pytest_collection_finish(session):
    manager = session.config.pluginmanager
    plugins = []
    for name, plugin in manager.list_name_plugin():
        plugins.append(dict(name=name, loaded=plugin is not None,
                            file=getattr(plugin,'__file__',None)))
    fixtures = {}
    if session.items:
        for name in ('httpbin','httpbin_secure'):
            fixtures[name] = [describe(d) for d in (session._fixturemanager.getfixturedefs(name,session.items[0]) or ())]
    emit(dict(stage='collection', plugins=plugins, fixtures=fixtures,
              rootpath=str(session.config.rootpath), inipath=str(session.config.inipath),
              inicfg=session.config.inicfg, args=session.config.invocation_params.args,
              environment={n:os.environ.get(n) for n in ('PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_PLUGINS','PYTEST_ADDOPTS','PYTHONPATH')},
              entrypoint_plugins=[dict(name=dist.project_name,version=dist.version,plugin_file=getattr(p,'__file__',None))
                                  for p,dist in manager.list_plugin_distinfo()]))


def pytest_unconfigure(config):
    if original is not None:
        from _pytest.fixtures import FixtureRequest
        FixtureRequest._get_active_fixturedef = original
