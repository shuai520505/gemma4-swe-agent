# Decision: opt-in deterministic evidence skill

| Criterion | A: state controller | B: deterministic verifier | C: diagnosis/implementation/verification Agents |
|---|---|---|---|
| Compliant path | Advisory YAML possible; arbitrary host callback unavailable | Official SkillToolset + sandbox executor | Built-in workflow/AgentTool permitted |
| Real control | Cannot hard-gate six tools from submission | Hard-gates its own verdict, re-execution and local timeout; global tools unaffected | Enforces sequencing, not evidence correctness |
| Extra inference | Potential repeated state turns | No inference inside mechanism; invocation/skill loading can require model turns | Extra agent turns and handoffs |
| Latency | Unknown; state bureaucracy risk | Git hashing + one bounded scratch check | Higher/unknown, transfers/history cost |
| Complexity/recovery | Unsupported callbacks would require organizer change | One standalone stdlib script, UNKNOWN on unavailable evidence | Multiple contexts and coordination failures |
| Expected repair pathway | Redirect diagnosis, but unsupported hard transitions | Reject weak/stale success evidence and avoid unchanged repeated checks | Separate roles, with no demonstrated value under300s |
| CPU testability | Advisory state not sufficient | Actual process, file identity, assertions and timeouts independently observable | Possible, but disproportionate first prototype |

Select B only. No custom state controller is smuggled into a research Runner. DIAGNOSE/HYPOTHESIZE/REPAIR/VERIFY/SUBMIT may describe progress, but are not enforced global states. No extra Agent, model, summarizer, dynamic budget, compression, or output truncation factor is added.

SUPPORTED = this selected scratch script completed with at least one evaluated structurally nonconstant assertion, no observed failing assertion, and unchanged hashed workspace/check bytes. CONTRADICTED = the proposed local success claim is contradicted by script failure; ImportError is an execution error, not evidence the Issue is unsolved. UNKNOWN = absent/unexecuted/trivial assertions, identity problems, mutation during checking, timeout, etc. OBSERVED = cached prior same-tree/check evidence; zero new subprocesses, never upgraded to fresh support. None proves semantic relevance or Native Resolved.

A remains byte-identical EGR. B/C share EGR prompt, agent/eval configs, skill metadata and tools. Only their scripts differ. C returns UNKNOWN plus the same procedural guidance and executes no reproducer. Main causal contrast B/C is executable evidence versus advisory control; A/B compares the entire deployable mechanism package and includes official Skill interface/instruction overhead. Report both; do not call A/B a pure instruction-invariant effect.

Limits: Agent can bypass the optional skill, forge scratch state, choose a tautology with a variable, or test a wrong hypothesis. The mechanism is not an adversarial attestation boundary. The native evaluator remains the only repair endpoint. A hard global submission gate would require an organizer-supported callback/registry; no such interface is assumed.
