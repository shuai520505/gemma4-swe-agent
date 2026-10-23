# Prospective V02b admission policy

These rules apply only after V02B_PROTOCOL_LOCK is committed and the recovered
environment is frozen. PR25's original STOP is unchanged. Old14246/14609 are
diagnostic development cases; neither can fill the new prospective sample quota.
5077 is a separately labelled carry, contingent on environment migration.

|Class|Required evidence|Action|
|---|---|---|
|A independent environment error|Actual missing distribution query in that sandbox plus frozen dependency declaration and external module namespace; or already established inline-snapshot origin|REJECT_CONTINUE|
|B target-related collection failure|Original Issue supports API/argument; original workspace source lacks it; traceback/provider corresponds; no independent environment fault|CONDITIONAL_TARGET_FAILURE; never formal in this round; continue|
|C mixed collection failure|Every error separately established as A or B; at least one of each|REJECT_CONTINUE while independent fault remains|
|D unknown internal/error cause|Any component unexplained, dependency state unobserved, incompatible trace/source correspondence or unsupported reporting discrepancy|STOP|
|E integrity/evidence failure|Task/Snapshot/Verifier/environment drift, required raw evidence missing or inconsistent, changed source/tests/config, provenance or cleanup failure|STOP|

Missing dictionary keys mean UNKNOWN, not proof of missing packages. No broad
ModuleNotFoundError-to-environment rule exists. Unknown mixed cases still stop.
The missing PydanticV1NotSupportedError in original fastapi.exceptions can be
target-related under the public pydantic.v1 rejection Issue, but that spelling
is not explicitly mandated by the public Issue. It remains conditional.

## Snapshot assertions and duplicate teardown records

Recovery01 exposed a research-reader defect before new screening. With
inline-snapshot0.21.1, a wrong snapshot assertion can generate a call failure
record and another record for the same test's autouse fixture teardown. Pytest's
suite tests attribute counts unique tests, while the XML contains more records.
The official native verdict remains false. This is not automatically a broken
environment, nor permission to ignore arbitrary fixture errors.

The new research reader handles only the exact verified upstream plugin case:

- Original JUnit hash and capture timing verified; original bytes retained.
- Suite tests equal unique classname/name pairs; failure/error/skip aggregates
  match all XML outcome nodes; extra record count equals paired finalizers.
- Each duplicate has exactly one snapshot call assertion and one error with the
  precise upstream message, paired to the same test identity.
- Installed plugin source matches the SHA-verified0.21.1 wheel.
- No other errors or malformed groups exist; official exit remains1.
- Source/config/test hashes remain unchanged; no snapshot update flags added.

Such a negative baseline may be formally eligible as target behavior failure,
after Issue relation review, while retaining the raw JUnit errors and duplicate
record counts. Independent environment errors are zero only under this precise
proof. Ordinary unrelated setup/teardown errors and reporting conflicts STOP.

Only research parsing/attribution is adapted. Official Verifier source, pytest
arguments, assertions, candidate ZIPs and native resolved are not rewritten.
The positive and negative owned snapshot controls verify that mismatches still
fail and test files are not automatically updated.
