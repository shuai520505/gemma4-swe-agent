# EGRD V0.3.2 final decision

**EGRD_V032_NEITHER_REPAIRS** — the primary submitted-and-verified repair endpoint is false in
both arms. Two real-Gemma Agent sessions were executed; the platform Notebook is
COMPLETE, but neither Agent completed successfully or submitted a patch.

| Required question | Actual answer |
|---|---|
| Notebook/version |[141100028/v1](https://www.kaggle.com/code/wudangdexiaodoashi/egrd-v032-real-gemma-evidence-ab); private, COMPLETE|
| Dispatches/attempts |One SaveKernel, HTTP200; A then B once each; no extra inference probe|
| GPU allocation |4×NVIDIA L4, each23,659,151,360 bytes; TP4|
| Model loaded |Yes; immutable Kaggle instance version2; all eight asset hashes matched before load|
| Model revision |google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2; no upstream HF commit invented|
| Tokenizer/template |Exact observed SHA256s in MODEL_IDENTITY.json; tokenizercc8d3a0c…, template94899c0f…|
| Runtime |vLLM0.19.1; Torch2.10.0+cu128; CUDA12.8; Python3.12.13; driver580.178.04|
| SDK |swegemma0.2.11, adk-submission0.2.13, google-adk1.36.1; both actual Compilers passed|
| Generation |context32768; output16384; thinking4096/enabled; no request seed; engine log resolves default seed0|
| Common serving |prefix caching disabled, no LoRA, no history filtering/compaction or research Guard|
| S0 bytes |Unchanged3303d6e1dd246d3861910701beb580c8d9a165ea1eb1c1a13d8c8ba9d6efd4f9|
| Actual input comparison |Only original frozen B supplement differs; identical instructions/tools/config/roles; receipt exactly once|
| Initial actual tokens |A3430; B4108; +678, measured by serving /tokenize and confirmed by first response usage|
| A ended |300.008s native deadline;20 charged tools; late production edit at291.116s|
| B ended |277.611s native serving HTTP400;20 charged tools; no production edit|
| Patches submitted |A=false; B=false; both submitted-patch hashes null|
| Production edits |A django/contrib/auth/forms.py; B none; B did successfully edit Agent-visible tests|
| Post-edit target/controls/regression |NOT_RUN for fallbacks; null. Owned baseline checks did run and failed target1→0, passed3 controls/regression|
| Costs |44 HTTP attempts;42 HTTP200;1 HTTP400;1 canceled in flight;444878 known received tokens, incomplete usage|
| Startup |295.364s model load; first-cell-to-final-coordinator-record1292.657s; exact billing unavailable|
| Evidence used by B |Receipt exposure verified; causal use and useful production impact not established|
| Hypothesis result |No demonstrated benefit on this one exposed task; no generalization or score inference|
| Next action |Repair test-execution prerequisites/entry-point decisions; separately test retained fallback before judging its correctness|

Raw archive `67386d9aa82f93612250b2d84dbf26f5bd2a7a82a5494d2ec2fe3bcc2bb74114`:39,610,066 bytes, CRC plus all421 evidence files and
sealed source members verified. Full requests/responses, reasoning, tool results,
test bodies and patches remain private. Per-arm workers/chroots/histories and
trusted contexts were independent; leases, owned processes, workspaces and model
server cleanup passed. Boundary failures were not hidden. Generic supervisor
`official_result_missing` remains UNKNOWN because official benchmark TaskResult
is intentionally absent from this external development study; it is not a Native
Resolved=false. Native per-session traces are present privately.

Missing pytest, distutils, django-admin and proper settings/labels impeded
Agent-created tests. The minimal pinned Django environment supports the owned
probe and bounded regression, not an entire canonical Django/SWE-bench suite.
This is a material experimental limitation, not a claimed model-only failure.
Historical S0 formal-serving equivalence remains UNVERIFIED. The shared engine
default seed0 is observed, not retroactively asserted as historical S0 seed.

**Official Native Resolved: NOT_EVALUATED (null). Canonical SWE-bench resolved:
NOT_EVALUATED (null). Formal competition submission: NOT_RUN.** No candidate or
formal leaderboard submission changed. No further Notebook or real-model run
is authorized by completion of this two-session study.
