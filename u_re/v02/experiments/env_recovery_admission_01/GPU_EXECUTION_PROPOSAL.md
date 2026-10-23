# New V02b GPU scope requiring separate authorization

This round does not allocate GPU, load Gemma or submit to the Competition.
Unused V02 authorizations are not carried across the changed environment/cohort.

The executable task/order/model/budget lock is
`production/ABBA_EXPERIMENT_LOCK.json`; selected identities and evidence hashes
are in SELECTED_TASKS.json. Trusted evaluation uses V02B_ENVIRONMENT_LOCK.json.
The Agent keeps the original GPU03 chroot runtime allowlist and frozen ZIPs.
No evaluator-only content, another arm's artifacts, or research reports are
copied into Agent context. Every arm has its own Session, workspace, chroot,
process lifecycle, logs, patch and native verifier output.

| Batch | Runs | Task | Order |
|---|---|---|---|
|1|1–2|fastapi_5077 (predeclared carry)|A then B|
|1|3–4|fastapi_11355 (new)|B then A|
|2|5–6|fastapi_14463 (new)|A then B|
|2|7–8|fastapi_9555 (new)|B then A|

A is Frozen NoEGV; B is Frozen Action-First. Full is excluded. Candidate ZIPs,
generation settings and context guard stay unchanged: 300s Agent, 60 charged
tools,120s command,32768 context,16384 output,1024 reserve,15360 input cap,
4096 thinking,seed17. Primary endpoint is native resolved; carry/new pairs and
Context Guard status are reported separately. Unknown usage stays null; failure
costs remain in totals. Four same-repository pairs cannot establish generality.

## Proposed maximum resources

Request two distinct private GPU Notebooks, one per batch, at most four genuine
Gemma Sessions each;4×NVIDIA L4,TP4,Gemma4 31B QATv2,vLLM0.19.1. Each Notebook
requests at most10000 platform seconds; no automatic GPU retry, fifth Session,
task substitution, Prompt edit or formal Submission. A failed batch is retained
and the second batch cannot be repurposed as its retry.

Conservative per-batch admission retains the GPU03 formula:
`4*1410 + 900 + 1200 = 7740` wall seconds. The1410/session allowance includes
the300s Agent plus initialization, native verification, supervision and cleanup;
it is a planning envelope, not measured task duration. Additional1200 covers
model startup;900 covers export, final cleanup and safety. Reserve at least
20600 reported quota seconds per10000s Notebook under the conservative2× rule,
and recheck actual quota and a complete remaining window before each batch and
each new Session. Two batches require at least41200 planned report seconds.
No account quota difference is presented as a Notebook bill.

The read-only resource observation in resources/ is timestamped, not a capacity
reservation. Actual allocation,4L4 memory,CUDA12.8,torch2.10.0+cu128,vLLM0.19.1,
eight model-file hashes,tokenizer/chat template,model route,official wheels,
chroot canary,HTTP lifecycle,remaining window and idle/cleanup must be checked
at execution. Old successful hardware is only a known configuration.

## Final authorization binding

Any later authorization must name this experiment, exact task/order lock,
environment fingerprint, accepted production-payload SHA, both original ZIP
SHAs, model/version and the two batch limits. The new production entry rejects
GPU mode without a matching external authorization and rejects scripted CPU
transport on the GPU route. The shared production ZIP contains no scripted
model implementation; CPU acceptance injects the owned transport externally.
The existing exclusive claim/receipt/no-retry/version-bound collection machinery
must also bind each authorized GPU payload before dispatch. A later dispatch
must re-derive CPU acceptance from the raw archive, not trust a boolean flag.
