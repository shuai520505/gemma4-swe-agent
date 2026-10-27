# EGRD V0.3.2 final decision

**EGRD_V032_GPU_ENVIRONMENT_BLOCKED**

At 2026-10-27T04:40:47.541242+00:00, the final read-only preflight returned
`static_read_GO=false`, `conflict_gate=false`. The existing GPU Notebook
`wudangdexiaodoashi/the-boys-i-am-better` was QUEUED. Its separate
`the-boys-i-am-better-23d8c6` entry returned HTTP 404 for execution status;
metadata identifies it as GPU-enabled, not proven inactive. A third entry
reported CANCEL_ACKNOWLEDGED; this was not rewritten as completed. No other
Notebook was canceled, edited or redispatched.

Quota was 105730.256 report seconds remaining, reserved
0, exceeding the conservative 41,200-second planning floor. This does not prove
accelerator allocation or remove the conflict. The earlier clean preflight is
archived; it was superseded by the mandatory fresh check.

| Required question | Observed answer |
|---|---|
| Actual GPU Notebook/version | None. Planned `wudangdexiaodoashi/egrd-v032-real-gemma-evidence-ab` remains unused. |
| GPU dispatches / SaveKernel / real Sessions | 0 / 0 / 0 |
| Actual GPUs | None allocated to this study. 4×L4/TP4 is only the frozen request. |
| Model loaded | No. Version-2 metadata lists all eight expected assets; mounted byte verification was NOT_RUN. |
| Exact model/tokenizer/template used | None used. Expected identities are in MODEL_IDENTITY.json; no upstream HF revision invented. |
| Runtime used | No Kaggle runtime started. Planned vLLM 0.19.1, Torch 2.10.0+cu128, Python 3.12, CUDA 12.8 and pinned SDK. |
| Context / generation | Planned context32768, output16384, thinking4096, enabled; no explicit seed or later research Guard. Actual serving defaults not observed. |
| S0 bytes | Preserved: `3303d6e1dd246d3861910701beb580c8d9a165ea1eb1c1a13d8c8ba9d6efd4f9`. |
| A/B input identity | Verified against PR40 CPU requests; only frozen supplement differs. No real-Gemma boundary was reached. |
| A / B completion | NOT_RUN / NOT_RUN; completion flags remain null. |
| A / B patch submission and hashes | None observed; null / null. |
| Production files edited | Unknown/not executed; null, not an observed empty repair attempt. |
| Target, controls, regression | All current study outcomes null; prior PR40 SCRIPTED_ONLY engineering evidence retained separately. |
| Tokens/tools/time | Per-session fields null; real model requests0. No character-to-token conversion. |
| B evidence use | Not observable; no B inference. |
| Treatment hypothesis | Not tested; no repair-effect conclusion. |
| Statistical scope if eventually run | One exposed Django task, one attempt per arm; descriptive development-only evidence. |
| Next capability improvement | None selected from missing outcomes; first complete the frozen diagnostic after conflicts are resolved. |

## Gate accounting

- PASS: exact starting commit, historical archives/manifests, S0 ZIP/members,
  original task/Issue and frozen A/B inputs; previous 17-gate CPU archive verified.
- PASS: 12 new offline checks and 17 applicable PR40 regressions, payload
  compilation/closure, JSON checks, privacy scan and git diff whitespace check.
  These are engineering tests, not Gemma adoption or repair evidence.
- PASS: authenticated read-only Kaggle resources, model version metadata and
  available account quota, unique private planned Notebook identity.
- FAIL/UNKNOWN: current conflicting jobs; no assumption that HTTP404 means idle.
- NOT_RUN: actual 4×L4 allocation, accepted runtime window, mounted weights and
  tokenizer hashing, runtime SDK recheck, model startup/TP4, initial serving token
  counts, native real-model Runner, submitted-patch evaluation and runtime cleanup.
- AUTHORIZED: bounded one-dispatch/two-session owner grant, unused. The blocker is
  not lack of owner authorization. No delayed execution was scheduled.

The original CPU environment is not rebuilt. Local cached Python3.12 lacks
swegemma, so no new local full-Compiler claim is made. Exact actual-runtime
Compiler/hash checks are sealed before loading, but were not run here.

**Official Native Resolved: NOT_EVALUATED. Canonical SWE-bench: NOT_EVALUATED.
Formal Kaggle submission: NOT_RUN.** S0 remains the best-observed formal baseline.

Source base: `d2a09cb114df4621885f437bf04c4b7d919d47de`. Frozen runtime payload:
`a2ae511be5dda9fc49703dd4bae1aa1999fe085dacf6675785991427fce8eda6`. Final quota-bound Notebook was not generated because
the fresh gate failed; there is no actual execution identity or result archive.
