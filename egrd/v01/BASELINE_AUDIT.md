# Production architecture audit

Official path in the pinned distribution: submission ZIP → declarative `agent.yaml` / `eval_config.yaml` / includes → `adk_submission.compiler` → ADK Agent and registered tools → `swegemma.harness.agent_runner` with sandbox executor → tools / patch collection → trusted native verifier. Source identities were independently rehashed in SOURCE_AUDIT.json. Research workers, observers, chroot adapters and analysis scripts do not become submission mechanisms simply because they exist in this repository.

| Family | Production change | What is not enforced |
|---|---|---|
| S0, `candidates/s0/submission/` | Single LlmAgent; six tools; original strategy/config | No evidence controller. Best observed formal score 0.13, not a matched efficacy guarantee |
| S1, `s1/packages/`, `s1/egv_v01/` | Separate output/thinking/localization/verification prompt variants | Config/prompt tests do not demonstrate autonomous repair improvement |
| CURE, historical `cure/candidates/` | Checklist/CURE decision language and model-authored JSON in declarative candidate | Model JSON is untrusted advisory state; research-only controller code is not deployed. CURE generation differs from U-RE; do not pool causally |
| U-RE NoEGV / Full, `u_re/v01/` | Frozen three-member ZIPs differ in the EGV instruction block | Full has no independent verifier sub-Agent or deterministic evidence gate |
| Action-First, `u_re/v01/experiments/action_priority_01/` | Adds 119-word action-priority block | No execution-control change |
| EGR, `u_re/v04/experiments/evidence_guided_repair_01/` | Replaces strategy block with evidence-oriented instruction | No production tool interception, test freshness enforcement or causal oracle |
| S2, `s2/egv_agenttool_t500*` | Optional AgentTool and different 500s/compaction research setup | Five observed sessions do not delegate to the optional verifier; native success cannot be credited to its execution |
| MEER, `meer/v01/` | Official SkillToolset and executable sandbox evidence checker; B/C differ in script, A is exact EGR | Can enforce its own checks/cache/timeout, not invocation, global tool choice or final submission |

Byte comparisons independently confirm NoEGV/Full/Action-First/EGR `agent.yaml` and `eval_config.yaml` are identical. Their Prompt differences are the deployable factor. A/B/C MEER digests and exact differing members are in SOURCE_AUDIT.json; no ZIP was rebuilt. S0 defaults must be read through its compiler, not assumed equivalent to every later explicit generation field. Historical S2 and CURE use different budgets/configurations and synthetic/exposed tasks.

Research V0.3 changed output reservation consistently in the research worker/guard; this is not an EGR Prompt mechanism. Research chroot isolation protects evaluator data but is not evidence of improved repair decisions. Native result readers and taxonomy code are evaluator-side observers, never Agent tools.

Relevant pinned source references: `compiler.py:63,193,208` accepts optional callback registry and builds registered classes; `resolvers/callbacks.py:84` returns no callbacks when registry absent; `agent_runner.py:609` creates native sandbox executor; `agent_runner.py:1082–1096` handles missing explicit submission and working-tree fallback. These explain why three observed native successes without submit are real outcomes, not missing-data failures.

Formal archived scores: S0 57261002=0.13; Full 57505115=0.12; EGR 57566588=0.10. No per-task official trajectories were available. No causal claim that EGV, longer instructions, or EGR caused this decline is supported by those three aggregate observations.
