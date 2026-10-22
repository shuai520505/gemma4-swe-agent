"""Reusable native single-Agent phase; no model startup/save API or mock inside.

Caller supplies the approved model registry. CPU probe supplies scripted HTTP;
future GPU caller must supply the separately authorized pinned vLLM registry.
"""
import hashlib
import json
from pathlib import Path

from harness_v2.evidence import Journal,atomic_json
from harness_v2.official import DurableContext
from swegemma.harness.agent_runner import run_agent_sandbox
from .CHROOT_TASK_RUNTIME import SubprocessManager as AcceptedManager

HERE=Path(__file__).resolve().parent


def runtime_fingerprint(value):
    normalized=dict(runtime=value['runtime'],dependencies=sorted(value['dependencies'],key=lambda x:x['name'].lower()))
    return hashlib.sha256(json.dumps(normalized,sort_keys=True).encode()).hexdigest()


class SubprocessManager(AcceptedManager):
    def start(self):
        sid=super().start()
        value=json.loads((self.journal.directory/('runtime_'+sid+'.json')).read_bytes())
        expected=json.loads((HERE/'APPROVED_RUNTIME_FINGERPRINT.json').read_bytes())['runtime_manifest_sha256']
        try:assert runtime_fingerprint(value)==expected,'Staged approved runtime drift before Agent inference'
        except BaseException:self.stop(sid);raise
        return sid


async def run(cfg,task,snapshot,output,*,base_snapshot=None,incremental_patch=None):
    output=Path(output);output.mkdir(parents=True,exist_ok=False);journal=Journal(output)
    manager=SubprocessManager(journal=journal,base_dir=output/'agent_roots',timeout_seconds=120,task_wheels=cfg.wheels_dir)
    context=DurableContext(journal=journal,docker_manager=manager,task=task,budget=cfg.budget,harness=cfg.harness)
    manager.context=context
    patch_text='';error=None;trace=None
    try:
        patch_text,error,trace=await run_agent_sandbox(manager,cfg,task,snapshot,
            patch_path=incremental_patch,base_snapshot_path=base_snapshot,context=context)
        (output/'returned.patch').write_bytes(patch_text.encode())
        if trace is not None:atomic_json(output/'native_trace.json',trace.to_dict())
        atomic_json(output/'agent_result.json',dict(error=error,patch_bytes=len(patch_text.encode()),
            agent_seconds=context.agent_elapsed_seconds,charged_tools=context.tool_calls_used,
            patch_submitted=context.patch_submitted,model_calls=context.llm_calls_used))
        return patch_text,error,context
    finally:
        manager.cleanup_all()
        atomic_json(output/'cleanup.json',dict(complete=not manager.sandboxes,owned_roots_removed=all(r['root_removed'] for r in manager.cleanup_records)))
