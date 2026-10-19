"""Research-only passive ADK plugin. Never included in submission.zip."""
import hashlib
import time
import subprocess
from pathlib import Path
from google.adk.plugins.base_plugin import BasePlugin


def snapshot(workspace):
    root = Path(workspace)
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and not {'.git', '__pycache__', '.pytest_cache'}.intersection(p.relative_to(root).parts)}


class AuditPlugin(BasePlugin):
    def __init__(self, workspace, context, journal):
        super().__init__(name='s2_passive_audit')
        self.workspace, self.context, self.journal = workspace, context, journal

    def record(self, kind, **data):
        if kind in ('tool_start','tool_end') and data.get('tool')=='egv_verifier':
            git={}
            for name,args in [('status',['status','--porcelain']),('diff',['diff','--binary','--no-ext-diff'])]:
                try:
                    r=subprocess.run(['git','--no-optional-locks','-c','core.fsmonitor=false','-C',str(self.workspace),*args],
                                     capture_output=True,text=True,timeout=5)
                    git[name]=dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr)
                except Exception as exc:git[name]=dict(error=repr(exc))
            data['git_boundary']=git
        self.journal.append(dict(kind=kind, monotonic=time.monotonic(),
            counted_tools=self.context.tool_calls_used, **data), filename='nested_audit.jsonl')

    async def before_tool_callback(self, *, tool, tool_args, tool_context):
        self.record('tool_start', actor=tool_context.agent_name, tool=tool.name,
                    args=tool_args, call_id=tool_context.function_call_id, files=snapshot(self.workspace))

    async def after_tool_callback(self, *, tool, tool_args, tool_context, result):
        self.record('tool_end', actor=tool_context.agent_name, tool=tool.name,
                    args=tool_args, call_id=tool_context.function_call_id, result=result,
                    files=snapshot(self.workspace))

    async def on_tool_error_callback(self, *, tool, tool_args, tool_context, error):
        self.record('tool_error', actor=tool_context.agent_name, tool=tool.name, error=repr(error))

    async def before_model_callback(self, *, callback_context, llm_request):
        self.record('model_start', actor=callback_context.agent_name)

    async def after_model_callback(self, *, callback_context, llm_response):
        usage = llm_response.usage_metadata
        self.record('model_end', actor=callback_context.agent_name,
                    usage=usage.model_dump(mode='json') if usage else None)

    async def on_event_callback(self, *, invocation_context, event):
        self.record('native_event', actor=event.author, event=event.model_dump(mode='json', exclude_none=True))
