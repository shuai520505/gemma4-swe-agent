# Development-only receipt-availability comparison

Both arms use the original S0 ZIP, SHA256
`3303d6e1dd246d3861910701beb580c8d9a165ea1eb1c1a13d8c8ba9d6efd4f9`.
No new Agent, Prompt, Skill, controller, callback or tool is submitted.
The original Django Issue is verified from the hash-pinned public Parquet using
only instance_id/repo/base_commit/problem_statement. No patch/test_patch/hints
column is read. The stored original is preserved byte-for-byte.

- A receives that exact Issue and ordinary official task framing/tools.
- B receives the same Issue followed by the delimited EVIDENCE_RECEIPT.json
  observation. It contains an executed failure, positive controls and source,
  diagnostic/receipt/environment identities; no proposed code change or patch.

The original published Issue already contains the reporter's causal explanation.
It is preserved identically in A/B, not treated as independently verified root-cause
evidence and not silently removed to make the experiment more difficult. No
separate solution-hint field is supplied. This known task is DEVELOPMENT_ONLY.

Injection is a **research-controlled task-input supplement**, not a deployable
competitor callback or mechanism. S0's instructions/configuration/ZIP are unchanged.
The effective Task.problem_statement differs for B only in memory; the original
stored Issue remains unchanged. Pinned native build_agent_prompt renders it.
The scripted HTTP boundary captures the complete requests privately, permitting
a byte-bound first-request comparison after removing exactly the supplement.

There is no Agent-visible receipt file or diagnostic path in either workspace.
Only B receives the sanitized observation in task context. Reading the entire
Kaggle input is prevented by non-root chroot confinement, not by Prompt instructions.
The whole Dataset is mounted on the trusted Notebook host only.

Extra evidence and its extra context are intentional treatment differences. The
comparison does not isolate a verifier algorithm, optional Skill adoption, or an
automatic evidence-generation system. Request/token/time overhead must be included.
Token overhead stays UNKNOWN without the exact pinned serving tokenizer/template.
Character or byte counts are not token estimates.
