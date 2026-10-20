# CPU launch sequence exception

The read-only preexistence query returned an SDK ValueError claiming kernels.get permission denial for the new slug; it did not expose an HTTP404. CPU_PREEXISTENCE.json correctly records exists=null, not false. Its assertion failed. The ad-hoc PowerShell invocation nevertheless continued to the next Python command, so this preexistence assertion did not act as the intended sequential gate.

Exactly one CPU-only SaveKernel request was sent and accepted: HTTP200, new kernel139838876, version1, as recorded in results/cpu01/SAVE_REQUEST.json and SAVE_RESPONSE.json. Thus the returned version establishes this was a first saved version; the ambiguous query itself did not. There was no retry, duplicate version, GPU, model source or formal Submission. The exclusive SAVE_INTENT write in the frozen launcher prevents blindly resending this same build.

Retain this procedural exception rather than rewriting the query as successful. Subsequent dependent operations use one Python process with checked return codes. Replication must inspect existing saves and accepted versions; do not rerun this launch to improve its preflight history. This note is independent of fixture evidence and cannot grant native baseline admission.
