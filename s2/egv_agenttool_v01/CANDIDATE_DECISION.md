# S2 development decision

**CPU Feasibility: GO, with audited limitations. GPU execution: NOT AUTHORIZED / pending quota and final seal. Algorithm benefit: UNTESTED.** This candidate is an official declarative AgentTool architecture, not an external repair controller. No GPU, LoRA or formal submission was launched. S0 remains the sole confirmed Public Score0.13, submission57261002 COMPLETE; S2 has no score.

| Question | Answer and actual evidence |
|---|---|
| Q1 Two Agents implemented? | Yes: candidate/agent.yaml declares one official AgentTool; child YAML has three bound organizer tools. Official real Runner role-tagged traces and source edits are in results/cpu05/validation/cases/native_closed_loop. |
| Q2 Official Compiler accepts? | Yes: ZIP extracted and compiled by actual adk-submission0.2.13; candidate generation/schema/empty-State rendering passed. results/cpu05/validation/new_tests.log and official_source_index.json. No research Python is in ZIP. |
| Q3 EGV actually runs tools? | Yes in CPU: real read_file and run_command execute checks.py, workspace provenance and failed/passing assertions. Model responses are scripted HTTP, not Gemma. Native nested_audit.jsonl lines23/27/41/45. |
| Q4 Counterevidence returns? | Yes in CPU: actual AgentTool FAIL return at line30, also received in following Main HTTP request; output_key is updated. Negative lost_result does not count as delivery. |
| Q5 Main really repairs? | Yes in CPU: actual edit_file changes n>0 to n>=0, line34; actual diff and hash change, not a prose claim. Ignored/still_fails/old_regression negatives remain failures. |
| Q6 Retest and explicit submit? | Yes in CPU: target/old-negative assertions pass at line45, diff at52, official submit_patch success at56; native.patch155 bytes. Direct Main retest variant also works. submit_fail records actual GitDiffError and is not credited as submit. |
| Q7 Shared300s/60 tools effective? | Yes under actual organizer semantics: budget01 native deadline300.098s cancels child HTTP; actual shared charged count60 denies later Main/child charged operations. Raw71 tools/74 model dispatches demonstrate that60 is not a cap on all function/model events. Free status/submit/wrappers can continue before enclosing time limit. |
| Q8 Production-write risk? | Yes: real child run_command Shell write changed app.py; file hashes and Git boundary evidence expose it. Prompt restriction plus auditing is not forced isolation. No edit/write/submit schemas in child, but Shell remains powerful. Future observed child workspace write triggers architecture STOP. |
| Q9 Eight-task experiment ready? | Candidate/source/task/order/model/wheels and two guarded Notebook drafts frozen; all8 passed native clean CPU baseline,24 screened. GPU quota, explicit authorization, authorized build seal and actual Gemma startup/child/cleanup gates are pending. Thus preparation is ready, execution Go is not yet established. |
| Q10 Invest in GPU? | Recommend requesting the bounded, preregistered8-task/16-run architecture comparison after those resource/authorization gates, with no automatic launch. It can falsify usefulness. Do not replace S0 or infer leaderboard gain from mocks. |

## Observed closed loop, not simulated file effects

Canonical CPU05 native trace: Main reads False implementation, writes wrong n>0 Patch, delegates; EGV reads actual workspace module and executes a real zero-boundary assertion that fails; report returns; Main writes n>=0; EGV reads current code, checks target and negative old behavior successfully; Main reviews diff and calls actual submit_patch. Two delegations,16 mock HTTP/model dispatches (Main9/child7),13 raw tools,8 counted. The second scripted delegation summary still mentions the earlier n>0 hypothesis; child actual read confirms n>=0, so evidence comes from code and commands, not the stale summary. This is route feasibility, not a demonstration of spontaneous model reasoning.

CPU05: original115 regressions independently reran and passed; new6 test methods passed with23 named ADK scenarios (not23 independent tasks). budget01:2 exact-limit methods passed in314.974s. env01: exact research observer registration, side-effect detector and statistics tests passed;24 native baselines yielded12 eligible and final8 under frozen rule. Earlier CPU01–03 failures are retained, not combined into a fabricated successful run. CPU04 first acceptance remains archived; CPU05 is final runtime acceptance.

## Limits and failure decisions

The child session does not inherit Main's whole history or native App compaction configuration. Its scoped request must contain Issue/current hypothesis; guard remains shared. An enclosing native deadline propagates cancellation, but ADK AgentTool.close is not in a finally block, so tests do not certify every possible third-party resource; this candidate configures no MCP resource. Mock cancellation is not server-side Gemma abort proof. GPU needs real route/usage/context, idle metrics and process checks.

Passive file hashes and Git status/diff are research observers, not new model tools. Full-repository hashing cost is not benchmarked on Gemma tasks; child-boundary overhead belongs to B. No independent child hard time cap exists.60s/8-call reserve is unoptimized Prompt policy, not deterministic enforcement. The child Shell negative is a real safety limitation; no invisible write prevention or repaired-success claim is made.

H1/H2/H3 remain unverified for real Gemma. The minimum useful next experiment is the registered balanced4AB/4BA eight-task comparison, not a one-task victory claim or extra tuning on historical answers. Continue only if real actionable evidence reaches Main, changes repair, passes a relevant retest and improves complete official outcomes or useful matched-correctness cost without sacrificing old behavior/submission. Otherwise report failure and stop this candidate rather than expanding a favorable partial sample.
