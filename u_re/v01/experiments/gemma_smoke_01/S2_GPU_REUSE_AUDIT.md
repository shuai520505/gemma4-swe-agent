# Reuse of executed S2 infrastructure

PR8 remains an unmerged Draft at9aed40fa0fff10aff242fe30798d9c8c808b00c4. PR16 remains an unmerged Draft atcc9c18ee4eb8c1dcb767ab427064e4f07af618d4. This work branches from PR16, not a merge of the algorithm branches.

137 shared s1/harness_v2 files exactly match the source hashes in S2's executed protocol; see S2_REUSE_BINDINGS.json. Direct reuse: adk_submission.VllmServer/VllmConfig; s1.guard and LiteLlm/ModelRegistry; s1.worker; s1.verifier_v3.worker and environment JUnit capture; harness_v2.supervisor; infrastructure_recovery.wire; verifier_v3.audit; e3_localize_smoke_03.idle; verifier_v3.backend_logs. Official Compiler, six tools, submit_patch and native Verifier logic remain unchanged.

Minimal adaptation: use the existing single-Agent s1 worker rather than S2's near-identical worker with observe_nested; use Config()300s instead of S2's500s; replace four-run coordinator with one-run adapter; load frozen NoEGV directory. The S2 worker itself derives from this single-Agent path. No AgentTool/nested metrics, S2 prompt, old request context, patch or test output is imported into the candidate.

Readiness checks use /health and /models, without an extra READY inference request. Actual Gemma tool-call conformance still requires the future run. All model/wheel/source SHA are static pins until revalidated on assigned hardware. No current GPU allocation is asserted.
