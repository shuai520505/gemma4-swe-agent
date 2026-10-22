# Actual Kaggle CPU isolation evidence

## What changed

Prior Landlock failure is retained unchanged: `gemma_smoke_01/recovery_01/ISOLATION_RESULT.md` reports ENOSYS38. That result cannot distinguish missing kernel support from filtering/emulation. It does not prove that all other boundaries are unavailable. No Landlock syscall was repeated.

Official swegemma0.2.11 contains a Docker ContainerManager:network none,container-owned filesystem,no explicit host mounts in start(),optional preseeded sandbox image lookup. Exact wheel/member hashes and line spans are in `SOURCE_AUDIT.json`. Existing S2/s1 workers instead use SubprocessManager; rewritten paths/venv are not mandatory isolation. Historical S2 success is no proof of filesystem access denial.

The new user Notebook rules authorize actual CPU capability/tool probes. CAP01 Notebook **140209916 v1 COMPLETE** proves root UID,chroot and setresuid/setresgid support. Mount/user namespaces both return EPERM1. The installed Docker7.1.0 client raises DockerException while connecting through its configured environment; no usable official Docker/proxy path was demonstrated. This does not prove every Kaggle deployment lacks Docker. Local Windows has neither Docker tooling/runtime nor installed WSL. No dependencies were added and no images were pulled.

## Minimal supported boundary

`chroot_boundary.py` copies only a minimal Python stdlib+bash/git/coreutils runtime into an owned root,with no host bind mounts,/proc,/kaggle/input,history,other arms or evaluator files. Runtime is root-owned; Workspace belongs to UID65534. `chroot_exec.py` is a new clean child:chroot+chdir inside,drop all UID/GID identities/groups/caps,no_new_privs,closed inherited descriptors,sanitized environment,then exec original tool command. It reuses only the prior audited seccomp function; Landlock probe/apply is never called. Seccomp additionally denies parent-memory/ptrace/mount/chroot escapes and external network access.

Official six-tool functions/schema are unchanged. The adapter is below those functions. Crucially,official read_file/edit_file copy_from and write_file/edit_file copy_to also execute inside the chroot; a host-side shutil copy following an attacker-controlled Workspace symlink would invalidate this boundary. The copy methods do not follow untrusted symlinks from the trusted host. This implementation intentionally accepts trusted single-file transfer only; directory/snapshot/venv deployment is not yet a complete Runner adapter.

CANARY01 Notebook **140211037 v1 COMPLETE** ran all six real functions bound by SwegemmaContext. It completed12 native charged operations,one actual edit,target+old-behavior assertions,git diff --check and one official successful submit. It is not a model-driven Agent run or a native competition TaskResult. `canary01/derived/official_tool_events.json` and `tool_processes.json` contain the actual owned synthetic commands/responses,including real failures on forbidden reads. `CANARY_RESULTS.json` is an index into this evidence,not the enforcement mechanism.

The public owned evidence shows workspace positives,absolute private research/evaluator/other-arm reads denied,traversal/symlink/descendant reads denied,deliberately inheritable canary FD absent,host /proc/input absent,parent-memory syscall denied,external socket denied,official read_file through a symlink rejected,and unchanged host canary hashes. Original native execute_subprocess_command supplies timeout/process-group cleanup. The root was removed successfully. No real hidden tests,reference patch,model or task inputs were involved.

## Scope and remaining integration

Status: **ISOLATION_VERIFIED for this CPU synthetic six-tool deployment**. This is data-access isolation,not protection against kernel vulnerabilities. It does not establish full task dependency support,untrusted daemon/session escape cleanup,whole-Runner cancellation/native verifier compatibility,or assigned GPU-kernel behavior. A future full integration must preserve this root/UID/fd/transfer boundary,verify descendant cleanup including new sessions,and provide only approved task dependencies. It must use the same official tool schema/Verifier and immutable candidates. No boolean-only permission to skip these checks is provided.

GPU deployment promotion therefore remains pending. The next useful CPU work is one integrated official Runner/native-baseline deployment of this proven route; do not repeat Landlock or redesign a new Sandbox framework. New GPU allocation still requires scoped authorization and runtime proof. The normal Verifier remains trusted,separate,with evaluator overlays never copied into Agent root. Destroy the Agent execution environment before trusted native verification.

## Requests, recovery and development record

Exactly2 new CPU SaveKernel requests:one per unique slug,CAP01 and CANARY01. Both durable controllers retained UNKNOWN_STOP after strict ref parsing; independent read-only ID/owner/slug/version/source/payload confirmation established the existing version and COMPLETE state. Neither claim/events were rewritten,and no save was repeated. Each output is pinned by version1 before/after download,SHA/size and CRC. Raw archives are outside public Git; only owned synthetic evidence/safe metadata are newly published.

Before CANARY01 dispatch,a nested child-program compilation check caught an unterminated string literal in the preliminary build. The raw-string correction and recursive compilation test were made before freeze commit `a7cac4d`; no failed Notebook was overwritten or retroactively marked PASS. A preliminary history audit also rejected existing Windows CRLF checkout forms; the corrected audit records those separately and compares normalized Git blobs without rewriting any historical file. Candidate ZIP checks always use exact raw bytes.

Primary background: [Docker execution security](https://docs.docker.com/engine/security/) and [network none](https://docs.docker.com/engine/network/drivers/none/). The decision above is based on actual deployed commands and access results,not those documents alone.
