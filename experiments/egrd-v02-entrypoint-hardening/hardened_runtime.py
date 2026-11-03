"""V0.2 host-only alignment over the preserved non-root runtime; six tools unchanged."""
import shlex
from dataclasses import asdict
from inherited_hardened_runtime import SubprocessManager as PreviousManager,DurableContext as PreviousContext
from timing import align_context
from r2a_runtime import write
from stop_policy import InfrastructureStop
from source_binding import bind_command

class SubprocessManager(PreviousManager):
 def __init__(self,*args,task_repo=None,**kwargs):
  self.task_repo=task_repo
  super().__init__(*args,**kwargs)
 def exec(self,sid,command,*,timeout=None):
  repo=self.task_repo or getattr(getattr(getattr(self,'context',None),'task',None),'repo',None)
  return super().exec(sid,bind_command(repo,command),timeout=timeout)
 def admit_source(self,sid):
  super().admit_source(sid)
  if self.context.task.repo=='psf/requests':
   command='python3 -c '+shlex.quote("import requests;assert requests.__file__.startswith('/workspace/'),requests.__file__;print(requests.__file__)")
   result=self.exec(sid,command,timeout=30)
   write(self.journal.directory/'REQUESTS_SOURCE_BINDING.json',dict(command=command,result=asdict(result)))
   if result.exit_code:raise InfrastructureStop('REQUESTS_SOURCE_BINDING_FAILED')

class DurableContext(PreviousContext):
 def start_agent_session(self):
  super().start_agent_session() # Includes inherited CLI preflight after actual SDK timeout construction.
  observation=getattr(self,'deadline_observation',None)
  if observation is None:raise InfrastructureStop('SDK_DEADLINE_OBSERVER_MISSING')
  align_context(self,observation)
  self.journal.append(dict(kind='SDK_clock_aligned',raw_sdk_start_perf_counter=self.raw_sdk_agent_start_time,aligned_start_perf_counter=self.agent_start_time,deadline_monotonic=observation.receipt['deadline_monotonic']))
