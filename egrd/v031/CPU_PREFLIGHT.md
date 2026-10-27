# CPU Runner gate failed; no real Gemma execution

Notebook [141014201](https://www.kaggle.com/code/wudangdexiaodoashi/egrd-v031-evidence-to-patch-cpu),
private, GPU/TPU/internet disabled, no model/competition input. It reads the existing
development Dataset and official wheelhouse. Exact installed SDK versions/source
pins are checked before the real-task baseline: swegemma0.2.11, adk-submission0.2.13,
google-adk1.36.1, adk-eval-core0.1.0. No package upgrade or model weight is used.

## V1 — ERROR

The inherited generic adapter tries FastAPI-oriented dependency staging before
the Django-only overlay and cannot obtain flit_core from the three frozen wheels.
This is an initialization error, not a negative Issue result or model failure.
No Agent/model call starts. A partial root remains because the old start routine
had not registered it for cleanup. CPU_FAILURE_V1.json explicitly rejects the
original empty-manager cleanup flag as sufficient proof. Original files are kept.

V2 changes only the v031 adapter payload member: stage the exact Django dependencies
directly, retain original child confinement, and clean up partial initialization.
No S0, receipt, Issue, probe, evaluation code or native Runner bytes change.

## V2 — ERROR with useful partial execution

The unchanged-source probe reproduces the same relation count0 versus expected1,
with3 positive controls,1 failing target assertion and unchanged source identity.
The separate ordinary-user/password regression passes; trusted write protection
and cleanup pass. Displayed Django version is4.2.dev20261026000000 because of
synthetic Git metadata; PR38 without Git reported4.2. Source bytes/base hash match.

S0 actually compiles both explicitly and inside the native Runner for A. Its six
tools execute. A reads source, is denied the host probe read/write, passes a chroot
symlink canary, runs an owned runtime assertion and inserts an inert production
comment. Next git diff --check fails; submit_patch returns GitDiffError:
`fatal: bad config line 1 in file /dev/null`. Native closure nudges cannot recover
because the finite scripted fixture has ended. It returns no submitted patch.

Observed A counters:14 scripted ADK model calls,8 official charged calls,
3.025257797 Agent seconds. This is not Gemma cost/performance data. Actual model
tokens are null. Full HTTP bodies were not archived on failure; counts come from
the official context journal. B, trusted post-edit evaluation and full rendered
A/B comparison are NOT_RUN. No baseline failure is counted as an Agent failure.

## Root cause and current local repair

The observed failure is Git reading bad config from /dev/null. Source inspection
shows the inherited minimal runtime creates /dev/null as a regular file, while
the child sets GIT_CONFIG_GLOBAL=/dev/null. Shell redirections can persist bytes
there. The particular contaminating write and its bytes were not captured.
This affects the research runtime; it is not an explanation for formal S0 scores.

Current source adds device_runtime.install_null_device: require a genuine Linux
character device1:3, with no ordinary-file fallback. Failure to create it is fatal
and triggers partial-root cleanup. Offline tests simulate success, denied mknod
and an invalid regular-file result. They do **not** prove Kaggle CAP_MKNOD support.
The current source also preserves HTTP requests in finally and compiled config
before entering the Session. These post-V2 fixes are **NOT_KAGGLE_VALIDATED**.

Both authorized CPU versions have been used; no third version is dispatched.
The next concrete action needs a new CPU validation allowance, not GPU permission.
RAW_ARCHIVES.json records both original ZIPs/CRCs/hashes. Auxiliary CLI log downloads
ended IncompleteRead, but both main evidence ZIPs are complete and independently
verified. The original CPU logs inside those ZIPs are authoritative.
