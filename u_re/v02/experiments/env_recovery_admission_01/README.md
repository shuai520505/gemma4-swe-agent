# U-RE V02b: dependency recovery and prospective admission

Result: **V02B_ENV_RECOVERY_ADMISSION_COMPLETE**.
Four tasks formally admitted: carried fastapi_5077 plus new fastapi_11355,
fastapi_14463 and fastapi_9555. Final packaged production CPU E2E passed.
**GPU NOT_AUTHORIZED; no real Gemma ran in this study.**

Read FINAL_DECISION.md for Q1–Q20; exact identities and evidence hashes are in
SELECTED_TASKS.json, RAW_ARCHIVES.json and INTEGRITY_MANIFEST.json. All evaluator
test text, raw JUnit/TaskResult, snapshots and model/tool traces remain outside
Git in private evidence. Public files are code, safe derived metadata and fixed
public dependency wheels with original licenses retained inside the wheels.

Protocol/carry preregistration preceded new native outcomes (6456212); recovered
environment and strict research classification were frozen before the first new
baseline (5339589, finalized builder binding21377a3). Screening was dispatched
from6da9ce5 and stopped after the first3 new tasks reached4 total. Old PR25 STOP,
recovery01 ERROR and all original UNKNOWN_STOP events are preserved.

## Reproduce/audit without dispatching

```text
python -m unittest u_re.v02.experiments.env_recovery_admission_01.test_local -v
python -m u_re.v02.experiments.env_recovery_admission_01.production_audit <private-e2e02-archive.zip> e2e02
python -m u_re.v02.experiments.env_recovery_admission_01.release
```

Actual-evidence tests need the private downloaded archives at their recorded
locations. Missing evidence must fail, never synthesize a PASS. These commands
do not execute official tasks, install dependencies or make Kaggle calls.
`audit recovery` is a **freeze-generation** command and must not be rerun to
change the already frozen environment/protocol after screening.

Existing attempts have exclusive dispatch claims. Never relaunch them. Future
CPU iterations require a new identity. GPU_EXECUTION_PROPOSAL.md describes the
new separately authorized scope; current production GPU entry rejects absent or
mismatched authorization before model allocation. The local e2e01 pre-dispatch
seal rejection is not a Kaggle failure or a CPU acceptance result; e2e02 is the
accepted final payload. Shared production code was not changed after acceptance.
