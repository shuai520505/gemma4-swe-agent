# GPU02 result: GPU_BLOCKED_BY_RUNTIME

## Actual authorized GPU attempt

PR22 was checked before execution and during recovery:Draft/open/unmerged,head5598178f4dbf3fdae543ae41e8328f70c0b2b908. This branch is based on that exact commit. GPU02 build source commit3500eb8e686ccd165b0cef09937ad0cd0d79b17a.

Exactly one GPU SaveKernel was sent: `wudangdexiaodoashi/gemma4-u-re-actionfirst-abba02`,Notebook140233779/v1. HTTP200JSON returned ID/version. The controller preserved UNKNOWN_STOP because the returned `/code/owner/slug` ref failed its immediate strict match. Independent read-only recovery confirmed owner/ref/slug,private status,GPU configuration,version1,semantic Notebook content and exact embedded payload. Latest remained1 before/after output download. Platform result:ERROR. No original acceptance event was fabricated or rewritten.

Actual hardware:four NVIDIA L4,23659151360bytes each;CUDA12.8,torch2.10.0+cu128,vLLM0.19.1. Eight frozen model/tokenizer/template file hashes and both task/snapshot identities matched. GPU chroot canary completed with access-denial checks and cleanup. Evidence:GPU_EXECUTION_RECORD.json and safe_evidence/results/.

The trusted baseline lazy import failed before baseline workspace execution and before vLLM startup: `ModuleNotFoundError: u_re.v01.experiments.fastapi_pilot_01`. Every declared source pin was packed correctly;those pins did not cover the complete runtime import chain. This is our packaging/acceptance gap,not a candidate failure.

|Run|Task|Candidate|Status|Native resolved|
|---|---|---|---|---|
|1|fastapi_9425|NoEGV|NOT_RUN|null|
|2|fastapi_9425|Action-First|NOT_RUN|null|
|3|fastapi_14786|Action-First|NOT_RUN|null|
|4|fastapi_14786|NoEGV|NOT_RUN|null|

Real Gemma requests0;real SWE Agent sessions0. vLLM/model load was NOT_REACHED. No real-run patch,first edit,submit,tool usage,token usage or JUnit exists;per-run fields remain null/NOT_RUN. ABBA_RESULTS.json,AGENT_BEHAVIOR_METRICS.json and NATIVE_VERIFIER_RESULTS.json preserve this distinction. Neither candidate has an algorithm outcome from GPU02.

## Resource evidence

Requested/accepted platform timeout10000s;no independent effective-window API field is available. Code elapsed326.393255797s,not independently billed GPU duration. Initial account remaining82709.410 report seconds;fresh post-GPU02 remaining82016.632,0reserved (QUOTA_AFTER.json). Delta692.778 is account-level consumption,not an independently attributed Notebook invoice. Model server was never started;SERVER_CLEANUP confirmed=false means no known server PID/idle confirmation,not evidence of an escaped model process. Isolated canary sandbox cleanup did complete.

## Authorized CPU engineering repairs

1. **140236395/v1 ERROR**. Source commit5562ecd74f8a65a73fb4b5c7d3eca1727d3d4e40. AST import closure included lazy function imports and transitive local helpers. The unchanged native baseline function actually ran both frozen tasks:9425 tests1/failures1/errors0;14786 tests9/failures2/errors0 (7passed). Source provenance,unchanged source at pytest boundaries and cleanup passed. It then exposed a second defect:observe_http created `agent/` before agent_phase.run's exclusive mkdir. No synthetic Agent began. Original ERROR and log remain under repair_cpu01/.

2. **140237627/v1 COMPLETE**. Source commit03d5bb0f7e4e4ac73d2c5fe5266409d99fcab293. runtime_worker.py calls the unchanged production worker and directs its passive HTTP observer to a sibling trusted directory,then relocates exact event bytes after Agent completion. No tool,Runner,Verifier,Prompt,budget or submission semantic changes. Actual official Compiler/ADK/chroot worker ran an owned synthetic project with scripted local HTTP replies. Five tool interactions (get_status,read_file,edit_file,run_command,submit_patch),three officially charged calls,six model-boundary HTTP exchanges,207-byte patch,explicit submit,native TaskResult resolved=true,JUnit1passed,source-change observations,HTTPterminal audit and full cleanup passed. Six schemas were registered;write_file was not exercised in this repair probe. No real baseline was repeated in repair02.

Both CPU Notebooks were GPU=false,TPU=false,Internet=false,model_sources=[] with zero Gemma requests. Synthetic reply token counts are fixture values,not empirical model cost. The original generic worker runtime_config contains real_model=true;separate CPU acceptance/transport identity explicitly records SCRIPTED_ONLY and prevents treating that flag as real-model evidence. CPU_PRODUCTION_WORKER_REPAIR_PASS does not imply GPU/algorithm validation.

Local regression suite22PASS. An initial unsent CPU build had missing HERE;fixed before dispatch,unsent build preserved. An offline extraction assertion initially sought source observations in the coordinator journal;actual records were in the Agent manager journal. The analysis path was corrected without changing raw execution evidence. Network/SSL recovery errors remain in read_observations;using the existing local proxy recovered the same completed CPU version without rerun.

## Integrity and publication

Original NoEGV,Action-First and Full ZIP/member SHA remain unchanged. Historical tracked changes outside this new directory are empty. Frozen task selection,ABBA order,300seconds/60charged/120command,generation and official source pins remain unchanged. Private raw GPU/CPU archives are CRC-valid and SHA-bound in RAW_ARCHIVES.json. Public extracts contain owned synthetic evidence or safe derived metadata;no competition evaluator overlay,reference repair,credential or signed URL is added. INTEGRITY_MANIFEST.json records the checks and source/payload hashes.

## Decision

The sole GPU02 allowance is consumed. Totals:this task sent1GPU Notebook save/run and2versioned CPU-only save/runs;0real Gemma requests,0real SWE Agent runs,1owned scripted synthetic Agent run,2native baseline rechecks,0formal Competition Submissions. GPU01 remains ERROR;GPU02 remains ERROR;CPU repair01 remains ERROR.

The two CPU-discoverable defects now have actual passing entrypoint evidence. A future GPU build must combine complete import closure and passive observer fix,exclude CPU scripted transport from its model route,and freeze/recheck its payload. Real vLLM startup and Gemma requests remain unvalidated for U-RE. NEXT_GPU_AUTHORIZATION_PROPOSAL.md specifies the unchanged four-session scope and fresh dynamic gates. Another GPU retry needs separate explicit authorization;no GPU03 was saved or run. No Action-First or EGV efficacy claim is possible.
