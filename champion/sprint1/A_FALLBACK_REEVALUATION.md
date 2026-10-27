# A fallback: scoped repair validated, formal outcome still unknown

Classification: **VALIDATED_REPAIR**, restricted to the unchanged owned development
checks and independent source review. Not official Native or canonical SWE-bench.

Original archive: egrd/v032/RAW_ARCHIVES.json; SHA256
67386d9aa82f93612250b2d84dbf26f5bd2a7a82a5494d2ec2fe3bcc2bb74114.
Original1414-byte Agent fallback SHA256:
`d0aba874e19c5c109f39f870c005e80666d1a0a091b0f8e0a428d6c6865bf838`.
The actual private patch was read, not reconstructed from a report. It contains
an executable change in django/contrib/auth/forms.py and unrelated scratch repro.py.
Agent-visible test edits are not inferred from this filtered native diff.

Separately labeled production-only DERIVED patch SHA256:
`76263b5e356f3a2a3e79cceaf1285ad76c80b322cef791e33d7466a165ed0bda`.
This is not the Agent's original output. Its production section is byte-preserved;
only the scratch-file diff is excluded. Neither patch is committed publicly.

| Actual CPU check | Original base | Original fallback | Production-only DERIVED |
|---|---:|---:|---:|
| Exact original source restored |PASS|PASS|PASS|
| git apply --check / apply |N/A|PASS/PASS|PASS/PASS|
| Target relation assertion |FAIL:0 vs expected1|PASS:1|PASS:1|
| Three positive controls |3/3|3/3|3/3|
| Existing bounded regression |PASS|PASS|PASS|
| Probe/common bytes unchanged |PASS|PASS|PASS|
| Source unchanged during tests |PASS|PASS|PASS|
| Owned source workspace cleanup |PASS|PASS|PASS|

These tests actually finished **locally before the owner's subsequent instruction
to use Kaggle/GitHub instead**. Python3.12.2, a separate task venv and the exact
three pinned Django task wheels were used. Source tree SHA256
542af0a58f5391245a3e82a435ae49a328def6b8f6428856e3016bc163b7dfa9;
base60a7bd89860e504c0c33b02c78edcac87f6d1b5a; Issue603fcbce…20cb3.
The original probe1467627a…1015e and regression bytes match the frozen records.
Actual stdout/stderr, return codes and their SHA256s are retained privately;
safe command records are in A_FALLBACK_CPU_RESULTS.json. No expectation changed.

Independent review: the change restores the issue-related relation-persistence
step on the committed form-save path; it does not special-case the owned probe,
weaken tests, bypass validation or change the password operation. The deferred
save branch is unchanged. The raw patch's scratch file is unrelated and should
be excluded from a clean repair. The finite tests do not establish correctness
for all custom form overrides, backends or hidden assertions. The local venv is
process/dependency isolation, not a Linux chroot or official evaluation container.

**Answer to the central question: yes, the291-second modification was useful on
the available development contract.** The prior experiment correctly recorded no
explicit submission and no post-edit validation at that time; this new CPU result
does not rewrite that history. Native fallback evaluation is possible in the
pinned official path, so failure to submit is not by itself proof of a formal
zero. No official result on this patch has been observed.

After the location correction, local installation/testing stopped. One private
CPU-only Kaggle verification request was sent; HTTP499 with empty body, no
confirmed Notebook identity/status. Its outcome remains UNKNOWN; no blind retry.
Therefore these local results are **not relabeled as Kaggle results**. Kaggle
Compiler/re-evaluation confirmation remains blocked. Earlier disk/install failures
and their logs are preserved. No Gemma was rerun and no reference answer was read.
