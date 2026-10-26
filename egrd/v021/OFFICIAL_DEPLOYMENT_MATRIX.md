# Official deployment gate: pinned distribution

Scope: PR34 `31511563da988634825d8148da1d2f0624303f03`; independent branch,
no historical merge. The pinned bytes, not generic ADK documentation, are the
authority for this audit. SOURCE_PROVENANCE.json records whole-wheel/member
SHA256 and exact symbol line ranges for adk-submission 0.2.13, google-adk
1.36.1, swegemma 0.2.11 and adk-eval-core 0.1.0. All four CRC/SHA checks pass.

Primary distribution provenance: [competition data](https://www.kaggle.com/competitions/gemma-4-developer-agent/data).
The locally retained, hash-verified HARNESS_README is the available loader
documentation; the complete `scripts/inference.py` is not present. No claim is
made about an unseen private scorer, an undocumented override or future SDKs.

Evidence levels: **S** = complete pinned source/schema inspected; **E** = exact
source exercised locally, with external doubles explicitly identified; **H** =
original hash/CRC-verified historical official execution. An E fragment test is
not a new full Compiler/Runner validation or a deployability proof by itself.

## Ten required questions

| # | Interface question and answer | Required classification | Exact source / executable evidence |
|---|---|---|---|
| 1 | Competitor Python before every model request? No deployable arbitrary-code hook. YAML callback **names** are accepted, but no callback registry is supplied by this Runner. Built-in instruction/Skill metadata processing is organizer code, not competitor callback execution. | UNSUPPORTED_IN_PINNED_INTERFACE | S: compiler.py:59–76,146–205; schema.py:257–323; callbacks.py:65–95, especially 84–85; swegemma agent_runner.py:617–628. E: callback-name/no-registry and rejected callable/factory fields tests. |
| 2 | Arbitrary global history rewrite? No competitor-supplied processor. There is a restricted native exception: `include_thoughts=false` filters reasoning fields and thought parts. It does not implement the requested evidence-preserving projector. | UNSUPPORTED_IN_PINNED_INTERFACE for custom projection; VERIFIED_DEPLOYABLE for native thought filtering | S: schema.py:157–175,257–323; resolvers/generation.py:80–143,195–458; contents.py:542–582. E: accepted config, original mapping/filter bodies and recorded owned message boundary; loss-of-question fixture. |
| 3 | Configure App compaction in submitted Agent? No. `EvalConfig.events_compaction_config` is a host field, not an Agent field or a documented submission budget override. | HOST_ONLY_NOT_DEPLOYABLE | S: swegemma/config.py:89–120; agent_runner.py:670–698; schema.py:257–366; guide:98,540–579. E: extra field rejected. Missing complete inference loader limits claims about undocumented behavior. |
| 4 | Built-in workflow enforces a deterministic diagnostic script step? No. It deterministically schedules child Agents, not script operations. Every compiler-accepted nonempty leaf is an LlmAgent. | UNSUPPORTED_IN_PINNED_INTERFACE | S: compiler.py:208–242; workflow builders:40–142; schema.py:326–366; SequentialAgent._run_async_impl:55–92; LoopAgent:70–124. E: schema rejection, sequence bypass/exception/pause/cancel and loop-bound tests. Empty workflows perform no useful diagnostic. |
| 5 | Automatically run a sandbox Skill without a model tool call? No established startup/mandatory-call entry. The script tool runs after explicit invocation; listing/loading and metadata processing do not run it. | VERIFIED_OPTIONAL_ONLY | S: skill_toolset.py:776–874,934–954,1062–1082; tools resolver:129–264. E: request processing/tool enumeration do not execute; explicit call routes; missing args/executor fail. H: CPU03 B_BYPASS. |
| 6 | Persistent structured state across actions? Supported session state and `output_key` text, plus workspace receipts after tool invocation. Not a trusted competitor-managed state reducer or arbitrary YAML state initializer. | VERIFIED_DEPLOYABLE | S: schema.py:257–323; llm.py:72–87; agent_runner.py:672–684; llm_agent.py:830–871; guide:112,116,297–301. E: output_key saves model-authored text while retaining Issue; strict schema rejects initializer. A JSON-looking model string is not verified evidence. |
| 7 | A tool can return a bounded evidence summary? Yes, an invoked sandbox Skill can emit bounded structured output; the helper must impose its own receipt/content limits. It cannot guarantee semantic relevance or invocation. | VERIFIED_OPTIONAL_ONLY | S: tools.py:248–253; skill_toolset.py:443–708,776–874; adk_eval_core/sandbox/base.py:176–223. H: CPU03 B executed verdicts and source-bound receipts. Native run_command can also execute Agent-provided probes, after a model call. |
| 8 | Force a step before the main repair Agent? A SequentialAgent can schedule a preceding LlmAgent, if that child finishes without failure/pause/deadline. It cannot guarantee that child's diagnostic tool use or a validated handoff. | VERIFIED_DEPLOYABLE | S: schema.py:326–335; workflows.py:40–68; sequential_agent.py:55–92. E: scheduling demonstrated with external child doubles, including no-diagnostic completion and interrupted handoff. This label covers scheduling only, not diagnostic enforcement. |
| 9 | Preserve original Issue and all necessary tool evidence across workflow? The session contains `problem_description` and supports explicit state interpolation. Exact downstream message/evidence sufficiency for a new multi-agent workflow is not demonstrated here; filtering and untrusted model output can lose information. | UNKNOWN_INSUFFICIENT_EVIDENCE | S: agent_runner.py:672–704; instructions.py:41–62; contents.py:542–582; guide:297–301. E: same context/Issue reaches both fixture children; this is not a full ADK downstream message test. |
| 10 | Exact Compiler input? Directory containing `agent.yaml`, sandboxed YAML `!include` and config-path subagents, registered tools/models, optional Skill directories/adapters. Closed four-class discriminated union; no arbitrary Python entrypoint/import. Organizer API arguments are not submission YAML capabilities. | VERIFIED_DEPLOYABLE | S: compiler.py:59–205,208–242; schema.py:45–76,179–227,257–413; registry.py:30–110; guide:69–124. E: complete real schema/registry modules accept valid shapes and reject custom code/classes/tools. |

## Boundaries that must not be collapsed

- The compiler's Python parameters `callback_registry`, `agent_factory`,
  `code_executor` and registry objects are **host-owned dependency injection**.
  The actual Runner supplies the sandbox executor but no custom Agent factory
  or callback registry. Installing one in a research host would not make a
  submitted YAML mechanism compliant.
- The original `build_submission_limits` function also runs in the isolated
  tests: 500 Agents/loop iterations, output default 16384 and thinking default
  4096 are confirmed (swegemma/config.py:36–72). Its generation maxima are
  32768. The research 300-second/60-tool/120-second limits are frozen candidate
  budgets, not universal immutable defaults. Allowing `.py` as a Skill resource
  does not permit importing a host Python entrypoint.
- The guide documents official automatic compaction in `scripts/inference.py`
  (interval 15, overlap 2, threshold 14336, retention 5). That is **host policy**.
  Its existence does not expose a competitor projector. PR33's research Worker
  did not configure it; the research Guard is not proof of formal scorer behavior.
- Sequential/Parallel/Loop are accepted by this restricted Compiler, not merely
  found in full ADK. Their scheduling code executes, but no accepted script-only
  Agent class, workflow operation field or forced tool-choice setting exists.
- `run_skill_script` does not require a prior `list_skills`/`load_skill` call
  (776–874). Removing discovery steps is feasible; removing model choice is not.
- A significant supported exception is **native thought-history filtering**.
  `ThinkingConfig.include_thoughts=false` reaches the original generation
  resolver and automatic official serialization/response filters. This executes
  without a voluntary Skill call; it is not an arbitrary competitor callback.
  With a positive thinking_budget=4096 the mapper keeps thinking enabled while
  filtering returned/history thoughts. Owned boundary tests preserve the Issue,
  tool IDs, source/patch labels and tool failure text, but lose a repair question
  present only in a thought part. Thus not every automatic history operation is
  unavailable; this fixed operation does not meet the requested preservation
  contract or expose a customizable projector. No tokenizer saving is claimed.
- Python Skill scripts use `runpy` in a temporary directory. SkillToolset's
  `script_timeout` applies directly to shell subprocesses, not Python `runpy`
  (636–700,896–899). The official outer sandbox executor enforces command/remaining
  budget and removes its transient launcher (base.py:176–223). A helper still
  needs a shorter child budget and an explicit persistent workspace receipt path.

## Local execution limits

Twenty-four new offline interface tests exercise complete pinned Pydantic schema and
registry modules, exact isolated workflow/Skill method bodies, and historical
official records. The local interpreter has Pydantic 2.13.4 but lacks the full
ADK/Compiler installation. No SDK installation or full Agent compilation is
claimed. External context/child/executor doubles test routing, not semantic
diagnostics, real Gemma adoption or a newly deployed mechanism.
