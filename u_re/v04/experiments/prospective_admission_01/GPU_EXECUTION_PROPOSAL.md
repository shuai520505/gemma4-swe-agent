# Independent GPU execution proposal — NOT AUTHORIZED

Engineering status: V04_EGR_GPU_READY. Human authorization for GPU SaveKernel and real Gemma is absent. This document is a proposal, not an authorization record. No GPU Notebook has been created or run in this round.

## Exact proposed scope

One new private Notebook, provisional slug `wudangdexiaodoashi/gemma4-u-re-v04-egr-abba01`; one SaveKernel maximum, no automatic retry.4xNVIDIA L4,TP4,Gemma4 31B QATv2 (`google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2`),vLLM0.19.1,platform window at most10000seconds. Four independent Agent sessions only:

| Run | Task | Candidate |
|---|---|---|
|1|fastapi_14297|A:Frozen Action-First|
|2|fastapi_14297|B:EGR V04|
|3|fastapi_14459|B:EGR V04|
|4|fastapi_14459|A:Frozen Action-First|

Each session:300s,60chargedtools,120scommand,context32768,output16384,safety1024,inputcap15360,thinking4096,seed17. Same original generation YAML and six tools, no extra Agent/LoRA/model/Prompt/compression factor. Fresh workspace/chroot/process lifecycle/history/patch/log/native evaluator per run; only the served model is shared. No fifth run or Competition Submission.

## Authorization must bind these artifacts

- Final CPU140415803/v1 COMPLETE, raw archive SHA256 `ffcdb21f02078919a4318151c40e4654643249c3c280f411111e5a8ff96138b8`.
- Final production ZIP SHA256 `77f7a16721eecb3bbcdf9736670b25cc73735ab7258500b965db66f81fb722f4`.
- ABBA lock SHA256 `c5d222ab4b2fd01a7964018e2db4bee7030d22245312c2d6d4de7bb218be5ae1`.
- Selected task lock SHA256 `bfd87a222b4a4a2da2aa7b5e993b759568aca5f01d2459521281ff4963e7b46a`.
- Trusted environment SHA256 `452c0d9afdf7c21edcd43a6a67e69cca6c67aba640eb526f50aa9835169dc7d9` (unchanged PR26 environment).
- A ZIP `70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8`; B ZIP `07263740c5ee22bf6611d7fa31dafbc84d7fb50288d22355b9201cd6954a6840`.
- All eight exact model/tokenizer/chat-template file hashes and runtime/source/wheel identities are in `ABBA_EXPERIMENT_LOCK.json`. CPU did not load these weights.

The current new Session entry rejects GPU without a new externally supplied grant bound to the exact lock,payload,environment,arms,model files,run count,4L4/TP4 and10000s scope. There is no GPU dispatch command in this preparation. Prior grants, old GPU_authorized fields and PR27's UNKNOWN are not authority for this proposal.

## Dynamic checks after new authorization

RUNTIME_RECHECK_REQUIRED: account/slug uniqueness, current GPU eligibility and quota, complete platform window, approved model input accessibility,actual4L4 and VRAM,CUDA12.8/PyTorch2.10.0+cu128/vLLM0.19.1/frozen official versions,eight weight/tokenizer/template hashes,actual chroot canary and cleanup,service health/identity,remaining window before each session. Existing PR27 Batch2 remains UNKNOWN; check for active conflicts by readonly evidence and never retry it blindly.

Reuse the conservative20600reported-quota-seconds planning gate for one batch and7740s execution envelope as planning assumptions, not measured cost or a promise. A live gate must cover all remaining300s sessions,native verification,export andcleanup. Account quota changes are not a per-Notebook bill. If resources are insufficient,do not dispatch or start a new session. Ordinary algorithm failures continue the fixed order; identity/isolation/environment/Verifier integrity failures stop new starts and preserve completed results.

Primary outcome: paired Native Resolved from original TaskResult/JUnit, including false/null. Secondary metrics: evidence-supported production edits/hypotheses,targeted assertions,repeated search/unchanged tests,broad tests/path/dependency errors,explicit/repeated submit/post-submit calls,Context Guard,charged tools,Agent/Worker time,prompt/completion/received usage with missing=null. Include failed-session costs. Two FastAPI tasks give descriptive evidence only, not statistical significance,cross-repo generalization or Public Score.

Important baseline interpretation:14459 retains2assertion failures plus2exact paired snapshot-finalizer records under the frozen PR26 reader; independent environment errors are0. Unpaired/unknown setup or teardown errors are not covered and remain STOP. Do not modify tests,Verifier or result XML to remove these records.
