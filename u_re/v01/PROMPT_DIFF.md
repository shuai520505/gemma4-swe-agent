# Prompt factor and cost

The exact A→B diff is CANDIDATE_EXACT.diff. Full equals the same prefix plus the EGV block plus the same suffix; removing the block byte-for-byte yields NoEGV. Both agent.yaml and eval_config.yaml match the frozen S1 Git blobs. No generation, tools, time, name or packaging-structure change accompanies this treatment.

Compared with S0/S1, the common workflow adds evidence-based problem triage, focused early candidate repair, soft300s planning windows, explicit progress/no-progress decisions, and successful-submit closure. Ordinary tests, important old behavior, test-expectation sanity and protection of existing tests remain common. Full alone explicitly searches for unsupported behavior contracts and discriminating counterexamples with workspace provenance. This is a matched two-arm comparison of that EGV block, not a comparison with S0's historical score.

Measured in official Linux CPU01 with the mounted31BQATv2 tokenizer (transformers5.13.1), add_special_tokens=False:

| Prompt | Words | Standalone rendered instruction tokens | Raw packaged tokens |
|---|---:|---:|---:|
| S0 at972d1dd |401|524|540|
| S1-EGV atb80565a |506|659|675|
| U-RE-NoEGV |466|643|643|
| U-RE-Full |588|792|792|

Token evidence: results/cpu01/validation/prompt_tokens.json; later full acceptance independently repeats measurement. tokenizer.json SHA cc8d3a0ce36466ccc1278bf987df5f71db1719b9ca6b4118264f45cb627bfe0f; tokenizer_config.json SHA a284d1243b62be31faa9c13e1c28cece940c4abaa7bd9ad87b94f61b40687200.

S0/S1 raw Prompts have CRLF, normalized by the official include loader. Both counts are preserved, not confused. These counts exclude chat template, organizer instructions, tool schema, Issue and history. Full adds149 standalone instruction tokens over NoEGV (+23.17%); it adds133 over S1. This is actual CPU tokenization, not measured GPU inference latency, received Token totals or expected score improvement. Changing trajectories and prefix caching prevent a simple per-call multiplication from being an actual cost estimate.

The two Prompts contain no curly-brace templates. Native empty-State ADK tests capture their full instruction in the first actual serialized HTTP request; Issue JSON is preserved as task data. CPU scripted paths cannot establish whether real Gemma selects the intended checks, respects soft checkpoints or ends promptly.
