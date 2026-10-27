# EGRD V0.3.1 — CPU preflight blocked

Status: **EGRD_V031_BLOCKED_BY_CPU_RUNNER**. This branch is stacked on PR38
5829838066b5c3cfb3037ebbf2613011c2d4f214. No prior PR is merged.

The exact historical S0 ZIP and original Django Issue are recovered and verified.
The real unchanged-source Django failure reproduces again with3 passing controls
and1 executed failing target assertion. A separate bounded password/user-persistence
regression passes. However, the complete two-arm Runner chain does **not** pass.

Private [CPU Notebook141014201](https://www.kaggle.com/code/wudangdexiaodoashi/egrd-v031-evidence-to-patch-cpu)
has two executed versions, both ERROR. V1 fails before the Agent at an inherited
generic dependency stage. V2 gets through the trusted baseline and actual S0 A
Compiler/Runner, exercises all six tools and edits source, then Git diff/submission
fails because the research runtime uses an ordinary file for `/dev/null`.
B is NOT_RUN. There were14 SCRIPTED_ONLY ADK model calls in A, zero Gemma calls.

The ordinary-file null device is replaced in the **current source** by fail-closed
character-device creation. CPU boundary requests/configuration will now be archived
even when a Session fails. These post-V2 fixes have local deterministic tests but
are **not Kaggle-validated**. The successful baseline and A's actual isolation checks
must not be presented as a complete two-arm acceptance.

Both authorized CPU versions are consumed. The dispatch utility only accepts1/2,
uses exclusive request records, and must not be used to create a third run without
new owner permission. No GPU, real Gemma, model weights, formal submission or new
production Agent/Prompt/Skill/controller is introduced.

## Reproduce the audit without rerunning a Notebook

`python -m egrd.v031.collect --blocked` re-derives safe partial results from both
original private ZIPs. `python -m unittest egrd.v031.test_preparation` verifies the
source/receipt/candidate/input locks, observed blocked results and simulated null
device positive/negative cases. The original archives/candidate/SDK evidence are
required; no API or model call is made by these tests.

Only public-safe source, hashes and derived records are committed. Private raw
Issues, probes/regressions, patches, model-boundary data and complete traces remain
under `D:/kaggle/Gemma 4 Developer Agent Competition/private-evidence/egrd_v031/`.
The existing private Dataset V2 is read, not replaced or versioned by this task.

See FINAL_DECISION.md for each acceptance gate and the16 required answers.
