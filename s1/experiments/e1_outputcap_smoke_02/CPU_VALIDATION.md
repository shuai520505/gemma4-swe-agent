# Exact official-stack CPU gate

The private Linux CPU Notebook `gemma4-s1-e1-smoke02-cpu`, saved version 1,
completed successfully. **77/77 passed, zero failures/errors/skips.** This is
HTTP-mocked compatibility evidence, not real Gemma inference or repair success.

The test set is the unmodified r04 71: 38 baseline Harness/API, five submission
static checks, and 28 S1 configuration/real ADK Runner/worker/probe/window tests;
plus six new startup-observer tests. The original 80-file registered source set
is byte-identical to the r04 CPU raw archive. The new 85-file map adds only the
independent experiment package, builder, CPU entry, observer and tests.

The new tests confirm the observer invokes the exact original
`s1.preflight.check_model` through the official LiteLLM HTTP path, journals
one generation plus two tokenizer operations, rejects empty text/count drift,
retains HTTP-error evidence, passes the original Notebook clock into r04's
actual controller, restores instrumentation afterward, and refuses the old
experiment ID. Existing r04 tests also verify that omitting `tools` is an
actual API error and that the old stopped builder cannot launch.

Versions: swegemma 0.2.11, adk-submission 0.2.13, adk-eval-core 0.1.0,
google-adk 1.36.1, google-genai 2.11.0, LiteLLM 1.82.4, psutil 5.9.5.
The complete Wheelhouse file map is frozen in `protocol.json`.

Raw archive: `results/cpu/raw.zip`, SHA-256
`57b42b8f5c36bbd1a4151faaea7c6fcfebb9a9884464790a8612488b2ffcd4cb`.
CRC and all 224 declared evidence files verified. Full source payload and
installation log are inside that original archive; extracted test logs and
both the 71-test and 77-test gates are under `results/cpu/validation/`.

Before GPU dispatch, Git blobs for all registered S1 files were checked against
these CPU-tested bytes. Preregistration was pushed in commit
`dd5dfbca7332a309d4edd558e1f8fd19d8951fc8` before saved GPU version 1 was created.
No candidate, Prompt, r04 runtime source or original evidence was modified.
