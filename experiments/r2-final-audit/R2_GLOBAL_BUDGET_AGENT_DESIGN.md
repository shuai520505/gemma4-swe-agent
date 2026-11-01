# Global budget-aware Agent: design only

STATIC_ANALYSIS / OFFICIAL_RULE: the submission is declarative YAML compiled by the official Harness. It is not a Python controller entrypoint. get_status reports the current session's elapsed/remaining time, charged calls, patch status, turns cap and command timeout. It does not expose a verified all-task timer, completed-task count, future task order or tasks remaining. A fresh session context is created per task. Cross-task storage access outside the sandbox is not a permitted solution.

| Capability | Current status | Deployable conclusion |
|---|---|---|
| Read local time/call budget with get_status | Official existing tool; CPU schema and real trace available | Can guide the current Issue only |
| Static per-task max_time_minutes/calls/turns | Official eval_config keys, environment overrides can take precedence | Can set one pre-reviewed cap for all tasks |
| Return a patch early | Official submit_patch | Current task can stop before its cap |
| Bound an individual command | Official run_command clamps timeout to local remaining time | Cannot assume a tool timeout argument not present in its schema |
| Know exact hidden N/order/global remaining time | UNKNOWN / no official Agent-visible contract located | Do not insert invented values into prompts |
| Dynamic per-task host allocation using remaining global time and remaining tasks | Theoretically useful; no submission-callable interface verified | Not deployable as a competitor controller today |
| A trustworthy task-global timer in an organizer callback | Would require an organizer-supported interface | Proposal/dependency, not available implementation |

## Policy that existing interfaces could support

Before any implementation, freeze a static conservative per-task cap using a declared N sensitivity and setup allowance. Keep R2 as the unmodified control. A future single-factor budget treatment may change only the cap while leaving prompt, model, schemas, tools, sampling, thinking, caching and LoRA unchanged. The inherited prompt's literal 28-call/eight-minute assertions would conflict with a shorter cap; resolving that conflict is a separate strategy/configuration treatment and must not be smuggled into a cap-only experiment.

Within a session, existing get_status can provide a local stopping signal. A proposed stopping policy would reserve time for one focused validation and explicit submission, stop broad exploration after a plausible production fix exists, and compare one next operation's bounded cost against the local reserve. Confidence should be grounded in Issue behavior, a relevant production diff and observed targeted checks; no inaccessible hidden tests or arbitrary numeric confidence should be invented. An easy task should finish early; a hard task should preserve a justified partial patch before local expiry instead of using every call. A low call count does not mean ample time, and spare time does not mean tools remain: both constraints must be checked. This is a design, not an implemented or tested improvement.

If the organizer later exposes trustworthy G seconds and R tasks remaining, a host-side policy could allocate min(local cap, (G-final reserve-estimated future setup)/R), with conservative cost estimates and a minimum useful repair window. Only an organizer-wired callback could apply this across tasks. Reading wall-clock time from run_command gives a timestamp but no verified scorer start or future task count; it cannot reconstruct a global budget by itself. Local warning text and process uptime must not be mistaken for global time.

## Pre-registered experiment proposal, not an execution request

Primary question: does a budget treatment improve independently validated repairs per 12-hour generation window without infrastructure/trust failures? Experimental units are task-seed sessions; global coverage is assessed at complete-batch level. Repeated calls within a session are not replicates. Do not estimate hidden success from R12's three selected tasks.

After separate authorization, freeze a development holdout before viewing any candidate outcomes, stratified by repository and Issue type. R12 remains an explanatory pilot and is excluded from confirmatory success estimates. Use paired task/seed runs for frozen R2 and one proposed budget treatment, randomize/counterbalance order within repository/batch, and freeze the full schedule and package hashes before inference. If multiple caps or prompts are screened, record the whole family and select only on a separate development partition; retain an untouched confirmation set. No holdout selection or new Agent is performed in this audit.

Measure actual officially scoped setup, model and generation time separately from validation. Primary endpoint combines target checks, controls, real production changes and independent semantic review. Secondary endpoints: coverage, valid explicit submission, first/last production edit, get_status adherence, wasted/repeated calls, malformed edits, timeout fallback, token usage completeness and per-task tail cost. Count ordinary repair failures; stop on predefined infrastructure, isolation, control, evidence or cleanup failures; never selectively rerun. In a proposal, preregister batch budget and stopping rules before data collection, including how incomplete batches enter analysis.

Advancement requires no trusted-check regressions, no hidden-data access, compiler acceptance, valid packaging and better batch-level repair yield under the same budget. Report paired outcomes and uncertainty; three tasks do not support a significance claim or a 0.50 leaderboard forecast. Exact N and the global clock's official charge boundary should be clarified before a full-run coverage guarantee. No R3, Controller code, Notebook, model inference or submission is produced here.
