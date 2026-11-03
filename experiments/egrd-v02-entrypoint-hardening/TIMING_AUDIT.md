# SDK deadline and Worker clock

STATIC_ANALYSIS: frozen swegemma 0.2.11 constructs asyncio.timeout(300) in run_agent_sandbox before start_agent_session. Construction fixes the absolute loop deadline. The inherited CLI preflight then runs before the timeout context is entered and before the previous Context start counter.

Preserved V0.1 REAL_GPU_OBSERVATION: elapsed from Agent Loop was 300.000776s while the late Context counter was 295.308s, with about 4.69978s preflight. The old >=299 counter inference was incorrect. Historical receipts are unchanged.

V0.2 passively observes the actual local asyncio.Timeout object in the pinned runner frame. It reads public when()/expired(), records loop/monotonic calibration and deadline minus the unchanged 300s budget, and restores tracing afterward. A missing, rescheduled or incompatible observation fails closed. Existing tracing is not overwritten.

The research Context's public agent_start_time is aligned to the observed origin, converting monotonic/perf_counter clocks. Its raw original start is retained. This makes official get_status and budget checks include preflight. The SDK timeout object is never changed. Official HarnessLimits is frozen; verification_timeout_seconds is asserted to be 300 rather than mutated.

Classification requires both actual timeout expiration and the SDK timeout label. A backend TimeoutError is not Agent Timeout. Outer/stage timeout remains Worker Timeout. Infrastructure stops, backend errors, raw SDK error and cleanup receipts stay distinct.

CPU_VERIFIED: real asyncio boundary tests include preflight, reject backend error as timeout, fail closed without an SDK deadline, and preserve raw/adjusted Context clocks without extending the deadline. sdk_context_check additionally exercises the installed official get_status against the research Context. Synthetic 4.7s fixtures are not presented as a new 300s GPU timeout measurement.

SDK source and package versions are frozen in RUNTIME_LOCK.json. This observation depends on that implementation and must be revalidated for another SDK. The remaining uncertainty is actual new-model deadline cancellation under GPU load, NOT_RUN in this round.
