# Actual request path and scope

Frozen origin PR33 `780f7620`; PR31 origin `f8b63e9`; PR32 remains a separate
unmerged source `a1dcc83`. `SOURCE_PROVENANCE.json` independently binds local
source, official wheels, the original GPU archive and native outcome hashes.
No candidate, official component or research execution component is modified.

The 15360 admission limit belongs to the **research model-client wrapper**, not
to executable code shipped in the EGR ZIP. The research Worker supplies that
guarded model registry to the official Runner. The ZIP contains declarative
configuration/Prompt (and Skills in B/C), not this host wrapper. The formal
competition's per-task admission path is not observable here.

1. Official Runner creates an in-memory task session and compiles the declarative
   Agent with the native sandbox code executor. Its App accepts compaction only
   when the **host EvalConfig** supplies it (`swegemma/harness/agent_runner.py`
   wheel lines 609–625,670–698).
2. Pinned ADK `contents.py:71–86` assembles full session history for
   `include_contents=default`. If enabled, `CompactionRequestProcessor:35–53`
   runs before content construction; token-threshold logic uses previous
   received prompt usage (`apps/compaction.py:425–466`). These branches are code
   capabilities, not evidence they ran in PR33.
3. ADK `models/lite_llm.py:1878–1954` converts contents/system instruction and
   schemas into messages and maps max_output_tokens to max_completion_tokens.
4. The frozen MEER adapter reuses the actual real_gemma_abba 01 worker. Its
   `EvalConfig` call has **no events_compaction_config**. Default is None in the
   pinned `swegemma/config.py:118`. The similarly named `s1/worker.py:50` does
   enable research compaction, but is not the executed MEER evaluator.
5. `GuardedClient` delegates to `s1.guard.Guard`, which binds output 16384,
   thinking 4096 and seed 17. `RequestGuard` preserves the exact Issue, invokes
   local serving `/tokenize` with messages/tools/template flags, then checks
   input+output+safety (`harness_v2/context_budget.py:28–42,70–110`). Only an
   allowed request reaches actual LiteLLM/vLLM generation.

## What the actual archive proves

- All 40 sent requests have the frozen generation parameters;40 HTTP200 responses.
  All 40 serving counts equal the received prompt token usage exactly. No fresh
  model or tokenizer call was needed for this equality check.
- Full output reservation 16384 applies to every admission, independent of
  actual previous completion length. Thinking 4096 is **not added a second time**
  by the guard. Context 32768,safety 1024 therefore leave 15360 input tokens.
- Three next requests reject at A 15607/B 15684/C 15989. They never reach vLLM
  generation. These are neither backend errors nor 300 second Agent timeouts.
- Zero compaction events, zero Issue restoration flags, zero uncapped-summary
  parameter events established by source/default and original event inspection.
  Every sent request contains the exact hash-matched Issue once. There is no
  observed compaction summary or Issue-reinsertion growth in this cohort.
- Request messages extend the previous prefix monotonically by one assistant
  tool call and one tool result. No exact duplicate-message insertion is found.
  Routine retransmission of history on later requests is not an insertion bug.

## What is not proven

The exact local tokenizer/template files are unavailable, although original
runtime hashes establish their identities. Component token replay is NOT_RUN;
character sizes are not token estimates. Provider history includes both
reasoning_content and reasoning fields. Whether/how each is rendered by the
missing template, and their individual token contribution, remain unknown.
Their coexistence is not proof that reasoning was tokenized twice.

The passive observer has no final rejected HTTP body because no generation was
sent. Its guard count/time are observed, but per-message sizes for that body
stay null. Formal competition per-task traces and the complete local production
inference config loader are also unavailable. Research guard behavior must not
be presented as the proven cause of official 0.13→0.12→0.10 score changes.
