# Offline validation and reproducibility

Scope: no new model, Agent, Notebook, sandbox repair or formal submission.

| Check | Actual result |
|---|---|
| `python -m egrd.v02.source_audit` | PASS: original archive CRC/SHA, three pinned official wheels, all 206 shared payload members, 205 registration entries, eight archived model-file identities, three candidate ZIPs and native outcome/JUnit hashes |
| `python -m egrd.v02.context_audit --output <private replay directory>` | PASS: 40 real requests and three rejected opportunities reconstructed; four resulting JSON files match the public derived outputs byte for byte |
| `python -m unittest egrd.v02.test_context_audit -v` | PASS: 14 tests, 1.976 seconds in the retained run; individual results in OFFLINE_TESTS.log |
| Exact token-level component rendering replay | NOT_RUN: exact local tokenizer and chat-template assets unavailable |
| New official Compiler/Agent end-to-end execution | NOT_RUN: intentionally outside this offline audit |

The tests compare the analytic boundaries with the unchanged registered policy,
verify rejection before generation, Issue restoration idempotence on synthetic
data, output/guard consistency, all original aggregate prompt counts, monotone
history and zero compaction, source-deployment exclusion, read overlap, missing
outcomes, deterministic serialization and the prior context pilot. Pinned
official helper tests cover empty callback registry and the actual meaning of
`include_contents: none`, plus absence of an Agent compaction field. They do not
claim complete current competition-platform validation.

Reproduction requires the privately retained original archives, official wheels
and separately preserved PR32 worktree named in SOURCE_PROVENANCE. Missing
sources cause errors rather than replacement with summaries or another
tokenizer. Analysis scripts export derived metadata only. The private bodies,
reasoning, tests, evaluator payloads and full patches are not public fixtures.

No performance gain is inferred from these engineering tests. The manifest
hashes public deliverables separately from source evidence. Original candidates
and history remain outside the new research-directory diff.
