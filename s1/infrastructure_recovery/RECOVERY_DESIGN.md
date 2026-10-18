# S1 research infrastructure recovery

Version: `s1-infra-recovery-0.2.0`, independent of frozen r04/r12. All new
implementation, registrations and evidence live in this directory. No Agent
Prompt, candidate ZIP, official wheel, official test or historical STOP is edited.
No GPU, model training or leaderboard submission is part of this recovery.

## Request lifecycle and cancellation

`wire.observe_http` scopes a passive observer around the actual HTTPX send used
by the official ADK/LiteLLM stack. Each transport dispatch attempt receives a
UUID. The exact body and its SHA plus parsed JSON remain in `http_wire.jsonl`;
the same ID joins `request_sent`, `response_received`, `cancelled`, `timeout`,
`transport_error`, and one `terminal_status` in `http_lifecycle.jsonl`.
Credentials/headers are not logged. ADK event observation remains the frozen
native DurableContext implementation.

`request_sent` means handoff to the transport, not proof that a server received
bytes. The real-socket regression separately waits for server receipt before
cancelling. The official Harness regression runs actual Compiler/ADK/HTTP with
a stalled local server and the native `asyncio.timeout` deadline. No Gemma or
GPU inference is involved in those CPU tests.

Cancellation during send or body read is recorded synchronously and re-raised;
it is never converted to a response or swallowed. Transport timeouts remain
distinct. Outer asyncio deadlines legitimately appear as inner CancelledError
and outer TimeoutError. Logging failures cannot replace CancelledError; the
resulting absent evidence fails closed. SIGKILL/power loss cannot run a finally
block: such requests remain unknown, not retrospectively declared cancelled.

Unreceived usage is null, never imputed from tokenizer counts or from zero.
Only observed response usage is summed. With no observed usage the sum is
null. `usage_complete`/`partial_token_usage` distinguish completeness. A 200
response without valid usage does not pass the evidence gate.

`session.deadline_proof` reads independent native error text, registered Agent
seconds, observed elapsed time, durable Agent end event, supervisor process
cleanup and sandbox completion. A cancellation can be explained only if its
ID has exactly one cancellation and terminal, no fabricated response/usage,
and it falls within two seconds of that proven native cutoff. Duplicate,
orphan, unclosed or unexplained requests stop continuation. Other original
model/parameter/context/Patch/Phase2/cleanup checks remain in force.

This new interpretation applies only to future preregistered runs. It cannot
turn the old smoke's unclosed request into an explained cancellation or reopen
either historical STOP. Explained cancellation can complete infrastructure
evidence while still leaving token cost partial and repair outcome unknown.
Client cancellation does not prove a real vLLM backend stopped generating.
Future GPU compatibility gates still need server-side cancellation/idle evidence;
this CPU recovery does not claim to have validated GPU request reclamation.

## Source provenance without another Agent tool

The research SubprocessManager keeps the literal native class dispatch name,
normal exec timeouts and original six tools. It installs a small observer in
the isolated venv's site-packages via `.pth`, outside workspace source/tests.
Each command receives a separate host evidence directory. Startup and normal
exit record sys.path, module __file__/realpath/source SHA; Python audit `exec`
events record loaded module code filenames and code hashes. No profile hook
runs on every function call, and no target function is replaced.

Commands using `-S`, killed processes and missing exit records remain unknown.
Modules loaded outside workspace are flagged even when the script exits 0.
Module execution provenance does not prove an assertion exercised the changed
function, or that the repair is correct: `behavior_verified` remains false.
The final behavioral claim needs a relevant executed assertion separately.

The original subprocess helper skips editable installation. A scoped research
adapter runs the same `--no-index --no-build-isolation --no-deps -e` installation
flags as the native Docker helper, in the sandbox venv, and fails closed on
errors. The scoring Harness and its tests/verification commands are unchanged.
Both future arms must use this same adapter; it is not an E4-only advantage.
Import audit modules are an explicit registered infrastructure parameter.

Declared PEP 518 build requirements are resolved only from the exact official
task-wheel directory, with requirement/version/marker/platform checks. Selected
wheel SHA-256 values and sandbox-only installation output are retained. No
network fallback or transitive dependency download is allowed. CPU r05 admits
Rich using cached poetry-core and FastAPI editable import using cached
pdm-backend; this does not admit missing test targets or fixture providers.

## Environment eligibility

Requests fixture providers missing from the pinned offline inputs are not
replaced with mocks or fixtures. Independent CPU checks use a clean official
snapshot, original public test files, exact task/archive hashes, source import
proof, pytest plugin trace and a read-only fixture-lookup diagnostic plugin.
The diagnostic plugin adds no fixtures and preserves return/exception behavior.

Controller regression success and task environment eligibility are separate
gate fields. An ineligible task cannot enter a repair-rate endpoint. A passing
public baseline file is a prerequisite, not proof of equivalence to hidden
tests or to the unavailable official scoring container image.

## Research execution boundary

`worker.py` is a disposable research entry around the unchanged S1 worker. It
requires a versioned, hashed, task/base-bound positive environment admission.
`research_environment()` scopes the manager/editable adapters to that process
and restores official bindings afterward. `session.inspect_run` is called only
after the existing supervisor has verified the process tree. Budgets, context
admission, native Patch persistence and Phase2 logic remain unchanged.

This code is host research infrastructure and is absent from every Agent ZIP.
It is not a claim that a private controller is a permitted submission format.
