# CPU infrastructure repair complete

**Gate: CPU_INFRA_HARDENING_VERIFIED**, limited to the reproduced faults and declared classifier patterns. This is not GPU readiness, a new candidate result or evidence that A improves repairs.

## Actual verification

Six local regression tests pass. The two historical session6 responses fail against the frozen old classifier as expected, returning CONTINUE where STOP is required. They pass against the new policy. Negative cases preserve ordinary assertion/syntax/user-command failures, successful diagnostic output and source reads. Missing or malformed stop-coverage receipts fail closed.

The new private Kaggle CPU Notebook `wudangdexiaodoashi/r2-infrastructure-cpu-hardening-01`, version2, is COMPLETE. Its actual evidence archive reports PASS using the pinned unmodified official SDK and the existing non-root Linux chroot:

| CPU scenario | Scripted HTTP requests | Observed behavior |
|---|---:|---|
| Ordinary AssertionError | 2 | Continues to a second command; fixture-only terminal callback then ends the control |
| Required Sphinx CLI missing during a tool | 1 | Durable infrastructure latch; no next request |
| Unsupported locale during a tool | 1 | Durable infrastructure latch; no next request |
| CLI absent at source admission | 0 | Stops before any request |

The three normally admitted sandboxes activate locale C, import Sphinx from `/workspace/sphinx`, run the source `sphinx-build --version` and build a minimal unrelated HTML document. The negative preflight deliberately removes only the generated wrapper in its owned sandbox. All four cleanup receipts pass. All recovered patch bytes and observed tracked production-source changes are zero.

The real SDK reports callback exceptions for the deliberate stop cases; those are the expected test mechanism, not failed assertions concealed by a PASS label. A separate composition probe executes the prospective coordinator adapter and verifies its worker selection and STOP admission; it intercepts the GPU-owning parent call and does not execute a real GPU scheduler. Synthetic suffix NOT_RUN markers are contract evidence, not additional benchmark sessions.

CPU attempt1 remains archived as blocked: the initial ordinary-error test driver kept submitting an empty patch and reached80 turns. The corrected control emits a second-command marker and terminates only after observing that marker. Both CPU versions and their actual source hashes are retained; version1 is not described as a pass. The CPU rerun is a diagnostic test repair, not a rerun of the eight real-model pilot sessions.

## Changes and why they address the causes

The existing subprocess SDK skips editable source-package installation, leaving the source CLI unavailable even when Python tests import successfully. A small wrapper outside `/workspace` now invokes the actual source entrypoint. Portable locale C and Python UTF-8 mode remove the inherited unavailable-locale assumption. Source admission runs before the Agent clock/request loop and includes a generic build, with SDK counters observed at zero. Its setup cost must be included in any future global budget.

Structured ADK function responses now participate in a persistent infrastructure latch. The original event is recorded first. A recognized failure raises before the next completion; the worker exports the receipt and the coordinator checks it before ordinary malformed-patch continuation paths. Missing receipts stop. Existing native-verification, isolation, evidence and cleanup admission remains delegated to the original function.

This is an opt-in composition of frozen infrastructure. Neither the official SDK nor the frozen worker/runtime/coordinator files were edited. No Agent prompt, tool schema, sampling setting, task, budget or candidate ZIP was changed. The literal manager class name remains compatible with official subprocess dispatch.

## Limits and next step

The classifier deliberately covers concrete observed stderr patterns and an explicit pinned-dependency list. It cannot infer every possible environment failure. An unknown import, an assertion reproducing a bug or a syntax error introduced by the Agent may be normal repair work and is not automatically classified as infrastructure. Already dispatched parallel tool calls cannot be undone retroactively.

This CPU integration verifies source CLI/environment and interruption wiring, not independent patch correctness, production GPU/backend behavior or hidden-task repair gain. It does not convert the previous pilot into a valid confirmatory experiment. The previous R2/A conclusions and original raw outcomes remain unchanged.

All74 protected historical assets and87 prior-study assets, including the raw GPU artifact, match their starting hashes. No historical verification receipt was rewritten. The new work has zero GPU dispatches, zero real Gemma requests and zero competition submissions.

The infrastructure gap reproduced in the previous pilot is now addressed and CPU-verified. Before another model experiment, freeze a new untouched confirmation cohort and its budget/stop contract, binding this exact adapter version. No new GPU experiment or R3 was created in this work.
