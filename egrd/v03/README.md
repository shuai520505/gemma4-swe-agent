# EGRD V0.3 — Kaggle repair development platform

Private Dataset: [EGRD Repair Development](https://www.kaggle.com/datasets/wudangdexiaodoashi/egrd-repair-development).
Private CPU Notebook: [141004018/v1](https://www.kaggle.com/code/wudangdexiaodoashi/egrd-v03-repair-development-cpu).
The numeric Notebook ID and version are independently recorded in CPU_EXECUTION_RECORD.json;
the URL opens the Notebook's current page.

Three unchanged-source development probes reproduce Issue-related failures in
Django, xarray and FastAPI. These are owned diagnostic checks, not the official
Native Verifier or a canonical SWE-bench run. No Agent repaired these tasks.

The private dataset contains licensed base archives, hash-pinned offline wheels,
owned executable probes, immutable task metadata and exposure labels. This public
directory contains builders, the CPU driver, safe derived results and an offline
observation schema. Original Issues, raw probes/logs and evaluator contents are
not committed. Access to the private dataset is needed to reproduce execution.

## Reproduction and resource boundary

1. Start from PR37 c8c92a45688a4a7005dea852e7927baefe980402.
2. Verify DATASET_BUILD_V1.json against the original private bundle and its members.
3. The CPU Notebook mounts that dataset read-only, verifies every member, restores
   each base archive, creates one isolated venv per task and installs only pinned
   local wheels. It imports the restored source, executes controls and the target
   check, records before/after source hashes and removes its workspace.
4. `python -m egrd.v03.collect` verifies the private original result archive and
   exports allowlisted derived records. It does not rerun tasks or contact Kaggle.
5. `python -m unittest egrd.v03.test_platform egrd.v023.test_recovery` runs offline
   regressions, requiring the original controlled evidence caches.

`dataset.py`, `notebook.py` and `cli.py` are explicit preparation/dispatch tools,
not automatic retries. Version directories and dispatch records are exclusive.
Do not rerun a mutation command to troubleshoot an ambiguous response. Recover
status read-only. There is one CPU execution; the corrective allowance is unused.
The CLI command surface in this namespace is scoped by the task authorization;
it must not be used to submit a competition entry or request a GPU.

See REPRODUCTION_QUALITY.md for source fidelity and environment limitations,
and REPAIR_RESEARCH_PROTOCOL.md for the next separate model study.
