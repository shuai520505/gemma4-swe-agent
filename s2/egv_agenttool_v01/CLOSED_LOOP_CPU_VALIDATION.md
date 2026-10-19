# Real official CPU validation

The accepted candidate is the five-file ZIP with SHA256 `1f9345cc11362acfc19fbede48284aa934dfbe3a36fe0aa889134125fa8de807`. All CPU preparations use that same ZIP and unchanged Main/EGV Prompts. Only test compatibility, fixture initialization and passive research instrumentation changed. No Gemma inference or GPU was used.

## Complete execution path

Actual organizer Compiler → empty Session State → actual Google ADK Runner → real LiteLLM HTTP client with mocked transport → Main AgentTool call → child get_status/read_file/run_command → real failing assertion → actual report returned to Main → real production edit → real target and old-behavior assertions → diff review → actual official submit_patch.

The same repair path also runs inside native run_agent_sandbox, not only a separately constructed Runner. Empty-State and native Harness sessions are distinct tests: the native Harness legitimately initializes its problem_description state. The fixture and scripted responses contain no public task/evaluator answers and never enter submission.zip.

The native successful fixture records16 mock model dispatches (Main9, EGV7),13 raw tool events and8 organizer-counted tools. Two AgentTool wrappers, two status calls and one submit are not charged. The submitted Patch really changes app.py from always-False to n>=0. EGV first executes the n>0 intermediate version, observes a zero-boundary assertion failure, and later verifies both zero acceptance and negative rejection. CPU mock token telemetry is not Gemma token consumption.

## Required negative scenarios

| Requirement | Actual case under validation/cases | Observed/required distinction |
|---|---|---|
| Unknown report | unknown | No executed actionable counterexample; no claimed closed loop |
| Invalid child test | invalid_probe | Real SyntaxError in probe; not a production counterexample |
| Ignored feedback | ignored | Report delivered, no Main repair; no cleared counterexample |
| Revision still wrong | still_fails | Main edit occurs, real retest still fails; handled != cleared |
| New behavior breaks old | old_regression | Target passes, negative regression assertion fails; false PASS text rejected by audit |
| Child writes production | child_write | Actual Shell write changes app.py; before/after hashes detect it, no forced read-only claim |
| Unavailable child edit tool | forbidden_tool | Child schema lacks edit_file; actual Runner rejects it |
| Child command timeout | child_command_timeout | Actual command returns TimeoutExceeded using accelerated1-second fixture; candidate remains120s |
| Parent cancellation during child | cancel_child / native_native_deadline | Pending child HTTP receives CancelledError; propagation and cleanup recorded |
| Little time remains | near_deadline | Same shared clock advanced to about30s remaining; no delegation, actual direct verification and submit |
| Direct Main retest | direct_retest | One delegation, actual Main correction and successful direct retest close the loop |
| Missing usable return | lost_result | Actual empty child final text/AgentTool result; no meaningful delivered evidence credited |
| Tool exhaustion | budget / native_budget | Shared count stops at3; later charged operations return BudgetExceeded; free submit may still succeed |
| Final submit error | submit_fail | Actual official submit_patch returns GitDiffError from injected sandbox Git failure; explicit_submit=false despite successful repair retest |
| Generation drift | parameter_drift | Shared request guard rejects altered output cap before child dispatch |
| Missing usage | missing_usage | Raw usage absent remains partial/null, not zero |
| Transport error | transport_error | Actual HTTP-client exception path retained with terminal status |
| skip_summarization control | skip_true | Child finds failure; direct Runner invocation ends without Main repair/submit |

The negative tests passing means the failure was exercised and detected. It does not mean the scripted Agent behaved correctly. Mock false PASS/Complete statements are deliberately not treated as execution proof.

## Preparation history is preserved

| Preparation | Actual outcome |
|---|---|
| CPU01 | Compiler and direct Runner route worked;4 failing assertions: incorrect native App/plugin registration and incorrectly constructed injected ExecutionResult. No original115 acceptance claimed. |
| CPU02 | Those adapter defects fixed; native feedback/repair/retest worked but real submit failed because synthetic Git HEAD was unborn. One failed test assertion; original archive retained. |
| CPU03 | Valid initial Git commit restored actual submit path; one failure disproved the test's immediate-budget-stop assumption. Actual native cap remained3, free submit succeeded with wrong Patch, native error=None. |
| CPU04 | New4 test methods/23 named scenarios passed; original115 regressions actually reran and passed in a separate process in this same official Linux preparation. |

Canonical ZIPs, installed-source snapshots, full HTTP/ADK/tool/native traces, toy Patch, assertion output and cleanup records are under results/cpu01–cpu04. These are independent preparations; no failed log was overwritten or recast as a success. The toy Git metadata is retained inside raw ZIPs; duplicate extracted embedded repositories are excluded from Git indexing. Raw archive CRC/manifests remain authoritative.

CPU05 adds real Git status/diff at delegation boundaries: all6 new methods (including2 statistics methods) passed in64.335s; original115 regressions separately reran and passed. Canonical raw archive SHA256 is `59ad675f8873d61f6ba1b661335f46d22e3f88e995ba0d2d5329d658baa6b366`,2874557 bytes,1254 verified manifest files,CRC passed. CPU_FEASIBILITY.json now pins this final runtime; prior CPU04 acceptance is retained as CPU_FEASIBILITY_cpu04.json.

budget01 separately passed both exact-limit methods in314.974s. Native300-second allowance expired at300.098277893s, with5 HTTP requests/4 responses and a real child cancellation terminal; final usage=null,partial. Shared60 charged-tool boundary rejected subsequent charged operations for both roles; actual raw71 tool events/74 mock model dispatches show free operations remain possible. No completed repair is credited to that exhaustion case. Cleanup passed. Raw archive SHA256 is `1af5eae2a31dc16347c6d364eacfc9973aac4d2f7ba6c64163d75a63e846a31b`,1411557 bytes,329 verified manifest files,CRC passed.

env01 separately passed the exact research observer registration route and side-effect detector, then screened all24 preregistered clean native baselines. Twelve were eligible and8 selected under the fixed cap/order. This used CPU04 logging; final Git-boundary instrumentation was tested by CPU05/budget01. Candidate, native evaluator and prompts were unchanged. Raw env01 SHA256 is `daa7c07f13ef1cbe334130825f3ed192f39d77a162ee81ee9036a14c01124f3f`,3423025 bytes,1329 verified manifest files,CRC passed. No public-task Agent ran.

Additional research observer integration and task eligibility screening are separate CPU evidence. None of these CPU cases is a Kaggle official resolved observation, a demonstration of autonomous Gemma cooperation, or a leaderboard score.
