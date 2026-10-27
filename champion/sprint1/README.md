# Champion Sprint1

Status: **SPRINT1_PARTIAL**. Three frozen single-factor S0 candidates are available;
actual official Compiler acceptance is blocked by a CPU-only Kaggle499 UNKNOWN
dispatch. Do not submit or start GPU from this directory without new authority.

- C1_BUDGET: only Prompt; supported earlier edits and time for closure.
- C2_CONTEXT: only8192 output cap; original Prompt and thinking defaults preserved.
- C3_TEST_AWARE: only Prompt; identify a runnable targeted test, separate setup
  errors, change strategy and preserve actual test expectations.

The A fallback passes the unchanged owned target, three controls and regression
on a locally completed CPU run before execution was redirected to Kaggle. This
is scoped VALIDATED_REPAIR, not Native Resolved or a score. Raw patch/evidence
are private; no task-specific fix enters any new candidate Prompt.

See FINAL_DECISION.md, REFERENCE_022_ANALYSIS.md, A_FALLBACK_REEVALUATION.md and
NEXT_GPU_AB_PLAN.md. Public reference source/output linkage is stronger than
the exact scored-artifact linkage, which remains explicitly unverified.

build.py documents deterministic construction from original S0. kaggle_cpu.py
contains the actual CPU Compiler/member/determinism/source-bound checks. Its
private transfer Notebook has GPU/TPU/internet off and no model source. Current
CPU claim is once-only; kaggle_io.py must only be used for read-only recovery
after the existing attempt. Do not run another local installation or test.
