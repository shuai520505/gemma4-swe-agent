# Input construction passes; full model-boundary acceptance is incomplete

The original Issue is559 UTF-8 bytes, SHA256
`603fcbce6271954ca24171d4ae19dcaba962abf158fc04f53d3fd18dbcd20cb3`.
It is projected from the exact PR37 public Parquet using only the four allowed
identity/Issue columns, independently checked against PR38, and stored privately.
The published Issue contains its reporter's causal claim; that text is retained
in both arms without treating it as an independently verified conclusion.

prepare.arm_input returns the original string unchanged for A, and appends a
clearly delimited canonical JSON observation for B. The original file is not
rewritten. Private input_A.txt/input_B.txt and INPUT_BUILD.json bind their exact
bytes. TASK_INPUT_DIFF.txt contains the complete **task-input-level** difference.
It is not mislabeled as a complete rendered ADK request diff.
A is559 bytes; B is2134 bytes; the delimited supplement adds1575 bytes.

Both arms point to the same unchanged S0 ZIP, instructions, tools and native
Compiler configuration. No separate hint/reference fix/test overlay is supplied.
These are construction/source claims. The failed V2 only reaches A; its original
fixture wrote full HTTP requests after successful Runner return, so its request
bodies were not archived on this failure. ADK tool/event traces are available,
but cannot substitute for the missing full request capture. B is NOT_RUN.

Therefore the required actual A/B rendered-input equality, B-only receipt
visibility, schema and generation equality are **NOT_ACCEPTED**, not false facts
about observed differences. The current source captures configuration immediately
and requests in finally; this repair awaits a separately authorized CPU run.

No exact serving tokenizer/chat template is mounted by this CPU Notebook. Token
overhead is UNKNOWN. Input byte counts are recorded in GPU_EXECUTION_LOCK.json;
they are never converted to tokens or presented as model usage.

S0 has no seed/generation fields in its YAML. The pinned official defaults supply
16384 output and4096 thinking; the schema seed default is None. Later seed17 and
research15360-input/safety1024 Guard settings are not proven original S0 behavior.
No such override is added. Resolve this discrepancy before final GPU freezing.
