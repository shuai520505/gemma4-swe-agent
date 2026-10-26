# COMPILER_FULL_PASS

Evidence: **140992640/v1 COMPLETE**, exact payload
`57104c6618b40e8ea5b440681b2fcf9b795a49a83269ea81cfd11ed607ea1cea`.
Original output archive SHA256:
`c5e2b029e5b167529d8056847ba3fd94a07a1c3d182a13b673803161833c7db7`.
Size 1,096,826 bytes; ZIP CRC and 202 uploaded source-member hashes verified.

## Actual SDK execution

Each exact N/D ZIP was extracted separately, validated through the real strict
official package validator and compiled using actual compile_submission,
ModelRegistry, SwegemmaContext and the full pinned Google ADK. Empty-state
compilation accepted one LlmAgent, six official tools and the original
SkillToolset. Instruction hashes matched the extracted candidate, generation
was identical (16384 output, seed 17, thinking 4096), and include_thoughts was
left omitted. No custom callback registry, callback or Compiler/Runner replacement was
installed. Native Runner compilation supplied the official sandbox executor.

The unchanged official single-Agent Runner ran independently for N and D,
using the accepted research chroot adapter. Real tool events show all six native
tools and direct run_skill_script calls, with no list_skills/load_skill/resource
call. The original frozen verifier bytes ran in the sandbox. The toy source
was genuinely edited, locally asserted, exported and explicitly submitted.
Unmodified native verify_task on the trusted side produced TaskResult resolved
true and JUnit **1 passed, 0 failures, 0 errors**, for each owned synthetic task.
This is synthetic engineering evidence, never a new admitted competition task.

| Arm | Scripted HTTP requests | Skill calls | Official charged calls | Worker seconds | Cleanup |
| --- | ---: | ---: | ---: | ---: | --- |
| N | 22 | 14 | 17 | 23.9081 | complete |
| D | 22 | 14 | 17 | 17.3847 | complete |

Skill calls and charged calls are separate recorded counters; no new accounting
rule is inferred. Timing differences between these scripted sessions are not
evidence of Prompt efficiency. Native results/JUnit/patch/transport cleanup
hashes and safe receipts are in CPU_TEST_RESULTS; complete traces stay private.

## Negative and source-bound checks, each arm

Fourteen real Skill calls cover: missing tool fields, invalid script, missing
CLI --check, absent probe, invalid workspace, assertion-free probe, missing
dependency, malformed Python, unrelated exception, timeout, large output,
target assertion before edit, after edit, and repeated unchanged assertion.

- Missing fields/script return the official SDK errors.
- Missing/invalid files or vacuous checks return UNKNOWN.
- Dependency/SyntaxError/ValueError return local CONTRADICTED, which is **not**
  proof of an Issue defect or useful reproduction.
- A bounded timeout returns UNKNOWN and execution continues; large output
  produces a compact receipt. The original implementation spools raw output:
  this does **not** establish a hard disk-byte quota.
- The target assertion fails before the edit and passes after it, with different
  source identities. The unchanged repeat is OBSERVED with zero child executions.
- Skill receipts retain semantic_correctness=UNKNOWN and native_resolved=null.
- Worker/chroot roots and scripted HTTP transport clean up successfully.

## Scripted boundary and limits

**CPU_MODEL=SCRIPTED_ONLY**. Model actions and HTTP responses are deterministic
owned fixtures; all **44** HTTP requests are to that fixture, **0** to Gemma.
Synthetic token usage in those responses is not real model cost and is not
reported as such. This validates actual SDK execution, error recovery and
isolated filesystem/tool behavior; it does not show voluntary Skill adoption,
Issue relevance on an unseen task, semantic repair superiority or GPU readiness.
No separate external SWE-bench baseline, mandatory invocation hook or formal
competition scoring path was exercised.
