# Public 0.22 reference: separate version, output and scoring identity

Source: [flexonafft / Budget-Aware Coding Agent v2](https://www.kaggle.com/code/flexonafft/gemma-4-budget-aware-coding-agent-v2).
The public page displays **Version10 of10, Public Score0.22, Best Score0.22 V10**,
Apache-2.0. Authenticated read-only GetKernel independently reports currentVersionNumber10,
kernel135978120, lastRun2026-10-24T06:54:29.643Z, CPU-only. Public HTML also references
scriptVersionId357955943. These establish the public **version/score association**.

The current source still says its SuperAgent adaptation scored0.18 and this
navigation/edit-recovery candidate is unscored. Treat this as a real inconsistency
in attribution, not permission to assume every displayed feature produced0.22.

Retrieved current .ipynb/API source UTF-8 SHA256:
`ec76bd9a4dedc4626bee9d31781469023e6cfe29b666afd095dff5723f717e7b`.
Current output `submission.zip` was downloaded successfully; SHA256:
`6ff73d104725cc31deadd18787f3f55e5ce534889cec82387e3b280637d34887`.
It is exactly the previously supplied public candidate digest. Four members:
agent.yaml, configs/sampling.yaml, eval_config.yaml, prompts/system.md.
Full source/ZIP and individual member hashes are retained in private evidence
and REFERENCE_PROVENANCE.json; no reference code is copied into our candidates.

Version-pinned API reads for10 and357955943 returned404. No complete version
history or owner submission record tying a scored upload to this exact ZIP hash
was obtainable. Current output plus currentVersion10 is useful evidence but does
not independently resolve the stale unscored note or prove the historical scored
upload's bytes. **SCORED_ARTIFACT_IDENTITY_UNVERIFIED**. Keep the confirmed-scored
implementation column UNKNOWN; do not fill it from the current candidate.

| Dimension | S0 | Retrieved public candidate | Confirmed 0.22 artifact | Potential benefit | Risk |
|---|---|---|---|---|---|
| Architecture |Single LlmAgent|Single agent|UNKNOWN|Low coordination cost|No architectural efficacy established|
| Time/tools/command |5min/60/120s|8min/28/240s; max_turns80|UNKNOWN|Earlier action with fewer turns|Global budget, under-exploration|
| Output/thinking |16384/4096 defaults|8192/4096 explicit|UNKNOWN|More possible input capacity|Long output truncation; extra search cost|
| Sampling |Not explicitly set|temperature0.2, top_p0.95|UNKNOWN|Potentially stable actions|Confounded with all other changes|
| Thought setting |Not explicitly set|include_thoughts=true|UNKNOWN|Reasoning retained where supported|History growth depends on actual serialization|
| Tools |Official six|Six plus3 code-graph declarations|UNKNOWN|Graph access if used|Prompt prohibits all3; schema overhead remains|
| Localization |Focused reads|Exact symbols, bounded independent search batches|UNKNOWN|Fewer model turns/output tokens|Batching dependent searches can mislead|
| Editing |Small supported change|Must edit by12, even best guess; edit recovery|UNKNOWN|Avoid no-edit endings|Unsupported edits, regressions|
| Testing |Targeted when practical|At most2 calls; assumes dependencies installed|UNKNOWN|Bounded costs|Wrong commands, weak checks, blanket dismissal of errors|
| Submission |Explicit diff+submit|Diff+submit; says fallback counts|UNKNOWN|Closure|Empty/damaged patch still fails|
| LoRA/Skills |None|None in downloaded ZIP|UNKNOWN|Low added overhead|No mechanism enforcement|

## Four claims checked against pinned official source

1. **Fallback can be evaluated without submit_patch: supported conditionally.**
   swegemma/harness/agent_runner.py:1050-1102 captures and filters a nonempty diff
   when patch_submitted is false. swegemma/evaluate.py:324 only short-circuits an
   Agent error when no patch exists; nonempty fallback goes to verify_task.
   verification.py:646-697 derives resolved from actual test/JUnit checks, not
   solely the prior Agent error. Timeout does not categorically invalidate a
   nonempty patch. This is code evidence for our pinned distribution, not a
   guarantee of a passing score or historical server equivalence. Keep explicit
   submit for predictable closure, while evaluating retained fallback separately.
2. **Declared but forbidden graph tools:** no runtime benefit is established.
   They remain model-visible metadata and may add tokens or be called against
   the Prompt. We do not inherit them. A public claim that graphs always fail
   cannot be generalized across SDK builds/tasks.
3. **Eight minutes vs global12h:** official competition documentation gives a
   global12h patch-generation budget including sandbox setup, excluding patch
   validation. If every task uses8min, at most90 tasks fit before any overhead;
   the true bound is lower with setup. Hidden task count is UNKNOWN. Fewer tool
   calls might end tasks early but does not guarantee meeting the global limit.
   Our three candidates retain5min; no eight-minute change is bundled.
4. **include_thoughts:** pinned google/adk/models/lite_llm.py:413-437,843-944
   converts provider reasoning to thought parts and serializes assistant thought
   parts as reasoning_content. Tool metadata/contents and the serving template
   still determine actual tokenized history. This is not proof that merely
   enabling include_thoughts adds a fixed token amount or that disabling it is
   safe. No thought/filter intervention is introduced this sprint.

Official pinned source hashes are preserved in egrd/v023/RECOVERED_DEPENDENCY_IDENTITIES.json.
Useful ideas: scoped navigation, stopping unproductive search, preserving time
for a concrete change, and bounded edit recovery. Rejected assumptions: blind
best-guess edits, universal dependency availability, graph uselessness and automatic
success from any source diff. C1/C3 are our own additions to exact S0, not copies
of this Prompt. Apache-2.0/source credits are recorded for analysis; no external
code or whole Prompt is redistributed. No champion or causal score claim is made.
