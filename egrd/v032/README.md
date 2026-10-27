# EGRD V0.3.2 — frozen S0 evidence-to-patch A/B

Development mechanism study, based on PR40 commit
`d2a09cb114df4621885f437bf04c4b7d919d47de`. One owner-authorized private
GPU Notebook, A then B, at most one real Agent invocation per arm. No retries,
extra inference probes, candidate changes, or competition submission.

The exact S0 ZIP and Django source are unchanged. B receives the original frozen
failure supplement; A receives only the original Issue. The owned development
probe is not official Native or canonical SWE-bench evaluation. Both official
outcomes remain null. Historical S0 serving equivalence is unverified.

`EXPERIMENT_FREEZE.json` and `GPU_ENVIRONMENT_LOCK.json` bind the common settings.
`BUILD.json` binds the private executable payload and Notebook. Raw requests,
responses, patches and evaluator files remain outside Git. No model weights are
included in the payload; the immutable Kaggle model instance version 2 is mounted
and every model/tokenizer/template file is hashed before loading.

Local checks: `python -m unittest egrd.v032.test_preflight -v`. The 17 applicable
PR40 regression checks also pass; its old branch-specific scope test is replaced
by this branch's historical-integrity check. These are CPU engineering tests,
not new Gemma observations.

Execution uses the pinned official Compiler, S0 Runner and six tools. The PR40
research filesystem adapter connects the external Django task to that path;
it is not a competitor-deployable controller. Passive HTTP/source observers do
not change messages, generation, tool decisions or trusted test expectations.
The first-request identity gate stops unexpected input before forwarding it.

No later research Guard, seed, safety reserve, history projection, compaction,
thought filter, Skill or Prompt change is added. Both arms share one read-only
model server with prefix caching disabled, and have independent workers, source
trees, chroots, histories and trusted post-session evaluations. This common
server setting is an explicit experimental choice, not a historical S0 claim.

The predeclared primary requires a defensible submitted behavioral patch,
applicability, fresh target/positive-control/regression evidence and independent
review. Missing, failed, timed-out and unsubmitted outcomes are retained.

See `FINAL_DECISION.md` for observed execution and interpretation after collection.
