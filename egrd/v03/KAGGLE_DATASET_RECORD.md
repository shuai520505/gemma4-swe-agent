# Private versioned dataset record

[EGRD Repair Development](https://www.kaggle.com/datasets/wudangdexiaodoashi/egrd-repair-development)
— ID **12872403**, owner `wudangdexiaodoashi`, **private**, actual current version
**2**, status **ready**. Official CLI metadata independently confirms `isPrivate`;
`datasets status --format json` confirms `current_version_number: 2`.

- **V1:** immutable CPU inputs: three base snapshots; owned diagnostic programs;
  environment locks and25 offline wheels; metadata/exposure registry; licenses;
  NOT_RUN results preserved. Input ZIP **64,472,934 bytes**, SHA256
  `a2f73107e0aa6435d1a3979d491419a3b591425c848a92cb434a826d80e5c06f`.
- **V2:** identical V1 input ZIP plus explicit result/provenance sidecars
  TASK_REPRODUCTIONS.json, CPU_EXECUTION_RECORD.json and RESULTS_MANIFEST.json.
  The old NOT_RUN input record is not retroactively rewritten. Read the latest
  sidecar for execution outcomes and retain `dataset_input_version=1`.

Kaggle automatically expands the uploaded ZIP. The CPU input was therefore a
read-only directory, not the original ZIP. The Notebook verified its exact
MANIFEST.json digest and every listed member. `observed_original_bundle_sha256`
correctly remains null; local upload ZIP identity and remote member identities
are separate observations. V2 preserves those source/probe inputs.

## Provenance and exposure

The historical129-task registry is metadata-only, development-only, with all
old exclusions/reservations retained. No historical raw task/evaluator payload
is copied. The PR37 SWE-bench source lock is preserved byte-for-byte:
revision `78f471bf655a3137b2e8a75af1501690ec009ec3`, published Parquet SHA256
`030cfd7f2a704c4c0226e7f104c725a3b41230b1d3517f9c915ad7ea5be3fa25`.
The492 repository-disjoint metadata entries retain their frozen order. Only the
first2 are executed here; a historical FastAPI task is appended for explicitly
exposed functional debugging. No outcome-based reordering or task replacement.

Original public Issue digests and base/source identities are recorded; raw Issue
bodies and benchmark patch/test_patch/hints are omitted. No reference solution,
native evaluator overlay, model reasoning or credential is uploaded. Whole public
base archives include their ordinary upstream tests, but no hidden task overlay.

## Licenses and access

Upstream source remains unmodified and retains its license/copyright/notice files:
[Django BSD-3-Clause at the exact base](https://github.com/django/django/blob/60a7bd89860e504c0c33b02c78edcac87f6d1b5a/LICENSE),
[xarray Apache-2.0 at the exact base](https://github.com/pydata/xarray/blob/1757dffac2fa493d7b9a074b84cf8c830a706688/LICENSE),
[FastAPI MIT at the exact base](https://github.com/fastapi/fastapi/blob/3c54a8f07b70cdd40e3d81ea319e9fcccd2481d2/LICENSE).
Original dependency wheels retain bundled license/notice files and hashes.
annotated-doc0.0.2 omits its license in the wheel: the publisher's
[release-tag MIT LICENSE](https://github.com/fastapi/annotated-doc/blob/0.0.2/LICENSE)
is verified and supplied separately, without modifying wheel bytes.

The aggregate uses Kaggle `other`, not a blanket CC0 relicensing. Keep it private.
This public PR carries source URLs/hashes and safe derived records, not the raw
source snapshots or task programs. Dataset access must be explicitly granted to
collaborators by the owner; a public Git branch alone cannot reproduce private inputs.

## Actual operations and preserved failures

One Dataset identity and two versions; one CPU Notebook identity and one executed
version. Before actual creation, local CLI rejected a subtitle longer than80
characters; source inspection/read-only recovery confirmed no Dataset had been
created before the corrected create. Original failure and correction proof are
retained. A local disk-full packing attempt and a no-output pip download were
also retained; the task's own cache was moved to C: without altering historical
evidence. No failed or uncertain Notebook was blindly redispatched.

The initial local Notebook template assumed an unexpanded input ZIP. Dataset CLI
file inspection revealed automatic expansion before dispatch. The old template
was archived privately and the actual V1 accepts the mounted manifest/member
layout. This local preflight correction consumed no extra CPU Notebook version.
CPU execution itself passed; the authorized corrective CPU version is unused.

Private cache: `C:/Users/HP/.codex/private-evidence/egrd_v03/`.
RAW_ARCHIVES.json binds the returned raw ZIP, size and CRC audit. CLI stdout,
stderr, request records, private upload sources and original Notebook are retained
there; no signed URLs or API configuration are published.
