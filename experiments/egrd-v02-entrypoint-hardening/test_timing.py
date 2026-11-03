import asyncio,importlib.util,sys,tempfile,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
class TimingTests(unittest.IsolatedAsyncioTestCase):
 def implementation(self):
  self.assertTrue((D/'timing.py').exists(),'Exact SDK deadline observer is missing')
  import timing;return timing
 async def test_deadline_includes_preflight(self):
  m=self.implementation()
  async def runner():
   timeout_context=asyncio.timeout(.045)
   await asyncio.sleep(.025)
   async with timeout_context:await asyncio.sleep(1)
  with tempfile.TemporaryDirectory() as tmp:
   with m.observe_deadline(runner,Path(tmp)/'timing.json') as obs:
    with self.assertRaises(TimeoutError):await runner()
   self.assertTrue(obs.receipt['expired']);self.assertEqual(obs.receipt['observation_count'],1)
   self.assertLess(obs.receipt['deadline_monotonic']-obs.receipt['captured_monotonic'],.06)
   self.assertIsNone(sys.gettrace())
 async def test_backend_timeout_is_not_sdk_deadline(self):
  m=self.implementation()
  async def runner():
   timeout_context=asyncio.timeout(300)
   async with timeout_context:raise TimeoutError('backend')
  with tempfile.TemporaryDirectory() as tmp:
   with m.observe_deadline(runner,Path(tmp)/'timing.json') as obs:
    with self.assertRaises(TimeoutError):await runner()
   self.assertFalse(obs.receipt['expired'])
 async def test_absent_clock_fails_closed(self):
  m=self.implementation()
  async def runner():return 'no timeout'
  with tempfile.TemporaryDirectory() as tmp:
   with self.assertRaises(RuntimeError):
    with m.observe_deadline(runner,Path(tmp)/'timing.json'):await runner()
 async def test_context_budget_aligns_without_changing_deadline(self):
  m=self.implementation()
  self.assertTrue(callable(getattr(m,'align_context',None)),'SDK context still starts after preflight')
  from types import SimpleNamespace
  import time
  now=time.monotonic();obs=SimpleNamespace(receipt=dict(captured=True,deadline_origin_monotonic=now-4.7,deadline_monotonic=now+295.3))
  ctx=SimpleNamespace(agent_start_time=time.perf_counter())
  original=ctx.agent_start_time;m.align_context(ctx,obs)
  self.assertAlmostEqual(ctx.raw_sdk_agent_start_time,original)
  self.assertGreater(time.perf_counter()-ctx.agent_start_time,4.69)
  self.assertEqual(obs.receipt['deadline_monotonic'],now+295.3)
if __name__=='__main__':unittest.main()
