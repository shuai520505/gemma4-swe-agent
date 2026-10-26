# Next focused repair-intelligence study — preparation only

Question: after a contract-grounded, source-bound failure becomes available,
does Gemma convert that observation into a defensible production edit rather
than continuing unrelated diagnosis? Platform readiness is separate from efficacy.
No Agent, new Prompt, Skill or production controller is implemented here.

## Offline observation rubric

REPAIR_EVIDENCE.schema.json fixes nullable fields and enums for task/source/patch
identity, a hypothesis digest and adjudication provenance, edit kind, executed
program/receipt identity, returncode, actual assertion count, relevance review,
freshness, post-edit status, requests/tokens/tools/time and termination reason.

- **Hypothesis:** retain model claims as untrusted claims. Label supported or
  contradicted only with an independently reviewed, discriminating observation;
  unknown is the default. Do not infer understanding from a file read or score
  correctness by matching hidden/reference answers. An explanatory hypothesis
  can remain unsupported even when a related test fails.
- **Check quality:** vacuous/no-assertion checks are weak evidence, not necessarily
  useless diagnostics. Executed assertions need outcome-blinded Issue relevance
  review. Passing positive controls support environment discrimination. Target,
  import/setup/dependency, unrelated exceptions and unknown failures stay separate.
- **Source binding:** identify source before every check and edit, program bytes,
  receipt, source after execution and patch bytes. A receipt is current only if
  its tested-source identity matches the current tree. Reusing a pre-edit green
  result after an edit is stale. A changed program is a new check.
- **Edits:** classify by reviewed behavior and path/diff. Production, scratch,
  debug-only and import-only edits differ. A production filename alone cannot
  establish a meaningful behavior change. Preserve both failed and promising
  revisions and their source-bound feedback.
- **Costs:** request/tool/token counts come from actual events, not estimates.
  This CPU run has zero model requests; Agent tool/token observations are null,
  not invented zeros. Failed/incomplete attempts remain in cost denominators.

The schema validates structure and explicit missingness. Semantic relevance and
causal correctness remain human/model judgments with separately recorded evidence;
schema acceptance is not automatic semantic adjudication. These are offline
research records, not a newly deployed deterministic verifier.

## Smallest useful future experiment

A separately authorized development-only matched study can use one current
reproduced task, with independent reset workspaces and the same frozen repair
candidate/model/budgets in both arms. Control gets the ordinary Issue and tools;
treatment additionally receives the already executed, source-bound contract-failure
receipt. No answer patch or modification hint is supplied. This tests receipt
availability, not optional Skill adoption or the verifier algorithm in isolation.
Giving a receipt introduces context and evidence-access differences; record both.

Primary development endpoint: independently reviewed production change addressing
the contract plus fresh post-edit probe/regression results. Record time to edit,
requests/tokens/tools, irrelevant diagnosis, patch identity, revisions and closure.
Do not call these official Native Resolved or canonical SWE-bench resolved.
Native/SWE-bench efficacy requires the respective unchanged legitimate evaluators.
S0 remains the ultimate competition reference; a different base candidate would
confound a pure mechanism comparison and must be reported as such.

The receipt hypothesis is falsified on the observed pair if the treatment still
does not use the failure to inform a defensible edit, or only increases cost or
produces a misleading repair relative to control. One task is a mechanism-debugging
case, not statistical or held-out evidence. Freeze exact candidate/task/environment,
receipt/interface, order, outcomes, costs and authorization before real inference.
Use untouched prospectively admitted tasks in a later independent confirmation;
never restore independence to these exposed tasks by relabeling them.

The frozen N/D adoption study, cues, historical outcomes and old task lock remain
unchanged. No model study, Kaggle dispatch or formal submission is authorized by
this proposed protocol.
