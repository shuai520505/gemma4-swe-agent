# Official Linux CPU admission

The accepted final payload is CPU02, Kaggle kernel
`wudangdexiaodoashi/gemma4-s1-e3-struct04-cpu02`, version1, COMPLETE.
It actually ran **113/113**, zero failures/errors/skips: the existing100
Compiler/empty-state ADK Runner/HTTP/deadline/context/Patch/cleanup tests plus
13 new native Pytest/file-capture/audit regressions. This is infrastructure
validation, not Gemma inference or an algorithm repair result.

Versions: swegemma0.2.11,adk-submission0.2.13,adk-eval-core0.1.0,
google-adk1.36.1,google-genai2.11.0,litellm1.82.4,psutil5.9.5.

CPU02 raw ZIP SHA256:
`4544268279c041b9f8ba9646cba1a875fb363bae856395212d75547a12138b9d`.
CRC and715 manifest entries verified. Original stdout/stderr, TaskResult,
JUnit, capture metadata, test inputs and cleanup records are retained under
results/cpu02 and in the byte-preserved raw archive.

## Executed regression evidence

| Requirement | Actual result |
|---|---|
| A: frozen Rich19passed4failed with error-word test data | assertion_failure; no infrastructure stop |
| B: frozen Requests194fixture errors | setup_error; verified historical clean provider/call-chain blocker; not confirmed Agent failure |
| C: native Pytest pass | original JUnit copied before stop; identical bytes survive sandbox cleanup |
| D: assertion plus setup | both events retained; unknown attribution blocks, not automatically external |
| E: actual collection/internal/executor error | separate categories; stop |
| F: ERROR/ModuleNotFoundError/Found4errors in data/stdout | cannot independently trigger environment failure |
| G: missing/corrupt/conflicting XML | fail closed, even if stdout claims a pass |
| Changed production source causing parser error | real traceback plus baseline/current SHA support Agent regression attribution |

Historical failure XML was not saved by the old SDK integration. A/B therefore
use exact-SHA-attested read-only nonzero replay of native counts and generated
failure/setup sections. This cannot synthesize a pass or admit a prospective
run. All new runs require the original XML. The same production file API
`s1.verifier_v3.audit.audit_verifier` is used in tests, replay and GPU audit.

## Selected clean task

The preregistered deterministic rule selected rich_3130 before evaluating it.
The unchanged native verifier ran on the unrepaired base with only its original
evaluator test patch: **1passed,5assertion failures,0errors**, exit1. This is a
valid environment baseline, not a model result. Exact snapshot, Issue, test
overlay and record hashes are in protocol.json/task_inputs. No reference repair
was inspected or provided. The native command already requests JUnit; the new
manager copies those exact bytes before native sandbox stop, without changing
the command, tests or scoring. Import provenance and production-source hashes
were captured. The GPU host must repeat this environment admission.

CPU01 also completed113/113 with the same classifier, capture and tests. Its
raw SHA is8b8a2b49ce6c83d395d69282795b94ba42c8f03f7dea8ce9010772b3352fb9f4.
It revealed a metadata admission-count mismatch (13 actual tests versus14
planned). CPU02 registers the actual source-declared13 and verifies the executed
count; no classifier/test/candidate changes were made for this adjustment.
Both preparations remain preserved; CPU02 alone admits the final GPU payload.

All2478 parent-tracked files matched their pre-execution byte hashes before
registration. Both frozen candidate archives and members were rechecked.
The GPU builder requires exact equality between the accepted CPU02 source map
and the GPU embedded payload. No claim of GPU startup is made by this CPU gate.
