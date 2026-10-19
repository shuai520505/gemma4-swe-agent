# 500-second native shared-budget validation

Actual official Linux CPU03 runs the native organizer run_agent_sandbox, not a simulated clock. evaluation.max_time_minutes8.333333333333334 is read from the actual T500 candidate YAML and passed into official EvalConfig/EvaluationBudget. Native Runner computes minutes*60; Python evaluates the requested value as500.00000000000006 seconds. Actual observed context Agent duration: 500.0930521920001 seconds. The child HTTP request stalls after Main has already read/edited/delegated; the enclosing parent deadline cancels it. The child never receives a fresh500-second allowance. Main/child get_status records share the same context and monotonic session clock.

Five actual mock-HTTP dispatches, four replies, final terminal cancelled, usage=null/partial. Source hashes remain unchanged in a0.2-second observation after native Runner cancellation and before its own sandbox_stop deletes the workspace. Cleanup complete, zero leftover sandboxes. Native fallback Patch is preserved. This is a finite observed cancellation/stability check, not proof of every conceivable background process or real vLLM abort. No Gemma server is running in this CPU test.

Actual60-count fixture exhausts shared counted read/edit/write/run operations across roles; later child and Main calls return BudgetExceeded. Free get_status/submit/AgentTool wrappers and inference may continue within the current invocation until the shared time limit. This intentionally wrong-Patch exhaustion case is not repair success. near_deadline advances the same500-second clock to about30 seconds remaining, skips delegation and explicitly submits through real tools. That fast closure case is separate from the actual500-second native wait.

CPU02 earlier observed499.998s cancellation but its new post-return stability assertion errored because the official Runner had already deleted the Sandbox. That raw failure is retained. CPU03 fixes observer timing and passes the500s/60-count tests and six other core methods; its overall run remains ERROR due to a separate EvalConfig test constructor error. CPU04 corrects only that test and reruns it plus115 original regressions. Final acceptance is a clearly labelled composite across immutable preparations, conditional on the CPU04 gate; no9/9 single-run claim is made.

Evidence: results/cpu03/validation/cases/exact_deadline/{native_boundary.json,http_lifecycle.jsonl,result.json,post_deadline_stability.json,cleanup.json,native.patch}; exact_budget/{nested_audit.jsonl,result.json}; near_deadline/{nested_audit.jsonl,result.json}. Mock usage is not actual Gemma token consumption.


## Final accepted evidence

CPU04 corrected configuration test passed and all115 original regressions actually reran and passed. CPU03 eight core methods passed with real500.093s evidence;its overall error remains retained. CPU_FEASIBILITY.json is explicitly COMPOSITE_DISTINCT_PREPARATIONS with unchanged critical source/candidate hashes,not a single9/9 passing preparation.
