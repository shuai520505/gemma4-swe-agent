# Reproduction quality and limits

The original private ZIP passes every member CRC and is bound by SHA256 in
RAW_ARCHIVES.json. collect.py verifies the returned driver bytes, input manifest,
every input member, individual RESULT/receipt/command records, stdout/stderr
hashes, base/Issue/snapshot identities, before/after source hashes and cleanup.
Platform COMPLETE alone is not used to classify a bug. A target failure requires
working imports and passed positive controls, a target-phase receipt and either
an explicit contract assertion failure or the predeclared Issue-specific exception.

| Task | Positive controls | Target observation | Classification |
|---|---|---|---|
| django__django-16333 | 3 pass: plain form validity/relation persistence; creation form validity | selected relation count 0, expected 1 after creation-form save | TARGET_BEHAVIOR_FAILURE |
| pydata__xarray-3095 | 2 pass: initial Unicode coordinate and shallow-copy dtype | deep-copy dtype object, expected `<U3` | TARGET_BEHAVIOR_FAILURE |
| fastapi_14297 | 2 pass: non-optional upload HTTP200 and expected file sizes | optional upload raises the Issue's `issubclass()` TypeError | TARGET_BEHAVIOR_FAILURE |

There are **three verified scoped runtime environments and three credible
Issue-related failing checks**, not three failed repairs. Django/xarray target
assertions actually execute. FastAPI's target raises before its final assertion;
it contributes **zero executed failing target assertions**, with the known exception
classified separately. Exit code1, printed text and assertion counts alone would
not justify these conclusions.

## Contract and source provenance

Task IDs, base commits, Issue digests, snapshot digests and probe hashes are in
TASK_REPRODUCTIONS.json and the private task registry. Contracts were derived from
original public Issue descriptions before execution. Reference patch/test_patch
columns, solutions and native evaluator overlays were not used. No source files
were modified to manufacture negative behavior. Only owned checks run outside
the restored source. Dataset archives retain upstream source tests/licenses but
those tests are not rewritten or substituted for official evaluation.

Django uses an in-memory database and the built-in User.groups ManyToMany field
to test the same creation-form persistence contract. It does not reproduce every
custom-user fixture or the issue's full original application. xarray follows the
Unicode index deep/shallow-copy discrepancy, but uses modern pinned scientific
dependencies, not the original benchmark image. FastAPI uses a public base-commit
codeload archive, not the competition snapshot's original packaging; the archive
hash is intentionally different and explicitly recorded. The optional/non-optional
request contrast isolates the reported path in this environment, without proving
the full fix or a complete input matrix.

## Exposure and evaluation boundary

The first two external tasks are selected in the exact PR37 order and are now
**EXTERNAL_DEVELOPMENT_EXPOSED**. FastAPI is **HISTORICAL_DEVELOPMENT_ONLY**.
The entire old129-task pool remains development-only; reservations and exclusions
are preserved. None of these three may be described as fresh held-out confirmation
after probe/Issue review. Remaining source-lock ordering is unchanged, not newly
admitted or cleared for an independent experiment.

No Agent, candidate patch, native verify_task or canonical Docker SWE-bench harness
ran. `official_native_resolved` and `swebench_resolved` are null throughout. The
results establish reusable diagnostic baselines, not official Native admission,
repair accuracy, model adoption, out-of-sample improvement or Public Score.
Post-edit verification is unmeasured because no edit was made.

Warnings/modern dependencies, incomplete behavior coverage and the unrecorded
startup-hook origin remain limitations. Future repair tests need negative-to-positive
discrimination on unchanged versus modified sources plus a separate regression
check; a green probe alone cannot establish complete semantic correctness.
