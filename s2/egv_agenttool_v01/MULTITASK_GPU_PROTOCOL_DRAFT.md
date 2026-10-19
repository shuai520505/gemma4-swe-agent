# Eight-task paired architecture experiment — frozen draft

Experiment: S2-EGV-AGENTTOOL-MULTITASK-01. **DRAFT_NOT_AUTHORIZED. No GPU dispatched.** Machine-readable protocol: [MULTITASK_GPU_PROTOCOL_DRAFT.json](MULTITASK_GPU_PROTOCOL_DRAFT.json), SHA256 `344682a8c8e1ace10665ad317bd26111070c675154f931fbb7aa9c9552a4a483`. Both guarded Notebook hashes/payload are in [GPU_DRAFT_FREEZE.json](GPU_DRAFT_FREEZE.json). This draft is not execution authorization. Future authorization requires a newly sealed authorized build, not editing this frozen artifact in place.

## Hypotheses and treatment

H1: EGV discovers useful evidence omitted by the single Agent. H2: delivered executable counterevidence changes Main's production repair and a real retest eliminates that counterexample. H3: the complete architecture improves official resolved or comparable-correctness cost under the same total allowance. CPU mocks establish none of these hypotheses for Gemma.

A is frozen S1-EGV V0.1, ZIP `cefadd019ec64d9d06cbde72e0d0507796e8af9a370dd2358059e211845135e9`. B is S2-EGV-AgentTool V0.1, ZIP `1f9345cc11362acfc19fbede48284aa934dfbe3a36fe0aa889134125fa8de807`. Architecture, prompt responsibility, exposed schemas and conversation handling differ: this is a complete-architecture comparison, not an isolated causal test of Agent count. No LoRA or outside inference backend.

Both use Gemma4 31B QAT version2,4 L4/TP4,context32768,safety1024,output16384,thinking4096,seed17. Sampling/include_thoughts remain omitted. One native300s Agent allowance and60 organizer-counted tools total,120s command. Status/submit/AgentTool wrappers are free under actual SDK accounting, not extra charged allowance. Child has no separate hard deadline; the enclosing deadline applies. Both arms use exactly the same observer, worker, v3 Verifier classification and context admission. Child Runner does not inherit native App compaction automatically; this is a measured architecture characteristic, not a hidden budget change.

## Frozen tasks and order

The24-task pool and selection rule were registered before native environment outcomes. All24 were checked without a model or reference repair. Select first8 eligible under the fixed order, at most4 per repository. See [TASK_SELECTION_AUDIT.md](TASK_SELECTION_AUDIT.md). No task replacement after GPU starts, including for environment failure.

| Pair | Task | Order | Batch | Clean baseline tests / failures / errors / skipped |
|---|---|---|---|---|
| 1 | rich_3043 | AB | 1 | 96 / 3 / 0 / 0 |
| 2 | fastapi_9753 | BA | 1 | 12 / 5 / 0 / 0 |
| 3 | requests_7205 | BA | 1 | 219 / 1 / 0 / 13 |
| 4 | rich_3935 | AB | 1 | 22 / 2 / 0 / 0 |
| 5 | rich_3064 | AB | 2 | 4 / 3 / 0 / 0 |
| 6 | rich_3882 | BA | 2 | 8 / 1 / 0 / 0 |
| 7 | fastapi_14986 | BA | 2 | 7 / 5 / 0 / 0 |
| 8 | requests_6644 | AB | 2 | 1 / 1 / 0 / 0 |

Base commits, exact Issue/task-record/test-overlay/snapshot hashes are in task_inputs; all model files,41 model wheels,124 task wheels, runtime sources and candidate members are pinned in JSON. No reference repair was used. The model receives original Issue and its own clean task repository through official tools, not admission JUnit, first-arm outputs, traces, hashes of reference answers or analyst reports.

Each arm starts a fresh native Agent session, workspace and Phase2 sandbox. A fresh host baseline is checked again before inference. Batch2 receives only the batch1 hash/integrity receipt, not its answers, and requires four complete pairs. batch_receipt.py checks canonical ZIP manifests, model/wheels/cleanup and all8 run identities. Do not concatenate old Pilot/S1 trajectories into this experiment.

## Admission, resource window and stop

Current technical CPU acceptance: CPU05 original115+new6 methods; budget01 actual300s/60 boundary; env01 exact worker observer route and24 native baselines. These separate preparations have explicitly different source manifests; env01 used CPU04 logging, CPU05/budget01 test final Git-boundary logger. Candidate and evaluator bytes are identical. GPU coordinator/source is prepared and statically checked, not already proven on GPU.

Remaining gates: explicit human GPU authorization; actual available Kaggle quota/window; new authorized protocol/Notebook seal; same model/wheel/source hashes; real model generation/route/tokenizer/usage and child schemas; context guard; fresh host baselines; backend idle/process cleanup. Budget and reserve calculations are in COST_MODEL.md. Four-hour per-batch window includes setup origin; reject startup/task admission if the conservative remainder does not fit. No quota was observed, so resource admission is currently pending.

Global STOP: identity/config drift; answer leakage; unexplained request terminal; missing or conflicting native Phase2/JUnit; unassigned environment fault; child workspace write; concurrent/ambiguous delegation accounting; sandbox/process cleanup failure; unconfirmed server idle/reclamation or insufficient global time. Preserve completed observations; unlaunched arms=not_run, unresolved environment/integrity=unknown. Do not hotfix/rerun/reselect in the frozen experiment.

An ordinary assertion failure or attributable Agent syntax/import regression remains official failure and does not stop the second arm when evidence/cleanup gates pass. Explain actual deadline cancellation by request_id and time; absent usage stays null/partial. Client cancellation alone does not prove server abort. Require registered idle metrics and retain backend logs; no invented request-specific abort acknowledgment. A child interrupted at deadline retains its incomplete delegation rather than a fabricated return.

## Endpoints and independent audit

Primary endpoint is unchanged official resolved, with native TaskResult/Phase2 stdout/stderr/JUnit and test_exit_code. Report A-only/B-only/both/neither on complete comparable pairs. unknown/not_run are never confirmed failure. analyze.py withholds full RR unless all8 pairs are auditable; small selected-task uncertainty remains even if complete. Tool events within a task are not independent samples.

For each arm inspect real tool calls, diff and execution paths: earliest correct location/edit, meaningful and redundant reads, invalid/repeated probes, target assertion provenance, old-behavior coverage/regressions, delivered/actionable counterevidence, Main response, real retest outcome, explicit submit vs fallback, diagnostic leftovers, final Patch validity. Grade Level1/2/3/unknown with immutable tool-record pointers. Text reports/exit0/import alone do not establish behavior. Closed-loop rate requires real Main production edit and successful discriminating retest; no-counterexample denominators=null.

Record role-specific model calls, all HTTP dispatches including compaction, raw vs counted tools, delegation time/return, received-only token usage, main/worker/Verifier times, observed platform duration×device count, first valid/final Patch and explicit submission. Audit all Main and child request semantics, including the last cancelled request. STOP on observer gaps that prevent attribution.

No public-task Agent result exists yet. [GPU_RESULTS_NOT_RUN.json](GPU_RESULTS_NOT_RUN.json) explicitly lists all16 arms as not_run, with full success rates=null. Results may support a later confirmation only if multiple real closed loops coexist with no material old-behavior/submission loss and a useful resolved or cost signal. Failure to close, frequent ignored feedback, child writes, budget exhaustion or higher cost without repair gain argues No-Go for this candidate.

## Artifacts and future execution

notebooks/gpu-batch1-draft/study.ipynb and batch2 equivalent are complete payload/install/coordinator drafts, but intentionally raise before installation/startup. They were not pushed. Do not remove the guard casually: register an authorized new build after quota and approval, preserve this draft, then push only that new artifact. Batch2 authorization requires a verified batch1 receipt. All original CPU failures, raw ZIPs and prior S1 evidence remain immutable.
