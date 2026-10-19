# Audit boundaries

`audit.py` is a post-execution host utility. It is absent from the frozen
85-file GPU payload and all Agent ZIPs, and cannot influence task actions.

`results/` is the initial faithful extraction of r04's runtime audit. In
particular r04 labeled native exit 1 as failed and summed the 24 available
response usages. Those extracted fields are not an attributable repair
verdict or complete cost for the 25 dispatched requests.

`final/` is the qualified research audit: A is unknown because all 194 errors
are verifier fixture setup errors; B is not_run. Native raw fields stay false
and exit 1. Token usage is explicitly partial, all 25 requests are enumerated,
and first successful file/production edits are separately identified from
tool results and the actual Patch. The report uses this qualified audit.

`final/control-tools.json` and CSV pair every one of the 23 native tool-call
attempts with its complete response. `final/control-requests.json` has 25 rows,
including the final request with no observed response/usage. The full actual
HTTP bodies and native reasoning remain in the immutable raw GPU archive.

No frozen runtime code was changed after GPU dispatch. Rerunning this offline
utility neither executes models nor repairs/splices the stopped experiment.
