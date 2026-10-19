# Pre-GPU acceptance

CPU02 official Linux acceptance: **100/100**, zero failures/errors/skips.
This is the unchanged recovery97 suite plus three scheduler-metric parser tests.
The existing suite includes real official Compiler, empty-state ADK Runner and
actual HTTP client serialization for control and E3, full Prompt preservation,
six tools, generation/context bounds, real socket/native deadline cancellation,
Patch durability, process cleanup and wrong-installed-package provenance tests.
No CPU result is Gemma inference or repair success.

Full official `verify_task` was executed on a clean unrepaired `rich_3278`
snapshot. Only the native verifier applied the original evaluator test patch;
no reference repair was used. Result: **7 passed,16 assertion failures**, exit1,
resolved=false. There were no collection/import/fixture/setup errors, and sandbox
cleanup completed. The original baseline file had7 passing tests; the evaluator
adds the failing cases. This establishes a usable environment and discriminating
baseline, not a failed Agent. Evaluator artifacts remain outside Agent sandboxes.

Task/snapshot/Issue hashes exactly equal the prior recovery draft. Workspace
import and original baseline tests are rechecked by the recovery suite. Full
Phase2 import provenance is retained alongside commands/results and raw fields.

The first CPU preparation Notebook exited before Phase2 because the new preflight
script omitted required `EvalConfig.models`. Its actual97+3 tests had passed,
but no final gate existed, so it was not GPU eligible. That Notebook, initial
registration and raw archive are retained under results/cpu, SHA256
`82e042a47fb994524ed800bb3ba7f8036d7eeaa491066f7c087c5404f4d0989c`.
The corrected CPU02 is a separate preparation version before GPU registration,
not a rerun/hotfix of a frozen GPU experiment or an Agent strategy change.

Accepted CPU02 raw SHA256:
`5fe107022d9f6dd0c48ee9be04ceb5364d39b69d9c55bb6eea0a7bae68b2adc4`.
CRC and430 manifest entries pass. All115 registered source files match payload
bytes. All108 source files from the prior97-test r05 payload remain identical;
the seven study files add orchestration/readiness only. Exact accepted source
map is registration_cpu02.json; initial registration.json is not rewritten.

The GPU Notebook uses those exact CPU02 runtime files. Its sealed bootstrap also
checks all124 task wheels against the prior official SHA/size map before
installation, in addition to the existing41 model Wheelhouse checks. This
standard-library hash admission changes no Agent/runtime source. Its exact code
is visible in notebooks/gpu/study.ipynb and covered by gpu_notebook.json SHA.
The builder creates the base Notebook; the final sealed Notebook is authoritative.
Do not regenerate it after registration. The runtime will repeat native Rich
environment readiness on the GPU host before starting the model, then require
real model/usage/context and scheduler-idle gates before either Agent.
