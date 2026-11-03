"""Passive host observation of the SDK's real asyncio.Timeout object; no SDK edits."""
import asyncio,json,sys,time
from contextlib import contextmanager
from pathlib import Path

class DeadlineObservation:
 def __init__(self,runner,budget_seconds):
  self.code=runner.__code__;self.budget=budget_seconds;self.timeout=None
  self.receipt=dict(captured=False,observation_count=0,clock='time.monotonic calibrated to asyncio loop.time',configured_seconds=budget_seconds,scope='HOST_OBSERVATION_NOT_AGENT_CONTROL')
 def trace(self,frame,event,arg):
  if frame.f_code is not self.code:return None
  if event=='line' and self.timeout is None:
   obj=frame.f_locals.get('timeout_context')
   if isinstance(obj,asyncio.Timeout) and obj.when() is not None:
    loop=asyncio.get_running_loop();before=time.monotonic();loop_now=loop.time();after=time.monotonic()
    offset=(before+after)/2-loop_now;deadline=obj.when()+offset
    self.timeout=obj;self.receipt.update(captured=True,observation_count=1,deadline_loop_time=obj.when(),deadline_monotonic=deadline,deadline_origin_monotonic=deadline-self.budget,captured_monotonic=after,clock_calibration_uncertainty_seconds=after-before,SDK_source_file=self.code.co_filename,SDK_line=frame.f_lineno)
  return self.trace
 def finish(self):
  self.receipt['observed_end_monotonic']=time.monotonic()
  self.receipt['expired']=self.timeout.expired() if self.timeout else None
  self.receipt['deadline_rescheduled']=self.timeout.when()!=self.receipt['deadline_loop_time'] if self.timeout else None
  return self.receipt

@contextmanager
def observe_deadline(runner,path,budget_seconds=300):
 if sys.gettrace() is not None:raise RuntimeError('Existing trace observer: cannot safely attach SDK deadline observation')
 observation=DeadlineObservation(runner,budget_seconds);failure=None
 sys.settrace(observation.trace)
 try:yield observation
 except BaseException as exc:failure=exc;raise
 finally:
  sys.settrace(None);r=observation.finish();p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,indent=2),encoding='utf8')
  if failure is None and (not r['captured'] or r['deadline_rescheduled']):raise RuntimeError('Official SDK deadline not captured or changed; stop rather than infer elapsed threshold')

def deadline_evidence(receipt,agent_error,cleanup_verified):
 actual=receipt.get('captured') is True and receipt.get('expired') is True and not receipt.get('deadline_rescheduled')
 return dict(official_agent_deadline=bool(actual and str(agent_error or '').startswith('Agent exceeded session timeout')),cleanup_verified=cleanup_verified,cutoff_monotonic=receipt.get('deadline_monotonic'))


def align_context(context,observation):
 r=observation.receipt
 if not r.get('captured'):raise RuntimeError('SDK deadline must be observed before context alignment')
 raw=context.agent_start_time;perf=time.perf_counter();mono=time.monotonic()
 context.raw_sdk_agent_start_time=raw
 context.agent_start_time=r['deadline_origin_monotonic']+(perf-mono)
 r.update(raw_context_start_perf_counter=raw,aligned_context_start_perf_counter=context.agent_start_time,context_clock_conversion_uncertainty='sequential perf_counter/monotonic sample, recorded separately from SDK deadline')
