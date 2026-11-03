# EGRD V0.2 architecture

Base: PR45, `72a57ffe189792c337e05e7e771a413c6b75e22a`. Changes are confined to this independent directory on `egrd-v02-entrypoint-hardening`.

## Actual execution path

Official Compiler -> one Gemma ADK agent -> six official Workspace Tools plus official SkillToolset -> nonroot workspace -> official submit_patch -> isolated official Native Evaluator -> worker receipts -> aggregate supervisor.

The six workspace tools remain get_status, run_command, read_file, edit_file, write_file and submit_patch. SkillToolset adds its own official list_skills, load_skill, load_skill_resource and run_skill_script. No second agent or model is introduced.

All four packages share the same FIRST ACTION prompt and Skill documentation. A/C have the existing inert script control; B/D have the unchanged executable V0.1 core. A/B use 12B, C/D use 31B. This round prepares only B engineering smoke; D is a separate conditional fallback, not an automatic extension or efficacy comparison.

## Mechanisms and their scope

| Component | Actual authority |
|---|---|
| FIRST_ACTION / Skill instructions | PROMPT_ENFORCED_OPTIONAL_EXECUTION; model can omit calls |
| core.py / Skill CLI | Deterministic source hashes, ledger invalidation and bounded lifecycle, but only when invoked |
| activation.py | Passive audit of real ADK calls, responses and exported state; not a controller |
| timing.py | Host observation of the real SDK timeout, plus research Context clock alignment; no deadline extension |
| result_contract.py / supervision.py | Executable fail-closed process/result/cleanup stop decisions |
| model_selection.py | Bounded diagnostic recommendation; never dispatch permission |
| MEER | Existing deterministic checks when invoked; no hidden evaluator access |

No CallbackRegistry or competitor middleware is wired into the official runner. Host tracing is pinned to the observed SDK source and is research instrumentation, not a claim that a submitted agent can intercept every tool.

Native verification loads the public evaluator test patch only after the Agent ends, into an independent workspace. No reference production patch or hints are used. Native resolved=false with error-free actual test execution is an ordinary failed repair; missing/error evaluator, JUnit setup errors, missing/all-skipped reports or unconfirmed cleanup stop the run. CPU02's raw plumbing PASS was rejected by this trust audit (187 fixture errors).

Source pool, Issue, snapshots, package members, system prompts, Skills, model files and runtime/evaluator versions are locked separately. The official snapshot has a synthetic Git HEAD; SNAPSHOT_BASE_BINDING proves every regular source byte matches the canonical upstream base. These identities are not conflated.
