# EGRD V0.3.1.1 CPU Runner recovery

**EGRD_V0311_CPU_READY_GPU_NOT_AUTHORIZED**

Private CPU Notebook [141087018/v1](https://www.kaggle.com/code/wudangdexiaodoashi/egrd-v0311-cpu-runner-recovery)
completed once. All 17 mandatory engineering gates pass on this new execution.
No PR39 partial result is substituted for an unobserved new-run gate.

Both unchanged S0 arms compile, invoke the original six tools, submit an inert
398-byte production-comment patch and apply it to independent trusted base trees.
Both post-edit probes still fail the original target assertion, while all three
positive controls and the bounded regression pass. This is the intended negative
repair control. It demonstrates a functioning submission/evaluation pathway,
**not** better repair intelligence or Native Resolved.

The only task-input difference is the original B-only failure observation. Actual
initial HTTP requests are captured and compared; full private bodies are not
committed. S0/Issue/receipt/N/D/MEER/Verifier/historical bytes are unchanged.

## Evidence and implementation

- `CPU_RUNNER_RESULTS.json` and its schema: all gates, actual SDK/counter results.
- `DEVICE_ACCEPTANCE.md`, `GIT_SUBMISSION_ACCEPTANCE.md`: actual kernel/native tools.
- `AB_MODEL_BOUNDARY_AUDIT.md`: captured input difference and unknown token cost.
- `TRUSTED_POST_EDIT_RESULTS.json`, `ISOLATION_AND_CLEANUP.md`: negative patch and confinement.
- `S0_CONFIGURATION_RECONCILIATION.md`: package, Compiler and serving distinctions.
- `KAGGLE_CPU_EXECUTION_RECORD.json`, `RAW_ARCHIVES.json`: one dispatch and verified private archive.
- `FINAL_DECISION.md`: all required answers and the remaining GPU authorization boundary.

`device_gate.py` uses PR39's original `install_null_device`, before installation
or Agent work. `sandbox_adapter.py` reuses its adapter and original confinement,
adding child device/Git checks and journal-owned lease cleanup. `lifecycle.py`
also guarantees transport shutdown if manager cleanup raises. The isolated
orchestrator/evaluator copies retain the prior official call path, adding durable
HTTP capture, actual-boundary comparison and comment-patch negative controls.
No trusted Runner, tool, Compiler, evaluator or candidate is monkey-patched.
These are research-host changes, not deployable new Agent capabilities.

## Offline reproduction

With the existing controlled evidence files available:

```text
python -m unittest egrd.v0311.test_recovery -v
python -m egrd.v0311.collect
python -m egrd.v0311.audit
git diff --check
```

The sealed CPU source payload remains private and immutable. `CPU_BUILD.json`
binds every member. Test/report code added after sealing does not change runtime
members. Notebook building fails if the output directory already exists; the
exclusive dispatch record prohibits a second push. No corrective CPU execution
or GPU execution is covered by the consumed one-run grant.

The historical 141014201/v1 and v2 ERROR archives remain unchanged. The new raw ZIP
download initially failed with IncompleteRead; read-only byte-range recovery
obtained the complete archive, verified CRC, all 353 evidence-manifest files and
the uploaded source identities. No Notebook was re-executed for download recovery.

Final offline acceptance: **50 tests pass, zero failures/errors/skips**, including
actual-archive provenance and schema negatives that reject a false ready gate or
invented Native Resolved. Two historical branch-specific diff-scope assertions
are explicitly replaced by the new namespace/history assertion; original tests
and their evidence are not edited. Local simulation and live CPU evidence remain
separately labeled in OFFLINE_VALIDATION.json and CPU_RUNNER_RESULTS.json.
