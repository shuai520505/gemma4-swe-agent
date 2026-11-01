# R2 submission package audit

CPU_VERIFIED: the real frozen official compiler accepted the exact candidate extracted from ZIP, including official tool registration and configuration parsing. SDKs: swegemma 0.2.11, adk-submission 0.2.13, adk-eval-core 0.1.0, google-adk 1.36.1, google-genai 2.11.0 and LiteLLM 1.82.4. Five newly downloaded organizer wheels match the frozen R12 wheel hashes. No stubs, monkeypatched tools, model load or inference were used. CPU_COMPILER_RESULT.json records the actual result, schemas/config and source hashes. Compiler acceptance is not a repair score or a whole-platform deployment test.

The local CPU environment does not have complete swegemma distribution metadata closure: pip check reports missing accelerate, safetensors, torchvision and transformers. The actual compiler and official tool registration import/run without these modules, but full model/serving runtime dependency acceptance is NOT_RUN here, not PASS. The previous R12 Linux serving run remains separate historical evidence. Raw dependency output and installed CPU package lists are retained; no GPU library installation or fake import stub was used to conceal this gap.

Candidate `submission_r2_candidate.zip`: 3646 bytes; SHA256 `af918c1a65aeb211298f13a69b5b789ae6b086974922c80469df87d902eb98d5`. It is byte-identical to frozen R2, including eval_config; it was not regenerated or silently retuned. The independent unpacked directory contains exactly agent.yaml, eval_config.yaml, configs/sampling.yaml and prompts/system.md. Agent YAML is at root, every include resolves inside that root, no archive symlinks/traversal, unrelated tests, research patch, data, adapters or executable framework files are present. Static credential patterns and the four actual texts were inspected; no secrets added. Full member hashes are in R2_SUBMISSION_MANIFEST.json.

STATIC_ANALYSIS: exact ZIP comparison with the historical BASELINE changes only prompts/system.md. The prefix is exactly the Baseline prompt and the suffix exactly the frozen six-rule R2.md. Model, nine registered tools, schemas, sampling .2/.95, output 8192, thinking 4096/include_thoughts true, budgets 8min/28calls/80turns/240s, and absence of LoRA are unchanged. The downloaded historical 0.15 submission receipt (ID 57666970) identifies the same Baseline SHA256 `944e1d23ce5e93a77af3e993834487e829487aff0a92ec7fe3e115590bfaf9f1`. This is stronger package identity evidence than copying the current Notebook's output; that later output had a different hash. R2 has no official score yet.

The graph tools already existed in the scored BASELINE registry; its own prompt forbids using them. They are retained without adding a mechanism. R12's host prefix-cache setting was false; server caching and scorer environment are outside these four ZIP files. Equality of package configs is verified, but equivalence of historical/private host serving is UNKNOWN.

The repository-at-R12 `submission/` is a separate older six-tool Agent with a different prompt, no explicit sampling include, 60min/100calls/300s local defaults and verification_timeout_seconds=300. It does not already contain R2. It is not overwritten. We do not merge R2 into that old configuration because doing so would lose the scored Baseline single-factor comparison. Instead the requested independent directory preserves the actual tested R2 exactly. No unverified field is added to make packaging appear complete.

## Official eval_config schema audit

OFFICIAL_RULE / STATIC_ANALYSIS: the freshly downloaded [organizer Starter](https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent) explicitly parses the four inference fields below. Current HARNESS_README section 7.1 maps them to Stage 1 `scripts/inference.py`; the frozen actual EvalConfig and real CPU parse agree. Official source identities are saved separately. The private inference controller's full source was not available; its runtime environment overrides are not assumed absent.

| Key | Actual meaning and support | R2 | Older submission |
|---|---|---:|---:|
| timeout_seconds | Per-command execution ceiling, not total task/session time; run_command clamps to local remaining time | 240 | 300 |
| max_time_minutes | Valid per-task Agent loop wall-clock budget; begins after sandbox setup | 8 | 60 |
| max_tool_calls | Valid charged-tool cap; get_status and submit_patch are uncharged | 28 | 100 |
| max_turns | Valid model turn limit; absent defaults are host controlled | 80 | absent |
| verification_timeout_seconds | Valid local EvalConfig/Starter Phase 2 field, but official scorer table fixes verification at 300s; not a supported Stage 1 submission override | absent | 300, local-only |

All four R2 keys have official support; no R2 UNVERIFIED_CONFIG_FIELD is retained. Older verification_timeout_seconds is classified LOCAL_ONLY_NOT_SCORER_OVERRIDE, not evidence of global runtime control. Verification is outside the stated 12-hour generation budget and cannot be added to it again. Agent time includes model waiting and tool runtime; command timeout is not additive; sandbox preparation is outside the local Agent timer but inside the all-task generation limit. Model server startup charging and exact private admission implementation remain UNKNOWN; budget scenarios include startup conservatively.

The real get_status schema exposes only current session time/calls/patch status. It provides no global remaining seconds or remaining-task count. The Starter's two published examples are not official task-count evidence. No arbitrary submission controller can be assumed callable by the Harness.

## Gate

Package/compiler gate PASS. Overall decision R2_BLOCKED_BY_BUDGET, because an unchanged eight-minute cap has no demonstrated safe full-workload coverage. The exact compiled ZIP is ready for inspection, not dispatched or formally submitted. See R2_FINAL_DECISION.md and the explicit unknown list in the manifest. GPU-specific serving libraries/runtime were not revalidated; compilation uses the genuine CPU import path with a non-listening localhost model endpoint and never invokes it.
