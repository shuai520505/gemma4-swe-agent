# EGRD conceptual architecture and trust boundary

Design only; no production implementation is approved by this autopsy.

Issue → evidence state → explicitly provisional causal hypotheses → next action → execution → source-bound observation → revise/verify/submit. This is a decision model, not an enforced state machine in the current competition package.

## A. Compact evidence state

| Field | Deterministic portion | Model/reviewer judgment |
|---|---|---|
| Issue contract | Hash/version of allowed input | Expected behavior, scope, compatibility |
| Implementation evidence | File/range/content hash and successful read | Causal relevance |
| Current patch | Base/tree/diff hash | Correctness, completeness |
| Check evidence | Check bytes/hash, source version before/after, exit, executed assertions, time | Discrimination, relevance, adequacy |
| Contradiction | Check failure / mutation since check | Which hypothesis it refutes |
| Open question | Provenance of model's stated question | Whether resolving it changes the repair decision |
| Budget | Observed elapsed tool time/calls where native interface exposes it | Next action duration unknown; no invented success probability |

Model JSON never upgrades a claim to trusted observation. Task-local files are writable and not an attestation boundary. Helper state covers only observations collected through that helper; direct official tools can bypass it. Unknown global budget stays unknown rather than being inferred from local invocation time.

## B. Causal localization assistance (M1)

Bounded AST symbol/caller inventory could expose argument transformations or distinguish symptom site from defining code. Static Python analysis misses dynamic dispatch, aliases and generated behavior. It adds context and does not establish causation. Since all 12 interpretable failures inspected relevant implementation, absence of a symbol index is not the strongest supported bottleneck. No symbol crawler or additional retrieval tool is built.

## C. Evidence-aware next-action selection (M2)

For an optional action request, identify the unresolved question and whether either possible result could alter a patch decision. Prefer an exact local reproducer or caller read over repeating unchanged output; after an edit, invalidate prior local support until the same relevant check runs against the new source identity. Native outcome remains external.

Possible executable subset: use existing MEER check identity/freshness/duplicate behavior to return a compact discrepancy record. A model may use that record to choose a new action. Determinism can prevent this helper from labeling stale/no-op evidence SUPPORTED, or re-running an identical cached check. It cannot force the next global action, reject direct submit_patch, or prove a check is relevant. Reusing this subset is preferable to implementing another evidence ledger. Its real adoption and decision effect must first be measured in the unchanged MEER experiment.

## D. Bounded patch search/selection (M3)

If later evidence shows loss of supported repairs, investigate one primary patch plus at most one evidence-justified revision. A snapshot record would include base/source/check hashes; restoration must reject concurrent changes and preserve unrelated files. No global reset, speculative branch fan-out, or evaluator-driven selection is permitted. Local pass is not a native-correctness oracle, so automatic “best patch” selection is presently unsupported. No demonstrated lost-correct-patch frequency justifies this mechanism now.

## E. Verification and failure recovery

Reuse MEER only for source-bound execution observations, stale evidence and duplicate suppression. A timeout/import failure yields UNKNOWN/execution error, not “Issue unsolved.” A failing local assertion can itself be wrong (S2 Rich3471). On helper failure retain the patch and original error; do not auto-revert or block official submission. A future design must preserve the ability to finish useful work when the helper is bypassed or unavailable.

There are no hard phase deadlines, mandatory edit counts, hidden evaluator feedback, extra models, or automatic assumption that more diagnostics improve repair.
