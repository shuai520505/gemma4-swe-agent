# Evaluation admission finding

CPU_VERIFIED: `audit_native_matcher.py` executes the unchanged validation functions extracted from the frozen official swegemma 0.2.11 source (SHA256 recorded in NATIVE_MATCHER_AUDIT.json). A required passing `test_vectorize_dask_dtype` plus an intentionally skipped sibling `test_vectorize_dask_dtype_meta` is rejected. Renaming only the unrelated skipped sibling makes the same validator accept the fixture. This fixture tests evaluator behavior, not a repair.

REAL CPU TASK OBSERVATION: attempt 4's unchanged xarray JUnit contains the matching required passing test and the upstream intentionally skipped `_meta` sibling. The official implementation matches a required base name to names starting with that name followed by `_` or `[`, then treats any such skipped match as a required failure. The source is in `swegemma/harness/verification.py`, `_node_matches_requirement` and `_validate_junit_xml`.

This is a prospective trust blocker for the registered primary endpoint. A correct Agent patch may receive a false-negative SDK verdict or tempt the Agent to remove a legal upstream skip. Neither outcome measures the intended repair quality reliably. All task IDs, test patches, expected results and SDK code remain unchanged. No reference repair has been accessed. No task replacement is permitted.

Do not dispatch the eight real-model sessions under a known-invalid primary evaluator. Preserve this finding and finish environment/wiring diagnostics on CPU. A separate prospective evaluation amendment would have to retain raw official SDK results, label any independently corrected exact-node verdict as an independent endpoint, and validate it without reading a reference repair. Do not silently turn that corrected verdict into official Native Resolved, modify trusted tests, or spend GPU merely to discover this known failure again.

The user's GPU authorization remains valid. This is an evaluation-integrity gate, not a request to repeat authorization. Candidate A currently has no measured real-Gemma benefit.
