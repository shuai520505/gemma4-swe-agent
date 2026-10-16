"""Host-side observers around pinned organizer APIs; no submission/tool changes."""
import json
from pathlib import Path
import time

from adk_eval_core.tracing import SessionTrace
from google.adk.models.lite_llm import LiteLLMClient
from swegemma.context import SwegemmaContext
from swegemma.evaluate import Evaluator
from swegemma.sandbox.subprocess import SubprocessManager as OrganizerSubprocessManager
from swegemma.harness.verification import strip_protected_files_from_patch

from .evidence import atomic_bytes,atomic_json
from .isolation import prepare_pip_entrypoints


class GuardedClient(LiteLLMClient):
    def __init__(self,guard):
        self.guard=guard

    def __deepcopy__(self,memo):
        # The compiler clones a model, not a new task. Keep its per-worker
        # admission guard/journal (which owns a lock) attached to every clone.
        memo[id(self)]=self
        return self

    def __copy__(self):
        return self

    async def acompletion(self,**kwargs):
        return await self.guard.acompletion(**kwargs)


class DurableContext(SwegemmaContext):
    def __init__(self,*,journal,**kwargs):
        self.journal=journal
        self.observed_event_ids=set()
        self.event_trace=SessionTrace(); self.event_trace.start()
        super().__init__(**kwargs)

    def set_phase(self,phase):
        super().set_phase(phase)
        stage={'Starting':'prepare_agent','Agent Loop':'agent','Verifying':'prepare_verifier'}.get(phase)
        if stage: self.journal.stage(stage,official_phase=phase)

    def set_activity(self,activity):
        super().set_activity(activity)
        self.journal.append(dict(kind='activity',activity=activity))

    def start_agent_session(self):
        super().start_agent_session()
        self.journal.stage('agent',agent_started=True)

    def stop_agent_session(self):
        was_running=self.agent_start_time is not None and self.agent_end_time is None
        super().stop_agent_session()
        if was_running:
            self.journal.stage('save_patch',agent_elapsed_seconds=self.agent_elapsed_seconds)
        if self.submitted_patch is not None:
            self.journal.patch(self.submitted_patch,source='context_agent_end')

    def handle_adk_event(self,event,agent_name=None):
        super().handle_adk_event(event,agent_name=agent_name)
        key=(getattr(event,'id',None) or id(event),bool(getattr(event,'partial',False)))
        if key in self.observed_event_ids: return
        self.observed_event_ids.add(key)
        self.journal.append(dict(kind='adk_event',event=event.model_dump(mode='json',exclude_none=True)),
                            filename='adk_events.jsonl')
        self.event_trace.record_event(event)
        atomic_json(self.journal.directory/'incremental_trace_legacy.json',self.event_trace.to_dict(format='legacy'))
        if self.submitted_patch is not None:
            self.journal.patch(self.submitted_patch,source='explicit_submit_event')
        self.journal.append(dict(kind='counters',llm_calls=self.llm_calls_used,tool_calls=self.tool_calls_used,
                                 patch_submitted=self.patch_submitted))


class SubprocessManager(OrganizerSubprocessManager):
    """Keep the pinned organizer's literal subprocess dispatch name.

    container_setup and verification use type(manager).__name__, not isinstance.
    A differently named observer silently enables Docker-only package setup.
    """
    def __init__(self,*,journal,**kwargs):
        self.journal=journal
        self.agent_id=None
        self.context=None
        super().__init__(**kwargs)

    def start(self):
        stage='prepare_agent' if self.agent_id is None else 'prepare_verifier'
        self.journal.stage(stage)
        sid=super().start()
        try:
            admission=prepare_pip_entrypoints(self.sandboxes[sid]['venv'])
            self.journal.append(dict(kind='sandbox_python_admission',sandbox_id=sid,**admission))
        except BaseException:
            super().stop(sid)
            raise
        if self.agent_id is None: self.agent_id=sid
        self.journal.append(dict(kind='sandbox_started',sandbox_id=sid,stage=stage))
        return sid

    def exec(self,sandbox_id,command,*,timeout=None):
        import hashlib
        verifier=sandbox_id!=self.agent_id
        test_command=verifier and ' -m pytest ' in command
        applying=verifier and ('git apply' in command or 'patch --' in command or 'patch -p' in command)
        old_stage=self.journal.state.get('stage')
        if test_command: self.journal.stage('verification')
        elif applying: self.journal.stage('apply_patch')
        self.journal.append(dict(kind='sandbox_command_start',sandbox_id=sandbox_id,
            command_sha256=hashlib.sha256(command.encode()).hexdigest(),timeout=timeout,
            command_kind='pytest' if test_command else ('apply_patch' if applying else 'other')))
        start=time.monotonic()
        try:
            result=super().exec(sandbox_id,command,timeout=timeout)
            self.journal.append(dict(kind='sandbox_command_end',sandbox_id=sandbox_id,
                exit_code=result.exit_code,elapsed_seconds=time.monotonic()-start))
            # Observe the native fallback extraction before its sandbox is removed.
            if not verifier and 'git diff --binary _swegemma_baseline' in command:
                task=getattr(self.context,'task',None)
                protected=list(getattr(task,'test_files',None) or ())
                text=strip_protected_files_from_patch(result.stdout or '',extra_protected_paths=protected)
                self.journal.patch(text,source='native_git_diff_checkpoint')
            if test_command:
                atomic_json(self.journal.directory/'phase2_execution.json',dict(
                    exit_code=result.exit_code,stdout=result.stdout,stderr=result.stderr,
                    duration_seconds=time.monotonic()-start,source='official_sandbox_exec_return'))
                atomic_bytes(self.journal.directory/'phase2.log',
                    f'STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}'.encode())
            return result
        finally:
            if applying and old_stage: self.journal.stage(old_stage)

    def stop(self,sandbox_id):
        prior=self.journal.state.get('stage','cleanup')
        self.journal.stage('cleanup',sandbox_id=sandbox_id)
        super().stop(sandbox_id)
        self.journal.append(dict(kind='sandbox_stopped',sandbox_id=sandbox_id))
        self.journal.stage(prior)


DurableManager=SubprocessManager


class DurableEvaluator(Evaluator):
    def __init__(self,config,*,journal):
        self.journal=journal
        super().__init__(config)

    async def _run_agent_sandbox(self,*args,**kwargs):
        patch,error,trace=await super()._run_agent_sandbox(*args,**kwargs)
        self.journal.stage('save_patch')
        self.journal.patch(patch,source='official_agent_return')
        if trace is not None:
            atomic_json(self.journal.directory/'agent_boundary_trace.json',trace.to_dict())
            atomic_json(self.journal.directory/'agent_boundary_trace_legacy.json',trace.to_dict(format='legacy'))
        atomic_json(self.journal.directory/'agent_boundary.json',dict(agent_error=error,patch_chars=len(patch or '')))
        self.journal.stage('prepare_verifier')
        return patch,error,trace
