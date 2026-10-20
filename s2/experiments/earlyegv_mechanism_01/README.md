# S2-T500-EARLYEGV-MECHANISM-01

Independent authorized execution build based on PR7/fce198a, frozen candidate/CPU commit272c284.
This directory does not replace the original guarded draft or any candidate.

Prespecified runs: rich_3676 A→B; fastapi_14492 B→A. Exactly four Agent runs.
Both arms31BQATv2/4L4/TP4/context32768/safety1024/output16384/thinking4096/seed17,
shared500s/60 charged tools, command120s. Sampling/include_thoughts remain omitted.
A ZIP13968b67844d1041bfb79b9f11fc21ae66fb36aee5b00d3b91c526d5d35da329;
B ZIPd1e815e770abbcc448325ad2a3c8785c62f6d3c63bc7f95700850748c048a487.
Only Main Prompt differs. This jointly tests early delegation/investigation/closure,
not their separate contributions or a population repair-rate improvement.

## Execution identity and gates

- GPU_AUTHORIZATION.json records the user's explicit, conditional one-save/four-run grant.
- AUTHORIZED_PROTOCOL.json changes draft authorization/status/pending text and adds two
  execution-only source bindings; candidates, task identities/order, conditions, native
  Verifier, coordinator and worker are byte-identical to their frozen bindings.
- EXECUTION_BUILD_MANIFEST.json freezes authorized protocol, payload, Notebook and CLI
  serialized request-text hashes before save/inference. Candidate copies are in frozen_candidates/.
- preflight.py made read-only raw quota/submission/inventory checks.20 recent saved sessions
  are terminal; reservation is zero; no duplicate experiment Notebook. The SDK does not expose
  complete interactive inventory or instantaneous L4 stock. This is not an exhaustive absence claim.
- The single authorized SaveKernel request is final platform machine/account scheduling
  admission and explicitly requests NvidiaL4/10000s. It must return no input/configuration
  rejection. The status API does not echo an approved timeout; the accepted explicit request
  is the timeout contract, not an independent retrospective measurement of10000s.
- runtime_gate.py rejects preexisting compute processes, non4×L4 hardware, wrong pinned
  package versions, insufficient remaining full slots and an exposed timeout below10000.
  It then marks machine admission verified for the unchanged frozen coordinator.
- Notebook clock starts at container PID1 creation rather than installation completion;
  runtime evidence records this conservative origin. Original SessionWindow and per-arm
  budget logic are unchanged. Both clean baselines and complete model/wheel/task hashes
  must pass before model startup; request/schema/usage/context/idle gates precede tasks.
- launch_once.py durably marks its sole SaveKernel transmission and blocks an SDK automatic
  retransmission. An uncertain response is queried, never blindly resubmitted.

The original135 official Linux tests are retained frozen evidence, not rerun claims.
PRELAUNCH_TESTS.log contains9 new-build/original-guard local tests; all passed without GPU.
Two initial Python parenthesis syntax errors in new preflight/build scaffolding were fixed
before either module's work began; no candidate, frozen source or GPU execution was involved.

## Stops and interpretation

Hash/model/input/configuration drift, native baseline faults, leakage, child production
writes/ambiguous delegation, unexplained HTTP terminal, missing/conflicting JUnit,
workspace/process cleanup/server-idle failure or insufficient full remaining resources
stop the whole study. Preserve completed outcomes, unknown and not_run; no retries,
task replacement, hotfixes, extra runs, formal submission or LoRA.
Ordinary attributable assertion/syntax failures, absent EGV/submit and500s Agent cutoff
remain algorithm observations and do not stop the paired next arm.

Primary endpoint is original official resolved. Mechanism requires actual EGV assertion,
actionable counterevidence, delivery, Main production correction and a successful
discriminating retest. Report text/call counts alone are insufficient; zero denominator
means null. Received-only usage remains null/partial on missing responses.

Full native Trace/Patch/TaskResult/Phase2/JUnit, tool/HTTP/AgentTool records, server-idle
and cleanup evidence will be collected unmodified after this single saved Notebook.
Until actual outputs are collected all task outcomes are not_run, not failures.
This research does not produce a Kaggle Public Score or establish general superiority.
