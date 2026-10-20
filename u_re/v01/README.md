# U-RE V0.1 — Unified Repair & Evidence Agent

One Gemma4 31B QAT LlmAgent performs triage, repair, evidence-gated verification and closure. This is a declarative Prompt-based workflow, not four Agents or an external state controller. The NoEGV arm has ordinary tests, identical repair/closure/progress/budget guidance, and no dedicated counterexample-search block. The Full arm adds only that block.

Both independent three-member ZIPs derive byte-identical agent.yaml and eval_config.yaml from frozen S1 b80565a. Model, six tools, generation settings,300s/60 counted tools/120s command ceiling are identical. CANDIDATES.json and CANDIDATE_EXACT.diff are machine-checkable. No executable research code, tests, answers, AgentTool, child Agent, Jev or LoRA is in either ZIP.

Entry points:

- ARCHITECTURE.md: scope and evidence-backed design rationale.
- PROMPT_DIFF.md: exact treatment and measured tokenizer costs.
- CPU_VALIDATION.md: actual acceptance, failures and limits; CPU_PASS is not Gemma autonomy.
- BUDGET_GUARD.md: Prompt guidance versus real Runtime guarantees.
- GLOBAL_BUDGET_ASSESSMENT.md: whole-run sensitivity and formal-submission No-Go.
- GPU_EXPERIMENT_PROTOCOL_DRAFT.md: an unexecuted paired study, not execution authorization.
- CANDIDATE_DECISION.md: Q1–Q12 and gates.
- INTEGRITY_MANIFEST.json: byte-level artifacts and source/evidence checks.

Build packages with `python -m u_re.v01.build`; inspect with `python -m unittest u_re.v01.tests.test_static -v`. A CPU build is made with `python -m u_re.v01.prepare_cpu cpuNN smoke|full`. CPU-only launch guards reject GPU metadata. Do not overwrite registrations, launch intents or old evidence; use a new revision after an actual correction. Official Linux CPU execution replaces only model HTTP replies; native Compiler, ADK Runner, Git, sandbox commands, assertions, budget counting and patch capture execute for real. Exact commands and final results belong in CPU_VALIDATION.md.

GPU_NOT_TESTED. No GPU Notebook or formal submission is authorized or created in this work. Neither positive CPU fixtures nor S1's local404→200 correction establish U-RE repair-rate improvement. Frozen S2-T500 formal57402336 has runtime error and Public Score=null; S0's confirmed57261002 remains0.13.
