"""Passive plugin registration for native App and nested AgentTool Runners."""
from contextlib import contextmanager
from unittest.mock import patch
from google.adk.runners import Runner
from .runtime_audit import AuditPlugin


@contextmanager
def observe_nested(manager, context, journal):
    original=Runner.__init__
    observer=None
    def initialize(obj,*args,**kwargs):
        nonlocal observer
        if observer is None:
            observer=AuditPlugin(manager.sandboxes[manager.agent_id]['workspace'],context,journal)
        app=kwargs.get('app')
        plugins=list((app.plugins if app is not None else kwargs.get('plugins')) or [])
        if not any(p.name==observer.name for p in plugins):plugins.append(observer)
        if app is not None:app.plugins=plugins
        else:kwargs['plugins']=plugins
        original(obj,*args,**kwargs)
    with patch.object(Runner,'__init__',initialize):yield
