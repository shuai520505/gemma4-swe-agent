# CONTEXT_PROJECTION_NOT_DEPLOYABLE

This decision is scoped to a **competitor-defined global projector through the
pinned documented submission interface**. It is not a claim that the host lacks
ADK compaction, nor a universal prohibition about unseen/future interfaces.

## Verified restricted exception: native thought filtering

The generation resolver is an important qualification to PR34's earlier broad
interface audit. The submitted `thinking_config.include_thoughts=false` field
is accepted (schema.py:157–175). The official LLM builder calls its generation
resolver and thinking mapper (llm.py:68–87). That resolver installs its own
fixed serialization/response filters (resolvers/generation.py:195–458):

- `_enrich_completion_inputs`:270–285 removes reasoning/reasoning_content from
  serialized outgoing assistant messages when configured false.
- `_strip_thought_parts_from_response`:119–143 removes thought parts before
  storage in ADK history. Positive thinking_budget=4096 still enables thinking
  in the mapper; hiding returned thoughts is not necessarily disabling inference.

Exact isolated mapping/filter bodies were executed against owned input/output
fixtures, with a recorded synthetic model-boundary capture. They preserve the
Issue, tool-call IDs and ordinary tool failure/source/patch labels. They also
remove an unresolved repair question whose only representation is a thought.
Thus a **limited automatic context operation is deployable**, without a Skill.
It is not a customizable evidence-preserving history projector and does not
satisfy this task's required unresolved-question/evidence-retention guarantee.
No token savings or repair effect is measured from these structural fixtures.

We do not call the official patch installer against Google modules or install
our own model wrapper. The CPU tests isolate its original function bodies;
production artifacts and generation settings remain unchanged. A full local
SDK compile of the thought-filter setting is NOT_RUN, not claimed successful.

## Projector gate

The gate fails before tokenizer acquisition or compression implementation:

1. The complete restricted schema accepts no custom history processor, custom Agent
   class, compaction field or code-executor function. Extra fields are rejected
   in executable Pydantic tests (schema.py:257–413).
2. Registered before-model callback names have no effect with the Runner's
   absent callback registry (callbacks.py:65–95; agent_runner.py:617–628).
   Names cannot import competitor code or register a new function.
3. App compaction is attached by the host from EvalConfig (config.py:89–120;
   agent_runner.py:670–698). The guide's documented submission eval_config keys list
   budget/time/turn keys, not a custom compactor (guide:98,540–579). The actual
   full inference loader is unavailable; no undocumented override is assumed.
4. A Skill can run its own bounded script when invoked, not mutate host ADK
   conversation history. `include_contents: none` keeps the current task/tool
   chain (contents.py:542–582). A workflow can add model turns or handoffs,
   but that is neither a selective deterministic projector nor zero-cost.

Therefore **reject custom evidence-preserving global context projection as the immediate production
mechanism**. No research-only interceptor, custom registry, semantic compressor,
tokenizer download or speculative projector was built. This resolves PR34's
open deployment question negatively for the available supported interface.

The smallest official clarification that could reopen the gate is an explicit
organizer-supported submission field and callable registry entry for bounded
pre-request history transformation, including ownership, allowed mutations and
accounting. A generic ADK class or a successful research-host hook is insufficient.

This gate does not establish that projection would improve repair if allowed.
The original cohort has nearly no repeated source lines, and prior context-cap
expansion removed guard stops without another native success. Preservation of
Issue/source/patch/adverse evidence would still require a separate study.
