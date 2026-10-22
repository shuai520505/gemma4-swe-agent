# ISOLATION_VERIFIED_TASK_ADMISSION_PENDING

This is **CPU synthetic filesystem-boundary evidence**,not GPU readiness or a Gemma repair result. GPU remains **GPU_NO_GO / NOT_AUTHORIZED**. The latest human Notebook rules authorized the2 CPU probes below; prior Landlock failures and UNKNOWN_STOP dispatch events remain unchanged.

| Attempt | Frozen source commit | Notebook/version | Platform result | Raw archive SHA256 |
|---|---|---|---|---|
| ISOLATION-CAP01 | `2cd68e1` | 140209916/v1 | COMPLETE | `2e79b19ed3019bfd0f3f6f3a0e1ae9d5633c856e2415cca95b63c1e3d6f67e61` |
| ISOLATION-CANARY01 | `a7cac4d` | 140211037/v1 | COMPLETE | `50f84d088c3fc3ba4cd471dcfd7ca9806c778fa46855bd5046cf4ca6fad1897d` |

Each has exactly1 SaveKernel dispatch. Both resources were independently confirmed by ID/ref/owner/version/private/CPU-only metadata plus semantic Notebook JSON and exact embedded payload equality; output reads pin latest to1 before/after. Frozen Notebook byte SHA differs from platform reserialization; no false byte-equality claim. Original raw ZIPs/logs remain outside Git under `private-evidence/u_re_isolation_cap01/read-04` and `private-evidence/u_re_isolation_canary01/read-03`; archive SHA/size/member-count/CRC and owned safe evidence are published. No real task baseline,Agent session,model call or formal submission occurred in these attempts.

## Q1–Q12

**Q1. Why Landlock unavailable?** Prior actual ABI syscall returned ENOSYS38. Kernel absence versus filtering/emulation is unresolved; the old failure is not rewritten. New CAP01 establishes mount/user unshare EPERM1 and DockerException on the configured Docker client,while chroot and UID separation succeed. See `cap01/derived/CAPABILITIES.json` and `ISOLATION_IMPLEMENTATION.md`.

**Q2. Existing official/S2 isolation?** Official swegemma0.2.11 has a Docker ContainerManager worth reusing when a daemon/proxy+approved image exists. Existing S2/U-RE research workers used host SubprocessManager; that is not a demonstrated filesystem boundary. Exact source/wheel identities and method line ranges are in `SOURCE_AUDIT.json`. No working Docker endpoint was demonstrated on this CPU deployment.

**Q3. Supported alternative?** Yes:actual Kaggle CPU chroot+separate UID/caps/no_new_privs+closed FDs+seccomp,with a copied minimal runtime and no host mounts. `chroot_exec.py` and `chroot_boundary.py` implement the enforced path. It is a synthetic six-tool adapter; full task dependencies,official Runner lifecycle and GPU deployment promotion are still pending.

**Q4. Real canary results?** CANARY01 passed all12 recorded checks:workspace read/write;research/evaluator/other-arm absolute read denial;traversal;symlinks;descendant read;inheritable FD;no host proc/input;parent memory;network;official read_file symlink denial;edit/target+old-test/diff/submit;host canary integrity. Root cleanup succeeded. See `CANARY_RESULTS.json` and `canary01/derived/{official_tool_events.json,tool_processes.json,cpu.log}`. Untrusted daemon/new-session escape cleanup,real task dependencies,native verifier integration and GPU environment tests are **NOT_RUN**; no claim of kernel-exploit containment.

**Q5. Six tools/Workspace preserved?** Yes,real swegemma functions get_status/run_command/read_file/write_file/edit_file/submit_patch,one successful production toy edit and submit,12 native charged calls. No schema/official tool source changed. Context reports300s/60charged/120command. This run does not independently retest those exhaustion boundaries or real model compliance. See actual events and scope in `CPU_CANARY_PROTOCOL.json`.

**Q6. Candidates unchanged?** NoEGV `2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608`;ActionFirst `70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8`;Full `887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821`. All ZIP CRC/member hashes and matching YAML audited in `INTEGRITY_MANIFEST.json`. Historical content unchanged; existing Windows CRLF checkout differences are separately recorded,never rewritten.

**Q7. Updated task exclusions/rank?** Static freeze completed before any new native task baseline in commit `2cd68e1`.129 metadata rows;79 inherited exclusions+8 preserved old Pilot reservations=87 excluded;42 remaining. Old reservations are not reclassified as executed models. PR19 deterministic selector/prefix unchanged. `TASK_POOL_FREEZE.json` contains provenance,full order and exact source hashes. No reference/test body/model outcome was used for ranking.

**Q8. Two qualified tasks?** No.0 new native baselines;0 admitted. First prospective IDs are fastapi_9425,fastapi_15023,then the other6 in the JSON. All remain **NOT_ADMITTED**,with snapshot/overlay SHA null until source binding. Max8,first2 eligible,ABBA,environment/conditional-target-failure handling and STOP are in `CPU_ADMISSION_PLAN.md`. No claim these are independent repository samples.

**Q9. Reuse GPU infrastructure?** Existing137 shared S2 bindings,VllmServer/Config,LiteLlm/ADK/Compiler,s1 worker,native Verifier/JUnit,HTTP/idle/supervisor/export/cleanup and one-shot save/read-recovery are retained. `GPU_EXECUTION_PLAN.md` identifies them. The chroot adapter is not yet a drop-in GPU worker; a real integrated Runner/dependency/cleanup CPU acceptance is required. No new GPU Notebook was built/saved and no S2 answers were imported.

**Q10. Model/resources/time/tokens?**8 model+41 official wheel SHA pins from existing SMOKE_PLAN;historical4L4/TP4/CUDA12.8/vLLM0.19.1. Current raw quota at2026-10-22T12:20:12Z is108000-24955.714-0=**83044.286 report seconds**,above20600 conservative threshold. Capacity,memory,actual hardware/kernel,model/ABI rehash and10000s approved window remain runtime checks.8640s total is a component planning estimate,not measurement. Candidate300/60/120 and generation16384/4096/17 unchanged. No Gemma usage exists; do not invent tokens. See `resource_snapshot`,`GPU_EXECUTION_PLAN.md`,`GPU_PREFLIGHT.json`.

**Q11. Actual execution counts?** **2 CPU Notebook saves/runs**,1 version each;**0 GPU,0 Gemma,0 Agent,0 real task baselines,0 formal Submissions**. Original durable events and all read-only recovery ledgers are retained per attempt. One limited formal status query foundFull57505115 stillPENDING/PublicScore null,independent of ActionFirst. S0 remains0.13;oldT50057402336 COMPLETE/null includes platform runtime-exceeded error. Nothing was resubmitted.

**Q12. What remains?** Promote the proven CPU chroot data boundary through the actual single-Agent Runner with approved task dependency staging and robust descendant/cancellation cleanup;screen at most8 precommitted IDs with unchanged native verifier and bind first2 eligible identities;freeze ABBA deployment/source hashes;then recheck model/device/quota/window/HTTP-idle/observability gates and obtain explicit scoped GPU authorization. These are concrete remaining gates,not a reason to repeat Landlock or redesign the inference framework. **No real ActionFirst effect evidence yet.**

## Gate decision

- Candidate integrity:GO.
- CPU synthetic six-tool filesystem canary:GO on the recorded CPU deployment.
- Full integrated Runner/task dependency isolation:promotion pending.
- Native task admission:NOT_ADMITTED / not run.
- Quota threshold:PASS for the timestamped snapshot;actual GPU/window NOT_CONFIRMED.
- GPU execution authorization:NOT_AUTHORIZED.
- Algorithm evidence:GPU_NOT_TESTED;no repair-rate claim.

Next useful computation is a versioned CPU integrated Runner/native-admission build preserving this boundary and frozen order. GPU remains blocked until that work and a separate scoped authorization are complete. New user CPU permission is recorded;no further permission is needed merely to investigate CPU capabilities within that scope. Ordinary Notebook research permission does not authorize formal Competition Submission.
