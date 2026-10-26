# Official and external sources remain separate

## A. Accessible official development source

Official CLI authentication succeeded. All **524 accessible competition files**
were listed over three pages, not just the default first 20. The task-bearing
source remains tasks.jsonl. A fresh authenticated download is byte-identical
to the prior 129-record source:
`e4b3fd60f69dbc2b9213e54eeb9636db78aefe92c1d06269d73d9f5f8f3c8ad6`.
The current HARNESS_README also matches the pinned guide:
`445000219b803942c469391ec8b69791a31e9cec2f934738c767e34b5ca0aa1f`.
No additional task record source was found in the accessible listing. This
does not make hidden grading tasks accessible or imply no other data exists.

The [official data page](https://www.kaggle.com/competitions/gemma-4-developer-agent/data)
has no body through the web reader; authenticated CLI files/downloads are the
primary evidence here. No hidden tasks, grading materials or answer patch were
requested. Embeddings/snapshots do not create new identities. The original
124 exclusions plus five preserved reservations cover all 129 records; no
historical NOT_RUN reservation is released.

## B. Verified public external benchmark

The publisher's [SWE-bench dataset documentation](https://www.swebench.com/SWE-bench/guides/datasets/)
links [SWE-bench/SWE-bench_Verified](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified).
The public, non-gated dataset revision is
**78f471bf655a3137b2e8a75af1501690ec009ec3**. The downloaded Parquet's SHA256
matches the publisher's LFS identity. It contains 500 tasks across 12 Python
repositories. Exact metadata and hashes are in EXTERNAL_SOURCE_LOCK.

Only instance_id, repo, base_commit and problem_statement (hash only exported)
were projected. The downloaded Parquet includes reference/evaluator columns,
but **none of those columns, hints, difficulty or outcomes was decoded or used
for selection**. Original Parquet stays private. No reference fix is inspected.

The [publisher project README](https://github.com/SWE-bench/SWE-bench#-citation--license)
and [LICENSE](https://github.com/SWE-bench/SWE-bench/blob/main/LICENSE) state MIT.
The dataset card has no separate license tag; this absence is recorded rather
than invented. Repository code retains its own license obligations; admission
must preserve those notices and check the individual repository/source rights.
Public accessibility alone is not used to assert unrestricted redistribution.

All 129 historical metadata tuples were compared. No exact repo/base/Issue-hash
match was found; eight psf/requests records are conservatively excluded at
repository level, leaving **492 repository-disjoint candidates**, not 492
admitted tasks. Semantic cross-repository aliases and pretraining contamination
remain unproven. No claim of universal independence is made.

The official upstream evaluator was source-pinned at
**02e7a74ffd0b707aab73d203fe87bdc7c76afc8e**, with seven source/license hashes
recorded. A public GitHub API 403 was handled using read-only git ls-remote;
an outdated docker_build.py path returned 404, then actual imports/source paths
were inspected. Neither failure was hidden or treated as an evaluator result.

The [publisher FAQ](https://www.swebench.com/SWE-bench/faq/) requires Docker for
its normal reproducible evaluation. The pinned evaluator imports Docker and
creates containers. No Docker executable/daemon is available in the local
environment. This study did not test a Docker daemon inside Kaggle or alter the
successful CPU Notebook to pursue a different experiment. Two first-ranked
base snapshots/license files are separately hash-checked if available; this
does not establish a working test environment or a discriminating baseline.

Classification: **EXTERNAL_EVALUATION_ONLY**. Its evaluator can accept patches
produced with the same six-tool repair workflow, but any adapter/task setup
needs validation. Its resolved label is **SWE-bench resolved**, never the
competition's official Native Resolved. No external baseline was run or task
admitted here.

## C. Exposed development data

Old tasks remain usable only for explicitly labeled development questions and
cannot fill held-out slots. This recovery used an owned synthetic fixture,
not a historical real Issue. PR36's task pool and execution lock are unchanged.
No local/CPU result is converted to a Public Score or used to replace S0.
