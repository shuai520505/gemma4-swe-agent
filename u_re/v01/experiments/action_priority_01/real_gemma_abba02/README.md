# GPU02 — independent authorized ABBA attempt

Base PR #22: 5598178f4dbf3fdae543ae41e8328f70c0b2b908. GPU02 dispatch used frozen build commit 3500eb8.

Actual Notebook 140233779/v1: ERROR. Four NVIDIA L4 devices were assigned. All frozen model file hashes and both task identities matched. GPU chroot canary passed. The original `native_baseline` lazy import then failed because the packaged repository import closure omitted `fastapi_pilot_01.screen`.

No model was loaded, no Gemma HTTP request occurred, and all four Agent sessions remain NOT_RUN. This is an engineering failure, not an algorithm failure. The original GPU01 and GPU02 records remain immutable. No GPU retry is authorized.

## Targeted CPU repair

`import_closure.py` traverses local Import/ImportFrom nodes including function bodies from the real session and worker entrypoints. `cpu_repair.py` reuses the established CPU single-dispatch controller. Its independent CPU Notebook rechecks both frozen trusted native baselines and executes the exact production worker with one owned synthetic task and a scripted local HTTP model boundary. No real Gemma, GPU, reference patch, or extra research sample is involved.

The CPU probe is not yet executed at this preparation commit. CPU acceptance must come from its real output, not these local tests. The earlier unsent CPU build is retained under `repair_cpu01/offline_build_01/`.

Raw task/evaluator evidence remains in private-evidence outside Git. Public files contain source code, integrity hashes, and derived execution metadata only.
