# 12B primary, 31B bounded fallback

V0.2 real model tests: NOT_RUN. No 12B or 31B performance, latency, repair or Skill compliance improvement is claimed.

Exact original configs are retained in configs/12b.json, configs/31b.json and MODEL_CONFIGURATIONS.json. Both use context32768, output8192, thinking4096/include_thoughts, temperature0.2/top_p0.95, Agent300s, command120s,60 charged tools and80 turns. Model mounts remain google/gemma-4/Other/<12B-or-31B-alias>/2. 31B has no 12B hf-overrides. Both real official Compiler paths pass; this does not establish model tool-calling reliability.

Prior REAL_GPU_OBSERVATION: V0.1 loaded 12B on four L4 in209.26s, but Skill calls were absent; 31B was not run in that pilot. Prior frozen 31B availability is historical evidence, not new V0.2 execution.

New public engineering smoke locks requests_6589 and requests_6592, selected prospectively as the first two sorted public Requests tasks. They are not held-out efficacy confirmation and do not reuse Pylint8898, Sphinx11445 or Sympy24661.

At most two distinct smoke tasks per model. If official tools/infrastructure are known good and 12B repeatedly does not call Skill, produces invalid arguments or demonstrates confirmed workflow breakdown on both tasks, stop12B and request separate31B confirmation. A single unsuccessful repair never disqualifies12B. Infrastructure failure stops immediately. If31B also fails Skill/workflow, stop for entrypoint/architecture investigation; do not keep spending GPU.

model_selection.py implements the bounded recommendation and has six tests. The current Coordinator automatically diagnoses repeated missing calls; invalid arguments/workflow breakdown need explicit evidence review before assigning those model-level diagnoses. No automatic model dispatch occurs. Prepared31B Notebook has a distinct slug, output directory and future exclusive claim path. Neither future claim has been consumed.

Before any dispatch: CPU acceptance must pass, human GPU confirmation must be recorded, quota/reservations must be read afresh, source/package locks must match and real allocation must prove exactly four accessible L4 cards. The user subsequently answered '允许CPU和GPU'; GPU12_AUTHORIZATION records that permission. CPU02 still has187 Native fixture errors, so authorization was not used and no GPU claim exists. Prepared notebooks deliberately refuse execution while CPU is blocked. Maximum notebook window18000s with900s final archive reserve; no formal submission.
