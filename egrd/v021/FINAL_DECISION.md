# EGRD_V021_OPTIONAL_ONLY

Code outcome: **CPU_SPIKE_NOT_APPLICABLE**. Interface tests pass; these are
separate conclusions. No new production mechanism, Agent ZIP or deployment is
created. No GPU, Notebook save/dispatch or Competition Submission occurs.

## Required answers

1. **Competitor-controlled pre-inference execution?** No arbitrary-code path in
   the pinned submission interface. Names are not implementations; native
   Runner omits callback_registry. See compiler.py:59–76,146–205,
   callbacks.py:65–95 and agent_runner.py:617–628.
2. **Global history modification?** No programmable competitor hook. A verified
   restricted native operation does exist: include_thoughts=false removes
   reasoning fields and thought parts, automatically. It loses a question present
   only in thought, so is not the required evidence-preserving projector
   (schema.py:157–175,257–413; generation.py:80–143,195–458). The separate
   include_contents switch retains the current task chain (contents.py:542–582).
3. **Submitted Agent compaction?** No exposed Agent setting. The App option is
   host EvalConfig; guide-described official compaction does not confer
   competitor control (config.py:89–120; agent_runner.py:670–698;
   guide:98,540–579). Full inference-loader source remains unavailable.
4. **Workflow guarantees a deterministic diagnostic?** No. Four restricted
   classes route to LLM/workflow builders; scheduling does not require a tool
   call. A preceding child can finish with zero diagnostics, or fail/pause
   before repair (compiler.py:208–242; workflows.py:40–142;
   sequential_agent.py:55–92; loop_agent.py:70–124; new executable tests).
5. **Can a Skill be forced?** No supported mandatory/startup invocation. The
   available mechanism is VERIFIED_OPTIONAL_ONLY. Direct run_skill_script
   routing needs no earlier discovery call, but the model must choose it
   (skill_toolset.py:776–874,947–954,1062–1082).
6. **What runs without voluntary Skill choice?** Built-in workflow scheduling,
   instruction/state substitution, native thought filtering and organizer host policy. None provides the
   requested competitor-defined deterministic diagnostic or global projector
   (workflows.py:40–142; instructions.py:41–62; generation.py:195–458;
   native Runner:670–704).
7. **What did CPU tests demonstrate?** Twenty-four new tests exercise the complete
   real schema/registry and isolated exact method bodies, with explicit doubles.
   Fourteen inherited offline context/interface regression tests also pass.
   The original CPU03 archive additionally proves an actual official scripted
   Skill invocation and an actual bypass. This is not a new full SDK/Runner run.
8. **What still needs Gemma?** Invocation/adoption, correct contract selection,
   whether evidence changes decisions, costs and Native Resolved effects.
   The CPU routing spy is not diagnostic execution; historical scripted repairs
   do not establish autonomous behavior. No new real-Gemma evidence is claimed.
9. **Which mechanism targets the observed failure?** Bounded discriminating
   reproduction directly targets A's malformed/non-discriminating diagnostics.
   It cannot derive a correct contract from assertion counts. Context termination
   is also observed, but global projection lacks the required deployment path.
   Existing MEER already implements much of the optional deterministic subset.
10. **Likely cost?** No new production mechanism is benchmarked. A future cue
    adds instruction tokens and may induce extra tool/model rounds and bounded
    probe time. Measured historical Skill-package overhead was 800 initial
    tokens versus EGR; that is not the cost of an unbuilt new cue. Actual repair
    overhead and semantic value remain unknown. Avoid extra diagnostic Agents.
11. **Can it deploy officially?** The optional Skill path has source plus actual
    historical official execution evidence. Automatic diagnostic enforcement and
    competitor history interception do not. Python script_timeout is not an
    internal Python timeout; the outer native executor provides the command/
    remaining-budget boundary (skill_toolset.py:636–700,896–899;
    adk_eval_core/sandbox/base.py:176–223).
12. **Falsification?** Continued bypass rejects an adoption claim. More calls
    yielding vacuous/wrong-contract evidence, greater cost without useful edits,
    or native repair regressions undermine usefulness. Script success alone
    cannot support the benefit claim.
13. **Implement next?** No new verifier now. Prepare the smallest matched
    adoption diagnostic using the existing Skill and one direct-call cue versus
    neutral control, then seek separate execution authorization. No cue text,
    new Prompt artifact or candidate is implemented in this task.
14. **Do not implement?** A research-only history interceptor, injected callback
    registry, arbitrary ScriptAgent, global submit/tool gate, semantic compressor
    without a deployable hook, or another optional Skill advertised as mandatory.
15. **Comparison with S0?** First isolate adoption using identical MEER interfaces
    and fixed resources. If useful adoption is established, separately compare
    active/inert execution with the same cue. S0 remains the ultimate exact
    frozen deployment reference; a later S0 comparison is confounded by Prompt/
    interface/default-generation differences and is not a pure mechanism ablation.

## Hard gate and limitations

**CONTEXT_PROJECTION_NOT_DEPLOYABLE** through the pinned documented competitor
interface. This is a scoped engineering decision, not permission to work around
it. Unknown private/current loader behavior is not treated as permission.
The exact source evidence and required labels are in OFFICIAL_DEPLOYMENT_MATRIX.

No new Spike is justified for mandatory execution, so the eight reproduction
fixtures are NOT_RUN for a new mechanism. This does not mean optional scripts
are prohibited. It means a script test would not answer the unresolved adoption
problem and would duplicate existing MEER engineering evidence.

All new work is under egrd/v021, from actual open/unmerged Draft PR34 HEAD
31511563. The original source/wheel/candidate hashes, historical failure and
unknown outcomes are preserved. Raw model/evaluator/test/patch bodies stay
private; only source identities, tests and derived research records are public.
No deployment, S0 replacement, merge or repair-success claim is recommended.
