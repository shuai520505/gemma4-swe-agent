# S2-EGV-AgentTool-V0.1

This is a declarative Main Coding Agent plus one official ADK AgentTool, egv_verifier, using the same Gemma4 31B QAT variant. It is not an external multi-agent controller. The candidate ZIP contains only five YAML/Markdown files. All Python, test fixtures, analysis, native Phase2 observations and experiment preparation live outside it.

Main retains the original S0 repair workflow with a minimal delegation-policy replacement and an added division of responsibility. It alone edits production code and submits. EGV receives an explicit Issue/hypothesis/path/diff-summary/question request; it reads current workspace code, executes assertions and relevant old-behavior checks, and returns scoped evidence. Main must act on real counterevidence and retest after revision. Full103-word S1-EGV instructions are not duplicated on both roles.

Main has the six existing official tools plus the declared AgentTool schema, **seven exposed schemas total**. The child has only get_status/read_file/run_command. There is no additional execution-tool implementation. Shell still permits writes; this is auditable but not enforced read-only isolation. The synthetic negative tests deliberately demonstrate that limitation.

AgentTool creates a fresh internal ADK Runner/session for each invocation, copies non-internal parent state and forwards state deltas back. It does not automatically copy the entire parent conversation. Both roles bind the same organizer tool functions to one SwegemmaContext and workspace; a new child session does not allocate fresh tool/time budget. output_key stores the latest verifier report in parent state. The return value is the final non-thought text, not the child's complete raw tool transcript.

`skip_summarization: false` permits the parent to consume the report and continue its repair loop. The actual CPU skip=true control ends the direct Runner invocation before Main repairs or submits; the native outer Harness may subsequently nudge, so this observation is not claimed as an absolute prohibition on continuation. No separate summarizer agent is added. Normal Main continuation and native ADK compaction still incur model/time cost.

Both agents use output16384/thinking4096/seed17 with omitted sampling/include_thoughts. The shared operational limits are300s,60 organizer-counted tools and120s per command. The60s/8 remaining-tool delegation reserve is an unoptimized heuristic. Scripted CPU tests prove the route can close and submit near the deadline; they do not prove autonomous Gemma follows it or that those thresholds are optimal.

The independent research worker preserves the native evaluator, context admission, original JUnit capture, Patch persistence, timeout and process cleanup. Its changes are the legitimate two-agent admission predicate and passive nested Runner logging; [WORKER_DIFF.md](WORKER_DIFF.md) gives the exact diff. No researcher chooses runtime repair actions. Role-specific decisions remain with the submitted declarative agents.

CPU model responses are scripted through mocked HTTP while file edits, tests, tool functions, feedback delivery, state updates and submission are real. This establishes API/execution feasibility, not Gemma cooperation or repaired public tasks. Full GPU inference and eight-task outcomes are not authorized by this development request.
