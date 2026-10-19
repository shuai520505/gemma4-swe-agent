# S1-EGV V0.1: fastapi_15800 real GPU pair

2026-10-19. Experiment `s1-egv-mechanism-smoke-01`, EGV → Control, one run each. **Both official resolved=false.** EGV produced a runnable but incomplete repair, with 18 passed / 42 failed in native Phase 2. Control introduced a SyntaxError and Phase 2 stopped during collection. There is an observable verification-and-correction signal for EGV, but no complete repair win and no demonstrated population benefit. **No-Go for replacing S0 or automatically expanding experiments.**

Kaggle research Notebook [gemma4-s1-egv-mech01-gpu](https://www.kaggle.com/code/wudangdexiaodoashi/gemma4-s1-egv-mech01-gpu), version 1, COMPLETE. This was a research execution, not a leaderboard submission. S0 remains the sole recorded official score: **0.13**, Submission **57261002**, COMPLETE.

## Registration and admission

The preregistration was pushed as commit `b87c98c8fd76ae8e1c4f942881561a08ba45b38f` before the single GPU dispatch at 08:44:47 UTC. Parent was `e355ce1b3dd6802706cdd69ae3b2da4736441406`; the remote head was independently checked. See [PREREGISTRATION.md](PREREGISTRATION.md), [protocol.json](protocol.json), [freeze_manifest.json](freeze_manifest.json), [gpu_dispatch.json](gpu_dispatch.json).

Task/base/Issue/snapshot identities are the preselected values in [selection.json](selection.json). No task replacement, reference repair, reused Agent trace, rerun, or mid-experiment patch was used. The evaluator test overlay was restricted to separate native Verifier sandboxes. EGV independently wrote three local tests with the same filename as the evaluator's absent test file; their contents are demonstrably different in the native tool trace. Those self-authored tests are not the 60 evaluator tests and were not used to replace Phase 2.

The official Linux CPU checks passed **115/115** for the final CPU03 payload: frozen 113 regressions plus the two actual Compiler → empty-state ADK Runner → mock HTTP candidate tests. CPU01/02 are separately archived preparation checks, not merged evidence. The accepted CPU03 154-file source payload exactly matches the GPU payload. Mock HTTP proves API compatibility only; the GPU run below supplies actual Gemma evidence.

The fresh, unrepaired FastAPI native baseline ran all 60 evaluator cases: **60 call failures, 0 setup/collection errors, exit 1**. The original overlay creates `tests/test_frontend.py`; its absence before overlay is expected. JUnit, dependency versions, source paths and cleanup were captured. The GPU host repeated this admission before model startup. See [CPU_ENVIRONMENT_ADMISSION.md](CPU_ENVIRONMENT_ADMISSION.md).

## Actual GPU and request gates

The frozen coordinator's torch assertion checked four GPUs whose names contain L4 before starting TP4; a separate device inventory file was not saved. The immutable model's eight file hashes, 41 model-wheel hashes and 124 task-wheel hashes matched registration. The pinned Linux image, native Verifier, tool definitions and candidate YAMLs were unchanged.

Startup health/models/tokenize, one actual `READY` generation, tokenizer/usage equality, context admission and deliberate oversize rejection passed. Startup inference used its separately registered no-thinking, 16-output readiness request: 16 prompt + 2 completion tokens, 4.293 seconds. It is not an Agent run. Native vLLM configuration records context 32768, bfloat16 and TP4.

Every actual Agent/ADK-summary request was checked directly: 31B QAT v2 route, `max_completion_tokens=16384`, `thinking_token_budget=4096`, `seed=17`, `chat_template_kwargs.enable_thinking=true`; sampling and include_thoughts omitted. Both frozen full system Prompts were present in the first wire request. No external decision controller or extra tool was supplied. All admitted requests respected 32768 with 1024 safety reserve; maximum observed input was EGV 9428 / Control 8875. No claim that hidden reasoning-token counts were independently measured is made.

## Paired outcomes and costs

| Endpoint | EGV | Control |
|---|---:|---:|
| Official resolved | false | false |
| Native Phase 2 | 18 passed, 42 failed, 0 errors | 1 collection error, no test bodies run |
| Official test_exit_code | 1 | 2 |
| Attribution | ordinary test-call failure | Agent-introduced SyntaxError |
| Agent elapsed seconds | 300.011 | 300.014 |
| Worker elapsed seconds | 330.116 | 328.582 |
| Native Phase 2 command seconds | 2.429 | 1.516 |
| Official LLM calls | 27 | 47 |
| Official tool calls | 27 | 47 |
| HTTP dispatches / responses / known cancellations | 30 / 29 / 1 | 51 / 50 / 1 |
| Received prompt tokens | 167878 | 272184 |
| Received completion tokens | 9263 | 9510 |
| Received total tokens | 177141 | 281694 |
| Complete token accounting | no | no |
| Relevant asserted target-check runs | 4, including 1 redundant rerun | 0 |
| Informative target-check runs | 3 | 0 |
| Non-target, print-only behavioral probes | 0 | 2, one duplicates the first |
| Unchanged behavioral reruns | 1 | 1 |
| Observed correction after counterevidence | yes, html=True after 404 | none |
| Existing old-behavior test execution | none | none |
| First successful production diff returned | 160.085s | 268.316s, syntactically invalid |
| First retained change passing local target checks | final change 234.755s; checks finish 238.160s | none |
| First stable whole-task repair | not attained | not attained |
| Native fallback Patch | 1223 bytes, 2 production files | 2881 bytes, 2 production files + repro_mount.py |
| Explicit submit_patch | no | no |
| Final evidence / cleanup / idle admission | passed | passed |

Counts are command-level, not individual assertions. EGV's three self-authored tests all passed after its correction; they do not establish full task correctness. The native official `status=SUCCESS` means the Harness returned, not that resolved=true. Official `total_tokens=0` and cost_usd=0 are preserved unchanged and are not interpreted as real zero usage/cost.

EGV used 20 fewer tools and 37.12% fewer **received-response** total tokens. Both have one cancelled request with unreceived usage=null, so actual total token savings are unknown. Both spent the complete Agent time allowance; EGV's worker was 1.534 seconds longer. Runtime is not reduced merely because fewer calls were made.

The platform log's final timestamp is 1248.560 seconds (20.81 minutes). Four admitted GPUs × platform runtime gives **1.387 device-hours** as an allocation proxy, including setup, model loading, both arms, cleanup and export, excluding queue time. This is not billing, pure inference time or a reserved-budget estimate. Model/startup preparation is shared and cannot be honestly assigned entirely to either arm. CPU platform runtimes are separately preserved in [CPU_platform_costs.json](CPU_platform_costs.json).

## Mechanism evidence and limitations

The initial review hid candidate labels, model reasoning and final official outcomes. [FIRST_PASS_SEALED.json](analysis/FIRST_PASS_SEALED.json) and its SHA were written before revealing the mapping; X was Control, Y was EGV. This is a same-reviewer label-masked audit, **not an independent blind evaluation**. The reviewer knew the protocol and behavior may reveal identity.

EGV authored real TestClient HTTP status/content assertions. Its second execution reached its new frontend implementation and returned 404 instead of 200. It changed both implementations to `StaticFiles(..., html=True)` and the next execution passed all three checks. That action/result/edit/action chain supports actual counterevidence-driven correction; it is not inferred from model self-report. Control's two successful commands merely print inherited `mount` capability; they never call the requested frontend interface or request assets. Its final escaped docstring edits introduced a SyntaxError, with no subsequent execution to detect it.

EGV did not consistently follow its rule: it reran unchanged passing tests once, never explicitly established import provenance in its own commands, did not run existing regressions, and timed out without diff review or explicit submission. The passive researcher audit confirms actual workspace FastAPI source for its local checks, with changed applications/routing hashes after edits. Import execution alone does not prove target reach; the HTTP assertions and 404-to-200 change provide the additional behavior evidence.

The raw import-verdict aggregate says `outside_workspace` because deliberately observed third-party httpx/pydantic/starlette/pytest modules are installed outside the repository. Per-module FastAPI entries and source hashes show workspace imports. This aggregate must not be mistaken for proof of wrong FastAPI imports. Raw evidence was retained unchanged; the join is in [PROBE_PROVENANCE.json](analysis/PROBE_PROVENANCE.json).

EGV's final native failures include unsupported fallback argument, absent route-group/low-priority handling, route precedence, tutorial files and related cases. A partial route expecting 405 receives 404, illustrating a routing compatibility gap. Neither arm executed an existing old-behavior regression. The supplied Issue is chiefly a short feature title/PR template; it does not spell out every evaluator API/internal requirement. These post-run evaluator details establish incomplete correctness, not proof that the Agent consciously ignored explicit Issue requirements. No evaluator findings were provided to either Agent.

## HTTP lifecycle, evidence and cleanup

Both native Agent deadlines are fully observed. EGV's last request `eaf94082cfd7402d80b95b757261dc9b` is cancelled at monotonic 1086.034s, deadline cutoff 1086.043s. Control's `83c3628d97294342812cc0b29fc6b62f` is cancelled at 1418.370s, cutoff 1418.378s. Both record actual CancelledError, terminal_status=cancelled, usage=null/partial; it is not a fabricated response. EGV's cancelled request is an ADK conversation-summary request; Control's is an Agent generation request. There are three summary requests per arm (EGV two responses + one cancellation; Control three responses). These explain why wire counts exceed native Agent LLM counts.

`http_observer_summary.json` is the provisional pre-boundary summary and records unexplained cancellation. It remains immutable. The final `research_audit.json` recomputes the same lifecycle with native deadline + cleanup evidence and correctly marks the cancellations explained. [NATIVE_VERIFIER_REPLAY.json](analysis/NATIVE_VERIFIER_REPLAY.json) independently replays the original file-based classification; the original XML and stdout/exit codes agree.

Both Agent and Verifier sandboxes have start/stop pairs, final process trees stopped, cleanup_complete=true and three consecutive server zero-running/zero-waiting samples. Exported backend logs also contain idle samples. **No request-specific server abort acknowledgement was obtained**; global idle is the preregistered reclamation criterion, not proof of a particular abort message. The server's final observed PID set was empty after shutdown.

Control's collection error is an algorithm failure, not an unexplained environment failure: clean baseline collected all 60 tests; the real JUnit traceback points at its changed applications.py line 1367 and invalid literal escaped quotes. Changed-source SHA and native Patch corroborate the cause. The final classifier marks agent_regression and does not trigger an infrastructure STOP. Both arms are confirmed failures, not unknown/not_run; all primary native evidence exists.

## Integrity and source identity qualification

Raw GPU ZIP SHA: `fdb36179f46921b4d61362c2ecb406afb8167e8decfdfa6b44b60930347a73c5`, 3316169 bytes, CRC and all 501 manifest files checked. Both nested run ZIPs and their manifests also passed. See [collection.json](results/gpu/collection.json), [EVIDENCE_SHA256.json](EVIDENCE_SHA256.json), [POST_EXECUTION_INTEGRITY.json](POST_EXECUTION_INTEGRITY.json).

The supplied archive's Git HEAD is b51861d3…, whereas task metadata base is f1d750fd…. The base object is absent locally; Git HEAD alone cannot attest task source identity. A supplemental read-only exact-upstream-base byte comparison confirms **all 48 FastAPI production Python files plus pyproject.toml (49 files)** match registered f1d750fd… bytes. Initial GitHub Tree API rate limiting and two raw-file transport failures are preserved; the two later read-only retries matched. No reference repair was fetched and nothing from this audit entered Agent input. This confirms that package/config scope, not the entire repository against Git history; exact full snapshot SHA remains the primary task-input identity. See [SOURCE_IDENTITY_AUDIT.md](SOURCE_IDENTITY_AUDIT.md).

All 4159 preexisting tracked files, all frozen candidate ZIPs/Prompts, old STOPs and original evidence remain unchanged. The preregistered Notebook/protocol and all 154 accepted execution source files also remain unchanged. Only this new study's results and offline analysis were added.

## Decision

There is a useful **local mechanism signal**, lower observed response-token volume, and a runnable partial repair relative to an invalid Control Patch. There is **no resolved improvement**, no reduced Agent wall time, no demonstrated retention of old behavior, and no population estimate. Hold EGV V0.1 as frozen research evidence; **do not promote it to S0, submit to Kaggle, or automatically launch multi-task confirmation**. A future separately authorized confirmation would need unseen tasks, balanced order, fixed budgets and primary resolved/old-behavior endpoints. Detailed questions Q1–Q7 are answered in [CANDIDATE_DECISION.md](CANDIDATE_DECISION.md).
