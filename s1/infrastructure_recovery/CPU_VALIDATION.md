# Official Linux CPU validation

Final acceptance: **r05, 97/97 tests passed**, zero failures, errors or skips.
These are controller/API tests, not Gemma repair results. All five recovery
Notebooks set enable_gpu=false and mount no model.

| Revision | Actual result | Retained limitation |
|---|---|---|
| r01 | Diagnostic complete | Clean Requests fixture reproduction and SDK/wheel inventory |
| r02 | Notebook error after controller tests | Wrong assumption that archive embedded Git HEAD equals Task base; assertion and evidence retained |
| r03 | 93/93 | Source import corrected; Requests providers missing; fresh editable backends missing |
| r04 | 94/94 | Added malformed-usage regression; setup script inspected only |
| r05 | 97/97 | Cached declared build backends tested; Requests blocked; Rich admitted; FastAPI baseline targets missing |

The final 97 comprise the unchanged 77 official Linux CPU/API regressions plus
20 new tests. They cover real server-received cancellation, outer asyncio
deadline propagation, cancellation during response-body read, transport errors
and timeouts, missing/duplicate terminals, invalid/missing usage, logging failure,
actual native Harness/Compiler/ADK Runner deadline, isolated Python import
provenance, missing exit evidence, and constrained offline build dependencies.
Existing context, generation parameters, Patch durability, verification timeout,
outer timeout, orphan cleanup and result-classification regressions remain green.

The native deadline regression uses a real local TCP server and actual official
Runner, not Gemma inference. At 2.996 seconds the official 0.05-minute deadline
reports `Agent exceeded session timeout (0.05 min)`. Its one dispatched request
has a durable cancelled terminal, no response, null usage, and partial usage.
CancelledError propagates to the native timeout handler. Native Trace and
lifecycle rows are retained under r05/validation/recovery_events/native_deadline.
This does not prove vLLM backend reclamation; that remains a future GPU gate.

Final clean Requests run retains 142 passed, 1 skipped, 1 xfailed, 193 fixture
setup errors. Those original baseline tests differ from the historical GPU
Phase2 test set, which had 194 errors. No Agent Patch or evaluator patch is used.
Both import probes and all 33 source/test Python hashes demonstrate the source
path correction without changing implementation or tests. Missing providers
still block Requests as a repair-rate endpoint.

Fresh-task checks use independent clean sandboxes. Rich's original public target
tests pass and cleanup completes. FastAPI's editable import succeeds after the
cached backend install, but baseline target-file admission fails; cleanup still
completes. Neither result is an Agent repair or hidden-test pass.

Reproduction uses the registered CPU Notebook and immutable source payload:
`python -m s1.infrastructure_recovery.build <new-revision> regression` prepares
another CPU-only job. Do not overwrite prior revision directories. Final versions:
swegemma0.2.11, adk-submission0.2.13, adk-eval-core0.1.0, google-adk1.36.1,
google-genai2.11.0, litellm1.82.4. Exact wheel/source maps are in registrations/r05.json.

Final raw ZIP SHA-256:
`62914802d04f25f0e37f04d15f32c257362eb9a2ca79a74a8bc790aafb7c71fd`.
CRC and all 378 manifest entries pass; all 108 registered source files match the
payload. SHA_AUDIT.json verifies 991 pre-recovery branch files, 945 original
baseline files and eight historical CURE archives unchanged. No historical
STOP, Prompt, candidate ZIP or hash record is rewritten.
