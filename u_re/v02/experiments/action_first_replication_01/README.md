# U-RE V0.2 independent Action-First replication

Final status: **V02_TASK_POOL_INSUFFICIENT**. The preregistered screening STOP
fired after five actual native baselines, with one eligible task. The remaining
eleven screening slots are NOT_RUN, not known failures. No GPU batch was saved.

- Base: PR24 `f5beac9979a0a9d307b14f686d3477b09a021a95`, unmerged.
- Preregistration: `c3cfb75418e6e9b34a88542c722d5c496f9dd031`, before all new
  baseline requests. Seed17, max16, first4 eligible, unchanged paired arms.
- Pool:129 original identities,95 conservatively excluded,34 remaining FastAPI
  identities. SAME_REPOSITORY_REPLICATION; no cross-repository claim.
- Actual screening: Kaggle140334057/v1 COMPLETE. Five empty-patch native
  verify_task calls, zero Agent/model calls. JUnit/TaskResult, workspace source
  provenance, unchanged-file records and cleanup agree for all five.
- Raw private archive SHA256:
  `e2798683afa7712a4bdc71daf1f74cff425160d92dcccaf2d5b1b41724cc700e`.

`TASK_ADMISSION_LEDGER.json` contains final classifications; `SELECTED_TASKS.json`
contains the one eligible identity. `FINAL_DECISION.md` answers Q1-Q17.
`ENGINEERING_FAILURES.json` retains two earlier CPU ERRORs and one UNKNOWN save.
`RAW_ARCHIVES.json` locates the controlled private archives and their checksums.

The final tree deliberately contains no unvalidated V02 GPU runner or sealed
production payload. Task admission stopped before that stage. PR24's measured
GPU03 runner remains unchanged and reusable, but is not a V02 acceptance result.
No candidate Prompt, ZIP, official tool, native test or Verifier was changed.

## Reproduce the offline audit

From the repository root, using the private raw archive location in the ledger:

```powershell
python -m unittest u_re.v02.experiments.action_first_replication_01.test_local -v
```

The audit checks the actual downloaded JUnit, TaskResult, source-boundary records,
cleanup and all129 snapshot identities. It does not run any task or call Kaggle.
`audit.screen(archive, 'screen04')` re-derives the screening view; the independent
public Issue contract review in SELECTED_TASKS is explicitly separate from its
automatic output. No reference/gold patch was accessed.

Do not invoke an old launch again. Every CPU attempt has its own durable claim.
The original UNKNOWN_STOP events are preserved even where later read-only
evidence confirmed resource identity and completion.
