# Deterministic selection and clean environment admission

The final24-task pool was registered before env01 ran. Selection uses SHA256 of S2-EGV-AGENTTOOL-MULTITASK-01|instance_id, first8 per repository and repository-interleaved ranking; final8 are the first eligible rows with a4-task repository cap. Pool SHA and18 actual historical exposures, with file evidence, are in TASK_POOL_PREREGISTRATION.json. Source metadata rankings alone do not constitute Prompt tuning. Three rejected pre-baseline rule proposals remain archived: initial overbroad text matching excluded all tasks, then inherited exclusions overexcluded Rich; actual identity fields replaced these rules before baseline execution. No algorithm result was used to choose tasks.

Native env01 checked all24 with empty Agent Patch, original evaluator test overlay and unmodified native verify_task. No Agent/public-task inference, reference repair or candidate tuning.12 had only ordinary assertion failures;6 collection errors,5 setup errors and1 execution error were excluded. These categories establish admission failure, not a new diagnosis of every excluded task's root cause. No tests or fixtures were changed to admit them. All sandboxes cleaned. Full original JUnit, callchains, import provenance and admission records remain under results/env01/validation and canonical raw.zip.

| Task | Native classification | Admission | JUnit counts |
|---|---|---|---|
| rich_3043 | assertion_failure | eligible | {'tests': 96, 'failures': 3, 'errors': 0, 'skipped': 0} |
| fastapi_9753 | assertion_failure | eligible | {'tests': 12, 'failures': 5, 'errors': 0, 'skipped': 0} |
| requests_7205 | assertion_failure | eligible | {'tests': 219, 'failures': 1, 'errors': 0, 'skipped': 13} |
| rich_3935 | assertion_failure | eligible | {'tests': 22, 'failures': 2, 'errors': 0, 'skipped': 0} |
| fastapi_14186 | collection_error | excluded | {'tests': 3, 'failures': 0, 'errors': 3, 'skipped': 0} |
| requests_7502 | setup_error | excluded | {'tests': 340, 'failures': 0, 'errors': 196, 'skipped': 2} |
| rich_3064 | assertion_failure | eligible | {'tests': 4, 'failures': 3, 'errors': 0, 'skipped': 0} |
| fastapi_14482 | collection_error | excluded | {'tests': 1, 'failures': 0, 'errors': 1, 'skipped': 0} |
| requests_6592 | setup_error | excluded | {'tests': 322, 'failures': 1, 'errors': 185, 'skipped': 2} |
| rich_3882 | assertion_failure | eligible | {'tests': 8, 'failures': 1, 'errors': 0, 'skipped': 0} |
| fastapi_14986 | assertion_failure | eligible | {'tests': 7, 'failures': 5, 'errors': 0, 'skipped': 0} |
| requests_6629 | setup_error | excluded | {'tests': 323, 'failures': 1, 'errors': 185, 'skipped': 2} |
| rich_3471 | assertion_failure | eligible | {'tests': 108, 'failures': 1, 'errors': 0, 'skipped': 0} |
| fastapi_13786 | collection_error | excluded | {'tests': 1, 'failures': 0, 'errors': 1, 'skipped': 0} |
| requests_6757 | collection_error | excluded | {'tests': 1, 'failures': 0, 'errors': 1, 'skipped': 0} |
| rich_3676 | assertion_failure | eligible | {'tests': 22, 'failures': 1, 'errors': 0, 'skipped': 1} |
| fastapi_14978 | collection_error | excluded | {'tests': 3, 'failures': 0, 'errors': 3, 'skipped': 0} |
| requests_7505 | setup_error | excluded | {'tests': 341, 'failures': 0, 'errors': 197, 'skipped': 2} |
| rich_3772 | verifier_execution_error | excluded | None |
| fastapi_15745 | collection_error | excluded | {'tests': 2, 'failures': 0, 'errors': 2, 'skipped': 0} |
| requests_6644 | assertion_failure | eligible | {'tests': 1, 'failures': 1, 'errors': 0, 'skipped': 0} |
| rich_3944 | assertion_failure | eligible | {'tests': 54, 'failures': 1, 'errors': 0, 'skipped': 0} |
| fastapi_14492 | assertion_failure | eligible | {'tests': 2, 'failures': 1, 'errors': 0, 'skipped': 0} |
| requests_6589 | setup_error | excluded | {'tests': 324, 'failures': 0, 'errors': 187, 'skipped': 2} |

The final set is4 Rich,2 FastAPI,2 Requests, all with observable ordinary baseline failures and zero baseline errors. Rich3471/3676/3944 are eligible but beyond the4-Rich cap; FastAPI14492 is later than the first8 accepted. This is infrastructure-based deterministic selection and a limited repository sample, not random evidence of broad generalization. No task was replaced after seeing model outcomes; no GPU outcomes exist.

Task identities include base commit, Issue SHA, task-record SHA, evaluator-overlay SHA and every snapshot file SHA in MULTITASK_GPU_PROTOCOL_DRAFT.json. These hashes are evaluator-side registration data, not model answer material. Environment admission is CPU evidence; fresh GPU-host baseline checks remain required. env01's successful exact observer integration used CPU04 logger bytes; final Git-boundary logger was separately accepted in CPU05 and budget01. This distinction is explicit rather than claiming a single identical payload for all preparations.
