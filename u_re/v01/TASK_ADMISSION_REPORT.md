# CPU03 evaluator-only task admission — GPU draft blocked

Saved CPU-only Notebook wudangdexiaodoashi/gemma4-u-re-v01-cpu03 / v1 completed the inspection. Its admission gate is **false**; Notebook COMPLETE does not mean task eligibility. Zero Agent runs, zero model calls, empty agent_patch, original snapshots and native evaluator test overlays only. No reference repair was used and no candidate changed after seeing baseline results.

| Proposed task | Native clean baseline | Decision |
|---|---|---|
| fastapi_14458 |12 JUnit tests,3 ordinary assertion failures,0 errors,0 skipped; native exit1 |Eligible discriminating repair endpoint; expected unrepaired assertion failures are not infrastructure errors |
| requests_7433 |339 JUnit tests,195 setup errors,0 assertion failures,2 JUnit skipped entries (including any xfail representation); native exit1 |Blocked; not an Agent repair failure |

Evidence: results/cpu03/validation/cpu_gate.json, task_identities.json, per-task official_result.json, unchanged native Phase2 command/output, structured_verifier.json, phase2.junit.xml, phase2_junit_capture.json and cleanup/admission.json. Both JUnit files were captured before sandbox cleanup; both cleanups completed. Snapshot/base-overlay/Issue/task-record/test-overlay hashes are bound in task_identities.json, not exposed as Agent answers.

Requests actual setup chain in the first error: tests/test_requests.py:124 test_no_content_length requests httpbin → tests/conftest.py:34 defines httpbin(httpbin) → Pytest reports recursive dependency involving fixture httpbin. XML error nodes contain191 such httpbin errors and4 httpbin_secure errors, with no other error type in this run. That is structured actual setup evidence, not an ERROR string in stdout. The classifier's original attribution remains unknown_requires_baseline_and_callchain; it is not overwritten to assert an unverified package-level root cause.

The observed wrapper/provider resolution is consistent with the older requests_7328 research block, whose provider investigation remains read-only. The prior S2 task pool screened for eligibility rather than universally repairing all Requests providers. No safe generic provider correction was found in the frozen research source used here. This run did not separately establish whether the missing outer fixture arose from package absence, plugin discovery/configuration or another environment difference. Those are unresolved mechanisms, not a new confirmed root cause or a statement about Kaggle's unavailable private scoring environment.

Disposition: retain both selected IDs and the failed admission. Do not substitute an easier task, spoof a fixture, alter original tests or begin a partial GPU pair. A separately versioned infrastructure investigation would have to establish a safe compatible provider path and rerun clean-baseline admission before this draft could be registered for GPU execution. Candidate CPU110/110 compatibility remains a separate passed gate; U-RE repair performance remains GPU_NOT_TESTED.
