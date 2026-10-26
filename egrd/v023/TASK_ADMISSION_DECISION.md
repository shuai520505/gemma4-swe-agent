# Conditional admission: no task admitted

Compiler recovery is complete. Official task admission is still blocked.
The original V0.2.2 pool/SELECTED_TASKS/execution lock remains byte-identical;
there is no replacement of its null identities with external ones.

## Separately frozen external source

EXTERNAL_SOURCE_LOCK binds the publisher dataset commit, LFS-verified Parquet,
metadata-only projection, seed 17, ranking prefix and maximum 16 future CPU
baselines. Selection is the first two eligible in SHA256(prefix+instance_id)
order, with an ID tiebreaker. No outcome/difficulty/reference-fix selection.
Repository-level exclusion removes psf/requests; all previous history remains
excluded. This conservative repository gate is stronger than only comparing IDs.
No model result was observed during this investigation.

The first two ranked public snapshots were downloaded in order:

1. django__django-16333, django/django,
   base 60a7bd89860e504c0c33b02c78edcac87f6d1b5a.
2. pydata__xarray-3095, pydata/xarray,
   base 1757dffac2fa493d7b9a074b84cf8c830a706688.

Their actual tarball SHA/size, root commit, Issue hash and root license-file
hashes are in EXTERNAL_SNAPSHOT_CHECKS. No archive was extracted or source test
body read. They are **NOT_ADMITTED**: source availability is not a meaningful
negative baseline. These are proposed external development cases, not the two
official adoption slots and not independent confirmation results.

## Unpassed gates

The publisher evaluator requires Docker; no local Docker executable/daemon is
present. Its source was pinned, not installed/executed. No empty-patch baseline,
FAIL_TO_PASS assertion, environment closure, native competition TaskResult or
JUnit has been obtained for these external tasks. No test or reference patch
was decoded/changed to manufacture eligibility. Only the synthetic CPU tasks
have actual new native results.

A successful CPU Notebook is not an infrastructure failure warranting the
second authorized version. That version was not spent exploring a new Docker
setup. Kaggle Docker-in-Docker feasibility remains NOT_TESTED; absence of a local
Docker binary is not proof that all Kaggle/container platforms forbid Docker.

Before any external task is admitted: establish a permitted CPU Docker host,
lock the evaluator dependencies/images and per-repository license/environment,
apply only trusted test overlays on evaluator side, run an empty-patch baseline,
confirm Issue-related failures with no independent environment errors, verify
cleanup and record the source/evaluator/result identities. Reference fixes must
remain inaccessible to candidate developers/model context. Stop on unexplained
collection/integrity errors. Reject explained environment-only failures in order;
stop after the first two eligible or 16 checks, without selective refill.

Task gate: **EXTERNAL_EVALUATION_ONLY**. Actual admitted counts: official 0,
external 0. The old official adoption experiment remains blocked.
