# U-RE V02b real Gemma replication

Execution experiment: `U-RE-V02B-REAL-GEMMA-REPLICATION`.
Base: actual open/unmerged PR26,def9c7a46c95a852f48feeafeb7017a00fb8a489.

This directory records the newly authorized two GPU batches. The accepted
shared production ZIP remains in env_recovery_admission_01/production and has
SHA256815d51b0528934283823c7469f42503fb6f388fc406c9e0870a46276be398e63.
Original preparation authorization=false and every historical record are intact.
GPU_AUTHORIZATION_RECORD.json supplies independent current human authorization;
its execution_experiment_id names this study, while experiment_id binds the
existing preparation lock required by the unchanged production adapter.

Batch1:5077 A→B,11355 B→A. Batch2:14463 A→B,9555 B→A.
Each batch permits one private4×L4 TP4 Notebook,10000s maximum window and4
Sessions. Every Session retains Gemma4 31B QATv2,300s/60tools/120s command,
original context/generation settings and an independent chroot/Agent context.
No Full arm, GPU retry, Prompt change, new task or Competition Submission.

`notebook.py` reuses GPU03's builder, durable dispatch and GPU-aware read-only
collector. It verifies the exact original CPU archive before each dispatch,
checks fresh quota/model input/slug, and passes the external authorization and
batch number to the unchanged shared production entry. An initial read used a
CPU-only metadata predicate and conservatively stopped despite matching source;
the corrected GPU-aware collector retains that partial observation and performs
independent source/version/model checks. No second save was sent.

`results.py` is analysis-only. Native Resolved and Context Guard are independent
fields. Guard events come from Worker/events.jsonl; source/tool events from
Agent/events.jsonl share the host monotonic clock. First source edit is an
observed filesystem-change interval, not a model intention. First applicable
production patch is its first observed trusted native application, often after
Agent termination; earlier candidate checkpoints are not silently assumed valid.
Local assertion evidence needs private Issue relation review. Printed diagnostics
are not passing assertions. Repeat metrics use command+production hash+observed
test/script epoch and are conservative proxies. Unknown usage stays unknown;
observed received tokens, including failures, are separated from unobserved
cancelled usage. Account quota differences are not individual Notebook bills.

Raw task/evaluator content, patches and model/tool traces remain outside Git.
Public JSON files contain derived metrics, identities, source hashes and redacted
errors. Failed local analysis tests are retained alongside their corrected pass.
Historical GPU03 data are used only as a separate descriptive cohort and for
offline parser regression checks, never as new Agent input.

Final observed state: **V02B_REAL_GEMMA_REPLICATION_PARTIAL**. Batch1
140361137/v1 COMPLETE produced4 genuine Sessions,89 successful model responses
and native A0/2,B0/2. All4 hit Context Guard. Batch2's unique SaveKernel returned
empty499; owner/source identity and actual execution remain unknown after bounded
read-only checks. Runs5–8 are null/UNKNOWN_UNOBSERVED, not failures or proven
not-run. FINAL_DECISION.md contains complete Q1–Q20, costs and limitations.
