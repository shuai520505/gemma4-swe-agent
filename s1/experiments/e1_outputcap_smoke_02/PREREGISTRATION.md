# S1 E1 output-cap smoke 02

This is a new experiment, `s1-e1-outputcap-smoke-02`. The prior
`s1-e1-public-01` is permanently stopped and its artifacts are immutable.
The machine-readable `protocol.json`, registered source map, CPU gate and
Notebook hashes are authoritative. They must be committed and pushed before
the GPU Notebook is dispatched. Dispatch itself is recorded afterward.

## Scope and frozen conditions

Exactly two sequential runs: A (`control`) then B (`e1_output8192`), both on
`requests_7328`, each in a fresh official sandbox and worker process. The
original Issue and base snapshot are identical. No task-specific Prompt,
reference answer, hidden test, prior Patch or reasoning is supplied to either
Agent. The official evaluator alone receives the evaluation tests.

Both use the previously frozen S0 Prompt, official Gemma 4 31B QAT version 2,
4 L4 GPUs, six official tools, one Agent, 300 seconds of Agent time, 60 tool
calls, 120-second command timeout, thinking budget 4096 and seed 17.
`include_thoughts`, temperature, top-p and top-k remain omitted. A reserves
16384 output tokens per request; B reserves 8192. Thinking is included in this
allowance. Context is 32768 with 1024 safety tokens. r04 compaction and full
Issue preservation remain unchanged. Each official Phase 2 has 300 seconds.
Full per-run outer deadline is 1350 seconds, not an additional Agent budget.

## Execution and CPU gate

The exact 80-file r04 CPU-tested source set is reused byte for byte, including
its full Runner tests and worker, context, cancellation, Patch persistence and
cleanup regressions. Six additional Linux tests exercise only a passive
startup observer. The observer calls the original, unmodified
`s1.preflight.check_model` with its explicit `tools=None` through the real
official LiteLLM client. It does not add an Agent tool or change A/B behavior.
No GPU execution is allowed unless all 77 official-stack CPU tests pass.

The startup observer persists health/models requests, full generation
request/response and actual usage, both tokenizer inputs/results, successful
admissions, and failures. Nonempty real generation, model identity,
tokenizer/usage agreement and actual oversize rejection are mandatory.
Startup generation has thinking disabled and output cap 16; it is metered
separately and is not an A/B task call.

The Notebook clock starts in setup, before extraction, wheel installation and
model hashing. r04 checks the remaining complete-task slot plus 900 seconds
of finalization before each task. Installation and execution share a `finally`
that bundles the evidence. Model/Wheelhouse/CPU/source/candidate/task hashes
are checked before inference.

## Stops, outcomes and evidence

Stop globally on any model or parameter drift, startup failure, context
failure, source/task hash drift, suspected hidden-data access, missing native
evidence, unverified cleanup, or insufficient complete-task time. No repair,
retry, task replacement or best-of selection is permitted within this ID.

r04's existing conservative task gate is retained: unknown outcomes, empty
Patch or incomplete actual Phase 2 stop the pair. This does not convert an
empty Patch or timeout into an official failure. Preserve raw fields and
separate normalized classifications; any unstarted arm is `not_run`.
An ordinary confirmed native test failure with complete evidence can proceed
to B. Test-collection exit 2 remains unknown pending environment audit.

Preserve full raw task HTTP, native traces, tool calls and results, errors,
Patch checkpoints/final Patch, official apply/Phase 2 output, and cleanup.
Measure real HTTP usage rather than TaskResult's placeholder token field.
Determine the first *effective* edit from a successful tool response and
content change; a failed `edit_file` call is not an effective edit. Exact
duplicate reads are counted mechanically and interpreted manually.

## Decision rule and reporting

Report A, B and B-minus-A for actual calls/tokens, Agent elapsed time, tools,
first effective edit, Patch validity, actual Phase 2, raw resolved and
submission/context/truncation behavior. Explain whether the smaller output
reservation reduced pressure, changed actions, or truncated output. Distinguish
an increased theoretical input allowance from a measured context bottleneck.

Recommend Go for a separately registered four-task screening only if startup
and both task infrastructure gates pass and raw evidence supports safe output
behavior. Unknown outcomes, unsafe truncation or missing cleanup mean No-Go
pending a new registration. This decision does not authorize launching that
screening in this turn. A single pair cannot estimate repair-rate gains or
generalization and is excluded from its future main-effect analysis.

No E2/E3/E4, CURE integration, LoRA, or leaderboard submission is authorized.
The only confirmed leaderboard score remains S0 0.13 (57261002).
