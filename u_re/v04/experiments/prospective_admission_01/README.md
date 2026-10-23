# U-RE V04 prospective task admission

Actual result: **V04_EGR_GPU_READY**, GPU execution NOT_AUTHORIZED. Started from actual open/unmerged PR29 a44cc483a6c114940a65322371dfa87ea5d9dd5e on branch feat/u-re-v04-egr-task-admission.

`TASK_ADMISSION_RESULTS.json` is the final canonical view, derived by the unchanged PR26 classifier and raw Issue/JUnit review. `SCREEN01_RAW_SUMMARY.json` preserves the original screening-adapter stop. `NORMALIZED_ADMISSION_VIEW.json` explains the exact correction without overwriting original Notebook records. `NATIVE_BASELINE_RESULTS.json` is raw-stage evidence, not a competing final admission decision.

Screened the first3of5prospective candidates, then stopped at the first2formally eligible:14297 and14459.13713 was rejected for declared-but-absent dirty-equals;14306 and14455 remainNOT_RUN. Original129-input hashes,canonical source-content/base/Issue/overlay aliases checked before baselines;no conflicts. No reference/gold patch inspected. All input sources,Issue,Snapshot,task/overlay hashes and original native counts/results are bound in `TASK_IDENTITY_LOCK.json` and `SELECTED_TASKS.json`.

The extra errors==0 check introduced by the screen adapter was stricter than the inherited rule.14459's two additional records exactly duplicate two snapshot call assertions during finalization, as already covered by the pinned PR26 parser/plugin. Original raw XML still contains8unique tests/2failures/2errors/10records,with0independent environment errors. The original screen STOP stays preserved. `normalize.py` reruns the frozen classifier on actual bytes; there is no manual eligible=true bypass. A mutation test proves independent teardown errors are rejected.

Production reuses PR29's Compiler/ADK/Runner/HTTP observer/chroot, original official six tools and native verify_task. `session.py` changes only admitted identities and uses the already-approved PR26 research reader; `worker.py` selects that same reader after the original official verification. Official tools/tests/Verifier,candidate ZIPs,Prompt/generation/budgets are unchanged. New GPU routes require a fresh grant. CPU transport is external to the production ZIP.

Three actual CPU Notebooks,allversion1COMPLETE:

| Purpose | ID | Outcome |
|---|---|---|
|Original screening|140412111|3screened;original conservative stop preserved;frozen-policy reconciliation admits first2eligible|
|Intermediate package|140415102|CPU engineering PASS;superseded after inherited future GPU completion-label regression|
|Final package|140415803|Full final payload CPU PASS;both real baselines and both owned scripted repair cycles|

The firstunexecutedcpu-e2e01build was moved to private evidence after the sealed builder refused overwriting it;zero SaveKernel. Each actual Notebook had one distinct durable dispatch. HTTP200 receipts initially entered strict UNKNOWN_STOP;independent readonly identity/source/version-bound collection confirmed existing resources,without resaving or overwriting events. PR27 Batch2 remainsUNKNOWN.

`CPU_END_TO_END_ACCEPTANCE.json` is the final release gate;`CPU_E2E02_ACCEPTANCE.json` is the explicitly superseded intermediate proof. `PAYLOAD_VERSION_HISTORY.json` preserves both executed payload hashes. Final actual result:SCRIPTED_ONLY,2owned sessions,14scripted HTTP requests,all6tools each,207-byte owned patches,explicit submits,native resolved=true,JUnit1passed each,chroot andcleanup complete. This is engineering evidence,not real Gemma performance. The two actual selected-task baselines remainnative resolved=false.

Reproduction (requires existing private raw archives; never redispatch):

```powershell
python -m u_re.v04.experiments.prospective_admission_01.audit <screen-archive> screen01
python -m u_re.v04.experiments.prospective_admission_01.normalize <screen-archive>
python -m u_re.v04.experiments.prospective_admission_01.acceptance <final-archive> cpu-e2e03
python -m unittest u_re.v04.experiments.prospective_admission_01.test_local -v
python -m u_re.v04.experiments.prospective_admission_01.release
```

No downloaded code is run by these offline auditors. Exact raw TaskResult/JUnit/patch/log content and per-member SHA/CRC indices remain private. Only safe source/hash metadata and derived results are public. Future GPU scope/dynamic gates are in `GPU_EXECUTION_PROPOSAL.md`;a new human authorization is still required.
