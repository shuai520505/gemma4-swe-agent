# R2 quality audit

REAL_GPU_OBSERVATION: original R2 target/control receipts and source identities were preserved, not regraded into official results. STATIC_ANALYSIS: all three diffs and relevant locked source were reviewed without reference solutions or hidden tests. CPU_VERIFIED: independent isolated base/R2 copies ran expanded owned tests; receipts include every assertion and failure. No original trusted expected outcome was modified.

## Django and the misleading label

The exact archived probe source `execution/inputs/integration/frozen-checks/probe.py`, run(), near line 117, emits CHECK_PASS_NON_DISCRIMINATING whenever controls pass and no target fails. The same helper was used to identify an unpatched reproduction during preflight, hence the unfortunate label. It does not calculate discrimination, compare candidates, or check source identity. The evaluator separately records target_passed, target_failed, patch identity and isolation.

The original Baseline Django receipt fails both fresh string targets while controls pass. R1 and R2 pass both with controls passing. All three have identical base_source_identity; tested_source_identity differs as their retained patches differ. All assert check_unchanged, check_write_denied and source_unchanged_by_checks. The captured exact probe code and comparison are hashed in DJANGO_DISCRIMINATION_AUDIT.json. Expanded CPU tests repeat the base-fail/patched-pass contrast. There is no evidence from this comparison of a nondiscriminating target, different base source, or mutated check. The label remains unchanged in historical evidence.

The helper would be unsafe as a generic no-target acceptance rule because all([]) is true, but both expected target rows are present in each of the three actual Django receipts; the empty-target edge case did not occur. The trusted frozen probe bytes also equal extension/r12_issue_checks.py. This audit does not silently repair its historical label or expected outcomes.

R2 expanded CPU checks: 13/13 pass, including fresh TextChoices/IntegerChoices representation, SQLite readback, choices/labels/values/names, enum inheritance, equality/hash/value lookup, JSON primitive serialization, auto values, custom date Choice values, repr/copy, formatting and integer arithmetic. Base fails the three representation targets and passes the controls. The fix changes generic Choices string conversion too, which is a wider inherited behavior; values, types and metaclass remain unchanged.

Original locked Django model_enums suite: 16 executed on base and R2, 14 pass and the same two functional-API tests error in both. Python 3.12 Enum passes `boundary` to the old ChoicesMeta.__new__, which does not accept it. This is a pre-existing runtime compatibility error, not an R2 regression or a suite pass. A compatible older-Python rerun is NOT_RUN. No production workaround or test weakening was applied. A guarantee across all historical Django usages is NOT_RUN.

## xarray

R2 expanded CPU checks: 10/10 pass, including the source-identity receipt, NumPy empty chunk metadata, real Dask chunks and multi-dimension aggregation, preservation of the inconsistent-chunk ValueError, actual Zarr chunks=None metadata without data reads, Zarr+Dask chunks, real value read counter, duck arrays with/without chunks and a LazilyIndexedArray backend with zero __getitem__ calls. Base fails the Zarr and explicit lazy-backend no-materialization targets. Existing required R12 controls already passed for all arms.

STATIC_ANALYSIS: _data is a private interface, but the locked Variable.chunks and chunksizes implementation already uses it to inspect the original storage. The change avoids calling Variable.data merely to ask if chunks exist; it leaves chunksizes iteration, metadata shapes and the inconsistency exception intact. For recognized duck/Dask arrays the data accessor retains their array identity. This supports the locked version, not a promise for future xarray versions or every third-party backend. Unrecognized objects forced through the private fastpath remain an unsupported-coverage risk; broad backend compatibility across versions is NOT_RUN. The Agent fix is not being distributed as an xarray library release.

The newly written expanded fixture initially used zero as a real Zarr value, which the default fill_value=0 decoder masks to NaN on both versions. Its first receipts are preserved. Positive fixture values resolve that audit-fixture defect without changing historical checks, expected behavior or production code; CPU_PROBE_FIXTURE_CORRECTION.json records it. Final Zarr controls still require real reads for values and zero reads for metadata.

## pytest

R2 expanded exact-function CPU checks: 10/10 pass including a source identity receipt. Array replacement, real DEFAULT, explicit Mock, attribute_name filtering, mixed counts, empty/no patchings, dual mock-module DEFAULT objects and a custom equality trap are covered. Base fails array/mixed/equality targets. Unit extraction executes the exact AST function, separately labeled from native framework collection.

The actual locked pytest 5.0.2.dev58 framework was also run against five owned collection tests: R2 passes 5/5, base raises the original ambiguous-array ValueError during collection. Tests cover array replacement, default mock injection, explicit Mock without injection, ordinary fixture argument preservation and a plain function. Raw commands and output are retained. The new fixture initially replaced os.getcwd globally, interfering with NumPy's lazy sysconfig import; it was moved to an owned Target attribute while preserving the original failing array comparison. Initial output is retained separately. No historical trusted check was changed.

STATIC_ANALYSIS: DEFAULT is a singleton identity contract; equality is inappropriate for arbitrary replacements that overload __eq__ and return an array. Identity matching still recognizes both installed mock-module DEFAULT objects and preserves the existing attribute_name exclusion. No legitimate injected argument should be counted by value equality with a non-DEFAULT replacement. Existing broader framework suites are NOT_RUN, not implied by these focused checks.

## Quality conclusion

No R2-attributable regression was observed in the expanded focused checks. The two Django compatibility errors are shared by the base, and compatible-runtime resolution remains unverified. The three R2 research patches retain their validated development status with these explicit limits. Official Native Resolved and canonical SWE-bench Resolved remain UNKNOWN; no claim of official 3/3 is made. These task-specific patches are not included in the submission candidate.
