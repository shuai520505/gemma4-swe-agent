# Observed costs and missing billing

This execution used2unique GPU SaveKernel requests,1targeted CPU SaveKernel,
3real Gemma Agent sessions and40real inference requests/40HTTP200responses.
The CPU repair used35SCRIPTED_ONLY requests, excluded from GPU/model efficacy.
There were0formal Competition Submissions,0selective session reruns and0third
GPU dispatches. Both GPU authorizations are consumed.

Received usage:303244prompt +11090completion =314334total tokens. Usage is
present on every successful real response. Separately attributed thinking
tokens remain null; the completion field is not assumed to exclude/include a
particular unreported reasoning component. No response finishes due to length.

Initial counted inputs are A2199/B2999/C2999 with identical normal task input.
The matched Skill package therefore costs800additional initial input tokens,
even without invocation. Its eventual time/repair effect remains unidentified.

Batch2 observed first-cell-to-cleanup window:1010.148seconds. Summed Agent
time353.030seconds; summed worker windows445.080seconds. The92.051second
worker-minus-Agent difference includes setup, native evaluation and cleanup.
The565.068seconds outside workers includes shared environment/baseline/model
lifecycle/idle/cleanup work. Neither difference is an isolated verifier latency
or a GPU invoice. Summed model HTTP latency336.589seconds includes service and
transport. Mechanism subprocess invocation count0 and added script execution
time0 are observed; Skill-interface causal overhead is not identified.

Batch1 actual device identity, isolated billed runtime and GPU compute time
were not observed; its body failed before hardware/model instrumentation.
Batch2 actually observed4L4devices and clean model-process termination. Queue
and pre-first-cell provisioning time are outside its elapsed clock. Multiplying
wall time by4would be an estimate of allocated device-seconds, not platform
billing or measured utilization, so no such bill is claimed.

Final CLI quota reports GPU0.63hused/29.37hremaining of30h. These are rounded,
account-wide figures. Pre-dispatch snapshots and any account deltas cannot
uniquely allocate a bill to this experiment. Cost per successful repair is
undefined with zero successes, rather than zero or an invented finite value.
Machine-readable per-arm measurements are in `RESOURCE_USAGE.json`.
