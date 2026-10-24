# Production architecture audit

Audited actual open/unmerged PR29 a44cc483a6c114940a65322371dfa87ea5d9dd5e and PR30 d5c60b4a6490cc54c0eb9c65de7a966c2cc1fced via GitHub on 2026-10-24. This branch starts at PR30; no historical PR is merged. HISTORY_INTEGRITY.json binds six baseline ZIPs and every member. A later official EGR-scoring branch is separate and its files/submission are untouched.

| System | Competitor production difference | Runtime/orchestration difference |
|---|---|---|
| S0, candidates/s0/submission | Single LlmAgent, six official tools, original prompt, 300s/60/120; generation defaults omitted | No custom controller in submission |
| S1, s1/egv_v01/candidate | Same single Agent; 103-word EGV prompt experiment; explicit generation settings | No evidence verifier runtime in ZIP |
| U-RE NoEGV / Full | Same agent.yaml and eval_config.yaml; Full inserts EGV block into common prompt | No independent EGV sub-agent, callback, or deterministic judge |
| Action-First | Adds 119-word action-priority block to NoEGV; other members identical | Advisory actions only |
| EGR V0.4 | Replaces Action-First119 words with237-word hypothesis/evidence/repair guidance;703-word prompt | No new execution mechanism |
| MEER B | EGR prompt and generation unchanged; adds organizer SkillToolset and one sandbox script | Actual local assertion execution, hash-bound verdict and duplicate-check suppression; no global tool interception |

Source: u_re/v01/CANDIDATES.json; u_re/v01/experiments/action_priority_01/PROMPT_FACTOR_AUDIT.md; u_re/v04/experiments/evidence_guided_repair_01/{build.py,EGR_PROMPT_LOCK.json,worker.py,session.py}; s1/egv_v01/README.md. CURE is retained in the sibling original checkout, ../gemma4-swe-agent/cure/CURE_DESIGN.md (read-only). It explicitly distinguishes its deployable Prompt-only candidates from contract_state.py/action_selector.py/worker.py research controllers that were NOT packaged or enforced in the scorer. CURE V0.1 used8192output/temperature0.2/top_p0.95/top_k40/include_thoughts=true, so it is not a budget-matched EGR comparator. Its research controller is not a competition mechanism precedent.

## Precise official path

submission.zip -> scripts/inference.py discovery/validate_single_declared_model -> adk_submission.validate_directory/schema/closed registries -> swegemma.harness.agent_runner.run_agent_sandbox -> context.create_tools -> native AdkSandboxCodeExecutor -> compile_submission(code_executor=...,script_timeout=command_timeout) -> real ADK Runner/App -> declared tools/SkillToolset -> sandbox -> submit_patch/native fallback git diff -> Stage2 fresh verify_task -> protected-file filtering/evaluator overlay -> pytest/JUnit -> native TaskResult. Module SHA and line references are pinned in OFFICIAL_SOURCE_PINS.json.

Official sources: compiler.py59-72,189-203; schema.py247-299; resolvers/tools.py129-260; agent_runner.py600-629,778-783; adk_eval_core/sandbox/base.py AdkSandboxCodeExecutor.execute_code; google/adk/tools/skill_toolset.py571-662,776ff. The skill materializes into a temporary directory, so the verifier explicitly uses /workspace rather than its temporary cwd.

The research worker (u_re/.../real_gemma_abba01/worker.py) adds Context Guard, passive HTTP/source observers, chroot deployment, and trusted-side result parsing. EGR worker.py observes Prompt propagation. These are research host layers, not mechanisms shipped in the three-file competition ZIP. Trusted Verifier/TaskResult/JUnit parsing is evaluation-only. Never attribute their enforcement to Full/Action-First/EGR.

## Evidence and limitation

research_audit.py re-read original GPU03/PR27/PR28 archives with SHA/CRC validation:12 sessions/315 tool calls (HISTORICAL_TRACE_AUDIT.json). Only normal Agent tool events were read, not reference patches or evaluator contents. Query/result repetition and assertion syntax are observations, not proof of uselessness or successful verification. EGR's original analysis identifies a non-asserting green reproduction, very late edits with no subsequent check, and repeated diagnosis. MEER addresses the quality/freshness of local evidence; it cannot solve semantic hypothesis selection or force the model to use the skill.
