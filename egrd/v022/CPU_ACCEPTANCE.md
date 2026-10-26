# FULL_COMPILER_CPU_ACCEPTANCE_NOT_RUN

Candidate integrity PASS is separate from full CPU acceptance, which is NOT_RUN.
No actual Gemma, new ADK Agent session, native task baseline or Native Verifier
run is claimed. CPU_MODEL=SCRIPTED_ONLY for the owned tool-call fixtures.

## Actual executed checks

14 new local tests pass (76.061 seconds); 38 inherited source/interface/context
regressions pass (2.667 seconds). These are 52 offline tests, not 52 Agent trials.
The new tests run complete original strict Pydantic schema validation, YAML
include resolution and exact original Skill routing/wrapper method bodies.
An explicit owned local executor runs the **unchanged frozen verifier bytes**
in a subprocess, with Windows temporary workspace/probe paths substituted in
valid CLI args. No official Google/Runner module is monkey-patched.

Covered: valid direct call without list/load; missing tool/CLI args; wrong
Skill/script; invalid workspace; absent probe; assertion-free/constant probe;
targeted pass; failed assertion; missing import; SyntaxError; unrelated exception;
source change invalidation/unchanged repeat; timeout/per-check budget rejection;
compact response despite >64 KiB diagnostic output; exact N/D Skill/config
equality; no extra Agent/controller; reproducible ZIP/member hashes and original
Prompt recovery. Native results remain null in local receipts.

Important negative behavior is retained: original CONTRADICTED includes import
and setup exceptions, not only target assertions. Relevance needs separate
Issue review. Large raw output is spooled before tail parsing; no hard raw-disk
cap is proven. POSIX descendant/chroot/resource-accounting behavior is NOT_RUN
here. Owned outer executor timeout is a fixture bound, not the official sandbox.

## Why full Compiler acceptance did not run

The three pinned SDK modules are not installed locally. The five retained SDK
wheels alone are not a complete dependency environment. COMPILER_AVAILABILITY
checks declared dependency metadata against installed versions/cached wheels:
38 direct dependency edges are unsatisfied. This records availability, not a
claim that every missing cloud integration would be imported by a compile.

Two no-index **dry runs**, not installations, were attempted. The first hit a
Windows writability-probe error before resolving dependencies. A clean-target
dry run then lacked a cached PyYAML wheel (system PyYAML itself is installed).
An independent metadata audit establishes the broader missing closure beyond
that clean-target strategy. Failure logs are retained privately by SHA in
PREPARATION_RECORDS. No global package was installed/upgraded and no replacement
SDK or Notebook workaround was used.

Accordingly no real compile_submission return, actual new SkillToolset instance,
full Runner initialization, native tool accounting or new TaskResult/JUnit is
reported as PASS. Schema and source-fragment checks cannot fill that gate.
Before any GPU readiness claim, restore a verified pinned isolated runtime and
run both exact ZIPs through the complete official CPU chain with cleanup.
