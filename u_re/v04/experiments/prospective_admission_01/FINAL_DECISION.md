# Final decision — V04_EGR_GPU_READY

The new prospective cohort has two formally admitted tasks and the exact final production ZIP has passed real Kaggle CPU engineering acceptance. This is readiness to request a new GPU authorization, not an existing GPU authorization or evidence of EGR efficacy.

Source: actual PR29HEAD a44cc483a6c114940a65322371dfa87ea5d9dd5e,open/unmerged;branch feat/u-re-v04-egr-task-admission. All changes are inside the new prospective study. Historical PR24–29 results and original candidates are unchanged.

## Actual native screening and correction

|Frozen rank|Task|Original native result|Final admission|
|---|---|---|---|
|1|fastapi_13713|0failures,1collection error;dirty_equals absent|ENVIRONMENT_BLOCKED;reject/continue|
|2|fastapi_14297|14tests,11passed,3test-call failures,0errors|BASELINE_ELIGIBLE,T1|
|3|fastapi_14459|8unique tests,6passed,2snapshot call failures,2paired teardown entries (10JUnitrecords)|BASELINE_ELIGIBLE,T2;0independent environment errors|
|4|fastapi_14306|NOT_RUN|null;first2eligible reached|
|5|fastapi_14455|NOT_RUN|null;first2eligible reached|

The original screen01 adapter incorrectly imposed raw JUnit errors==0 in addition to the frozen rule. It stopped14459asUNKNOWN. This initial stop is preserved in the original raw archive,public SCREEN01_RAW_SUMMARY.json,commit history and normalization source hashes. No native result is relabeled PASS.

The inherited PR26 policy already admits exact same-test inline-snapshot call/finalizer duplicates when an original target assertion fails and no independent environment error exists. Re-running that unchanged classifier on raw screen01evidence returnseligible for14459. The unchanged frozen parser proves two exact pairs,valid unique suite aggregates and the pinned0.21.1plugin source. A mutation test substitutes an independent teardown error and is rejected. Thus this is correction of an overly strict new adapter,not post-hoc relaxation of the frozen admission protocol. Counts remain2failures/2errors;native resolved remainsfalse. Canonical TASK_ADMISSION_RESULTS.json and SELECTED_TASKS.json contain the final derived state;NORMALIZED_ADMISSION_VIEW.json preserves the raw-versus-derived explanation.

13713's external dependency absence is established by original frozen test dependency declaration,real sandbox traceback and installed-distribution probe. It is unrelated to its requested metadata behavior. No dirty-equals artifact was installed,environment changed or test removed to admit it.14297's runtime call failures match the normal Issue's optional-sequence serialization exception.14459's failing schema assertions match the normal Issue's inherited security metadata contract. Private raw test bodies are not reproduced here or supplied to Agent.

All129original records/snapshots were hashed against the previously approved identities before any baseline. Candidates were compared against historical records and one another by repository+Issue,base commit,archive bytes,canonical source tree excluding.git/header/root-prefix noise,and normalized changed test content. No conflicts found. Canonical hashes supplement,not replace,original byte hashes. No reference/gold patch was viewed.

## Actual CPU acceptance

|Notebook|Version|Platform|Meaning|
|---|---|---|---|
|140412111|1|COMPLETE|Original3-task screening;raw stop and later frozen-rule reconciliation retained|
|140415102|1|COMPLETE|Intermediate full production CPU pass;superseded after local regression found inherited future GPU completion label|
|140415803|1|COMPLETE|Final exact production ZIP CPU end-to-end PASS|

The final payload contains the corrected completion label and was actually reaccepted;the intermediate pass is not used as a substitute. Original Notebook versions were never edited or rerun. There was also an unexecuted draft build(cpu-e2e01)preserved privately after the immutable builder refused overwriting;it consumed0SaveKernel and is excluded from actual Notebook totals.

Final140415803executes ZIP→Extract→production entry→official Compiler/ADK/LlmAgent/Runner→chroot→all6tools→source edit→targeted assertion→207-byte owned patch→explicit submit→original native verify_task→TaskResult/JUnit→cleanup for both candidates. Each owned scripted run hasresolved=true andJUnit1passed. There are14actual SCRIPTED_ONLY HTTP requests. Two real selected-task empty-patch baselines are also rerun from this final payload and reproduce their original native counts/verdicts. The trustworthy dependency fingerprint,source provenance,isolation canary andcleanup pass. Every returned production member hash matches the exact frozen ZIP.

Actual compiled instructions differ with expected hashes,while actual tool-schema SHA and generation/budget config are identical. Control instructionSHA405a0bb38523c26ac8350660cceff17a6e5bd5a5e07dd7065f9e84d31ae2e9bc;treatment b1dceeca98db3353d1f0055c7ddd26be9fdcde61a57f0dc22f43f0e9aed0a7e0. Tool-schema SHA f7766602e623aa4b163e56e3543855b242da81e757d2761865394c28a92e56b4. Both actual outgoing HTTP routes use16384max output,4096thinking,seed17. Time/tool/command budgets300/60/120 remainunchanged,context32768/safety1024/input15360.8192wasnotused.

CPU_MODEL=SCRIPTED_ONLY. These are engineering fixtures,not repairs of14297/14459byGemma andnot EGR performance evidence. The new official worker/Verifier operations are unchanged;only trusted post-result interpretation is routed to the already-frozen PR26 reader. Both candidates use that exact same reader/environment.

## Final immutable bindings

- Final production ZIP SHA256: `77f7a16721eecb3bbcdf9736670b25cc73735ab7258500b965db66f81fb722f4`.
- Final raw CPU ZIP SHA256: `ffcdb21f02078919a4318151c40e4654643249c3c280f411111e5a8ff96138b8`;1518934bytes,CRCvalid.
- Final raw private path: `D:\kaggle\Gemma 4 Developer Agent Competition\private-evidence\u_re_v04_prospective_cpu_e2e03\read-02\evidence_confirmed\output\v04adm-cpu-e2e03.zip`.
- ABBA lock SHA256: `c5d222ab4b2fd01a7964018e2db4bee7030d22245312c2d6d4de7bb218be5ae1`.
- Selected-task lock SHA256: `bfd87a222b4a4a2da2aa7b5e993b759568aca5f01d2459521281ff4963e7b46a`.
- Environment-lock SHA256: `452c0d9afdf7c21edcd43a6a67e69cca6c67aba640eb526f50aa9835169dc7d9`.
- A frozen Action-First ZIP SHA256: `70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8`.
- B frozen EGR ZIP SHA256: `07263740c5ee22bf6611d7fa31dafbc84d7fb50288d22355b9201cd6954a6840`.

### T1 — fastapi_14297

- repo: `fastapi/fastapi`.
- base_commit: `3c54a8f07b70cdd40e3d81ea319e9fcccd2481d2`.
- issue_sha256: `55c911d665e9b00a79f5db7c5a1bb75ded6307f7719b061ef0799bacd0b6fdd5`.
- task_record_sha256: `1cbdd75c49273a52ad9efe1a3baaba1cb89fdaf724978c48826ef18a83fd9ad2`.
- test_patch_sha256: `2adf1618a39794512e39fca96825c2a2c418c821dfbbb4f937a56c83cf0c35bb`.
- snapshot_tree_sha256: `859b6015a982412e97c965bf1a6539c05d8824907c741469b7ef0014cf556a97`.
- test_overlay_content_sha256: `423eeacbb07308e6bf6c73ea5a50fb71f7229abf89a47d8e9f8dcd3fe739de11`.
- TaskResult_sha256: `4f9b0994653d61a4d59858f6e920c7089f3230e48f3b1b720f6ef083ab853552`.
- JUnit_sha256: `3b38edc013c67eef69b8e670cf68da8f7cd0f04c43242a232aeaaa1fc818583f`.
- Original Snapshot `snapshots/fastapi_14297.tgz` SHA256: `faf251417cee0c2119c8dcaed978ca394abd35bd6c719ca9be175ed49688a595`.

Source for initial admission:CPU140412111/v1,with two later same-input native rechecks. Original input byte identities stay fixed;JUnit/TaskResult file hashes legitimately differ between rechecks because paths/timing change. All raw hashes are separately retained.

### T2 — fastapi_14459

- repo: `fastapi/fastapi`.
- base_commit: `eb1d50479ba0ac873e4ffa08a824b1d822ca3a17`.
- issue_sha256: `204aee6b1a8978fc1b0ce5777b3b116c45cea82d4b6822c5667724ccb6d62960`.
- task_record_sha256: `b80d8e35667e2666dff3bc5103cf596adc4cd3978d7255edefdd650f533aeccf`.
- test_patch_sha256: `14eb9bf24bbc787b7810a9ca25a84f40af00217d80c0ef7304363c29e154b315`.
- snapshot_tree_sha256: `07da4c7a349655412e41bb69e00759749fbc2ef8933d98354f99be35ca0582f0`.
- test_overlay_content_sha256: `199140d7e4b9e209a837ef2ced339ab7fc61b353e63b0867fd35f7a1cd4c3035`.
- TaskResult_sha256: `8fb7c7a4fe2b123945c57be57af85d3cb690ccb7aefe85160aab67880c803038`.
- JUnit_sha256: `46da3f46ccb028b56767e31250a61efb25f060b43e3c3ae0a6fc9f5ca449cf21`.
- Original Snapshot `snapshots/fastapi_14459.tgz` SHA256: `4c86d13f13ce750207fbeb2c8c9434cf106b64547c33621d89aebf1e88ba0aa1`.

Source for initial admission:CPU140412111/v1,with two later same-input native rechecks. Original input byte identities stay fixed;JUnit/TaskResult file hashes legitimately differ between rechecks because paths/timing change. All raw hashes are separately retained.

## Required Q1–Q18

1. **Screened count:**3different prospective tasks,never more than5;4additional native rechecks across2CPU engineering runs are not new task screening. Total7native verify_task baseline invocations;no candidate model repair on these tasks.
2. **Per-task results:**the table above preserves13713dependency collection failure,14297's3call failures and14459's2target assertions plus2paired snapshot-finalizer records.14306/14455remainNOT_RUN.
3. **Identity/aliases:**none detected after all129byte identities,metadata and canonical content checks. Unknown/conflicting identities would stop before baselines.
4. **Errors:**13713hasmissingdeclared dirty-equals.14459hasexplained paired snapshot-finalizer records,not independent environment failure. The screen adapter and offline flat-case-count reader initially mishandled those existing frozen semantics;both original failures are retained. No official Verifier was changed.
5. **Two admitted:**yes,under the existing frozen classifier and raw Issue/native review,not a hand-written eligible flag.
6. **Selected:**T1fastapi_14297,T2fastapi_14459because they are the first2eligible after13713'spermitted environment rejection.
7. **Order:**exact original13713→14297→14459;stop after confirming first2eligible. No check of14306/14455or outcome/difficulty-based replacement.
8. **Issue relation:**verified from original normal Issue,actual failing call/assertions and immutable source provenance;detailed raw evidence stays private. The runtime exception in14297occursduringtestcalls,notcollection.
9. **Candidates unchanged:**Action-First70af6921… andEGR07263740…match exact ZIP/member hashes. OriginalNoEGV/Full and all historical tracked files are also preserved.
10. **Conditions equal:**same Gemma31BQATv2,singleAgent,sixschemas,generation and300s/60tools/120s limits,context32768/output16384. CurrentCPUdoesnotproveweightloading;futureGPUmustrecheckeightmodel/tokenizer/templatehashes.
11. **ABBA:**14297A→B,14459B→A;all exact task/candidate/environment identities frozen inABBA_EXPERIMENT_LOCK.json. Agent histories/workspaces/chroots/logs/native evaluations remainseparate.
12. **Final real CPU acceptance:**yes,140415803/v1,fromactualpackagedZIP. It coversbothactualnegativebaselines,actualCompilerinstructions,modelwireconfig,toolschemas,ownedrepair+submit,TaskResult/JUnit,HTTPobservability,isolationandcleanup.
13. **Actual Notebooks:**140412111/v1,140415102/v1,140415803/v1;allCOMPLETE. EachhadoneCPUdispatchonly. OriginalstrictUNKNOWN_STOPeventsremain;independentreadonlyowner/ref/source/versionconfirmationanddownloadbindtheresults. NorepeatSaveKernel.
14. **Final ZIP:**77f7a16721eecb3bbcdf9736670b25cc73735ab7258500b965db66f81fb722f4.
15. **Verifier/history changes:**none to official verification/scoring/test bytes,original ZIPs orPR24–29results. PR26'salreadyapprovedresearchresultparserisreused;itsbehaviorisnotanewexperimentalA/Bfactor. PR27Batch2remainsUNKNOWN.
16. **GPU engineering readiness:**yes,readytorequestoneindependent4L4/TP4/foursession/10000sgrantboundtothisfinalpayload/tasks/model/environment. GPUaccess/quota/weights/runtime/windowandactive-conflictchecksremainRUNTIME_RECHECK_REQUIRED,notpresumedavailable.
17. **Real Gemma benefit:**none observed this round;0Gemma requests/0GPU sessions. Synthetic resolved=true provesengineeringonly. Both real tasks have native resolved=false empty baselines,not Agent failures.
18. **Formal replacement:**no. Obtain a matching GPU authorization,run both fixed candidates without hotfixes,then judge Native Resolved and costs. Do not infer Public Score,significance orcross-repositorygeneralizationfromtwotasks.

## Resource and safety accounting

Actual current task:3CPU Notebooks/3SaveKernel dispatches,7empty-patch native baselines(3new+4rechecks),4owned scripted sessions/28scripted HTTP requests across the two engineering payloads,0GPU/0realGemma/0CompetitionSubmissions. No known-state SaveKernel was resent. CPU billed resource consumption is NOT_OBSERVABLE here,not0;account quota deltas would not be a per-Notebook bill. Candidate weights were not loaded. Original PR27Batch2unknownisnotreclassifiedandretrypermissionisnotinferred.

Full raw logs,tests,Issue bodies,TaskResults,JUnit,patches and model messages remain under private-evidence. Public files contain approved sources,hashes,counts and safe derived contract summaries. Release checks scan decoded Notebook/payload bytes for known secrets,full evaluator overlays,signed URLs and raw evidence filenames;this is bounded publication checking plus boundary/role review,not a universal leakage proof.

Legacy BUILD.selection_protocol_sha256 refers to the reused original CPU interface gate;prospective pool/admission and real task-order bindings are the separately pinned ADMISSION_PROTOCOL_LOCK and ABBA_EXPERIMENT_LOCK. Future GPU authorization must use the new exact task lock,payload,environment and model bindings,not interpret that legacy field as a fresh task selection authority.
