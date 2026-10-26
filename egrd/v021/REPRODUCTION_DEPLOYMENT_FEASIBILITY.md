# Reproduction assistance: executable after invocation, not mandatory

**VERIFIED_OPTIONAL_ONLY**. The supported pathway is:

submitted Skill directory → restricted compiler `resolve_skills` → official
SkillToolset → model-selected `run_skill_script` → official sandbox executor →
structured tool response. Native `run_command` is another model-selected path.
This is actual executable behavior, but not automatic reproduction enforcement.

Source: tools.py:129–264, llm.py:58–87, skill_toolset.py:776–874,
adk_eval_core/sandbox/base.py:176–223, native Runner:604–629. Hash-verified
CPU03 original archive independently demonstrates script execution and a
separate successful submit without invoking it. B/B_BYPASS native synthetic
results are engineering evidence only. PR33 B/C real-model non-adoption remains
unchanged; an unexecuted verifier cannot be evaluated for repair efficacy.

## Useful deterministic subset and semantic boundary

| Desired feature | Executable subset if invoked | Cannot establish deterministically |
|---|---|---|
| Expected/actual contract | Store explicit Agent-provided fields and hashes | Whether that contract matches the Issue |
| Source version | Hash workspace source/patch and bind check identity | Root cause or whether inspected files suffice |
| Bounded probe | Child timeout/output/file budgets under outer sandbox limit | That the time spent has useful information gain |
| Vacuity | Count executed nonconstant assertions; reject assertion-free/obvious constants | That a nonconstant assertion tests the right behavior |
| Failing result | Record assertion execution/failure and traceback category | That an AssertionError witnesses the target defect |
| Environment/setup | Report ModuleNotFoundError, TypeError and other exceptions separately | That every import/setup error is independent of the target Issue |
| Source-bound receipt | Return bounded explicit evidence and freshness labels | Semantic correctness or Native Resolved |
| Stale checks | Invalidate a prior source/check identity after changes | Force the Agent to request a fresh check or obey it |
| Deadline | Enforce helper's own cap after invocation | Reserve time globally or guarantee final submission |

MEER already implements much of the hashing/assertion/timeout/receipt subset
(`meer/v01/verify.py:1–end`; original SHA in CANDIDATE_MANIFEST/INTEGRITY_MANIFEST).
A new name or contract JSON wrapper would not solve non-adoption. A receipt must
keep semantic relevance UNKNOWN unless established by independent evidence.
It must not treat every exception as target failure or every passed check as
correct repair.

## Why workflow scheduling does not solve invocation

The accepted workflow classes schedule accepted subagents only. They have no
script/tool-operation field. Compiler dispatch only reaches LlmAgent,
SequentialAgent, ParallelAgent and LoopAgent (compiler.py:208–242). Arbitrary
subclass or Python references are rejected (schema.py:45–76,326–413).

Executable negative tests run the pinned Sequential/Loop method bodies with
owned external child doubles. A preceding diagnostic child can emit a final
response with no tool call, after which repair runs. A pause, exception or
cancellation can instead prevent repair. Loop bounds cap child invocations,
not successful diagnostic execution. Adding a front LlmAgent is therefore
**model-mediated**, with extra inference/history cost, not deterministic
enforcement. Its root-cause/contract output is model-authored state, not evidence.

Other apparent invocation shortcuts do not change this boundary:

- AgentTool is an entry in an LlmAgent's tool list, not an automatic script leaf;
  its activation remains model-selected (schema.py:82–142; tools.py:38–126).
- LoopAgent exposes max_iterations, not a competitor-defined receipt predicate
  or "repeat until verification executed" controller (schema.py:350–366).
- `adk_additional_tools` Skill metadata changes available registered tools after
  activation, not execution (skill_toolset.py:956–1016). The LLM builder also
  retains its directly resolved official tools when appending SkillToolset
  (llm.py:58–87). This is not a hidden compulsory check gate. Removing normal
  tools would alter the comparison and still permits a final text response.
- Restricted generation config has no forced tool_choice field; the real schema
  rejects it. A host-side forced function call is not a submitted capability.

## Practical adoption detail, without a new Skill

The script tool resolves its skill and script directly, without requiring
list/load first. The current pinned API thus permits a future **single direct
call cue** using an existing Skill and exact path. This may reduce discovery
friction, but real Gemma may still bypass it. It is an adoption/guidance factor,
not an architectural mechanism or a guarantee. No new Prompt or artifact is
created here; use a matched adoption-only study before another verifier.

No production reproduction assistant is implemented in this task. The eight
proposed reproduction fixtures are not run as tests of a nonexistent new
mechanism. Existing MEER tests are historical engineering evidence, not a
substitute for proving mandatory invocation.
