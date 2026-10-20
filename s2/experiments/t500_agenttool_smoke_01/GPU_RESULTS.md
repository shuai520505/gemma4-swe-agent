# S2-T500 single-task real GPU result

Real Gemma4 31B QATv2 repaired public task rich_3471: original native Phase2 resolved=true, test_exit_code=0,108 passed. This is one exploratory development-task success, NOT a Kaggle leaderboard score or an architecture comparison. EGV was never invoked; an autonomous dual-Agent feedback loop was NOT demonstrated.

## Frozen identity and execution

- Experiment: S2-T500-AGENTTOOL-SMOKE-01; independent of both eight-task drafts. Only one GPU Save Version/run, no rerun or substitute task.
- Pre-inference Git commit:2a7bc58; branch feat/s2-t500-gpu-smoke.
- GPU Notebook: https://www.kaggle.com/code/wudangdexiaodoashi/gemma4-s2-t500-smoke-gpu01 version1, COMPLETE. CPU gate: gemma4-s2-t500-smoke-cpu02 version1, COMPLETE.
- Deterministic metadata-only selection: first already-CPU-eligible task in old24-task pool order outside all8 reserved pairs. Selected rich_3471, base e2a982d5ea747f0deb7f78e8eaa5b4be7d9194cf. No reference repair was read or provided; exact Issue/snapshot/test-record hashes in protocol_cpu02.json. This task is now exposed and must be excluded from any future claim of unseen evaluation after tuning on this report.
- Frozen submission ZIP13968b67844d1041bfb79b9f11fc21ae66fb36aee5b00d3b91c526d5d35da329; Main/child config and Prompts unchanged.31BQATv2,4L4/TP4,context32768,output16384,thinking4096,seed17; sampling/include_thoughts omitted. Shared500s/60 charged tools, command120s.
- CPU01 was only prepared, never uploaded: a local time-admission equality test incorrectly used311s rather than310s. Corrected test and separate CPU02 preparation passed; original prepared files retained. CPU02 exercised actual official Compiler/ADK Runner/tools/failed assertion/Main correction/retest/submit using mocked HTTP, then clean native rich baseline107pass/1assertion failure/0errors. CPU mock success is not model-reasoning evidence.
- Runtime uses the byte-frozen CPU-accepted worker, HTTP lifecycle observer, context guard, native Phase2 capture and nested observer. New code schedules exactly one arm.600s startup and300s install caps constrain infrastructure only; registered Agent budget remains500s.

## Observed results

| Metric | Observed |
|---|---:|
| Official resolved / test exit | true /0 |
| Original Phase2 |108 passed,0failed,0errors |
| Agent elapsed |500.015827s, native deadline reached |
| Native TaskResult duration |514.046018s |
| Worker elapsed |528.480954s |
| Main model events / EGV model events |50 /0 |
| HTTP dispatches / responses / cancelled |56 /55 /1 |
| Main requests / compression requests |50 /6 |
| Charged tools / actual tool starts |50 /50 |
| EGV delegations |0 |
| Explicit submit_patch / get_status |0 /0 |
| Patch capture |native unsubmitted-working-tree fallback,2248bytes |
| First production edit completion |463.672951s |
| Tools before production edit |45 |
| Failed tools |4 |
| Exact repeated read_file requests |3 |
| Maximum admitted input |8972tokens |
| Received prompt/completion/total tokens |301198 /15796 /316994 |
| Usage complete |false; final cancelled request usage=null |
| Full dual-Agent loop |absent; closed-loop rate undefined, denominator0 |

Native total_tokens=0 is retained unchanged in official_result.json; it does not describe observed HTTP consumption.50 Main requests have50 usage-bearing responses totaling300176tokens. Six compression requests have five received responses totaling16818tokens; the sixth is cancelled at deadline and its missing usage is not imputed. No actual EGV request occurred. Model events, HTTP dispatches and charged tools are different counts.

## Actual tool timeline and mechanism audit

Pointers below are within results/gpu01/runs/01-rich_3471-B/nested_audit.jsonl. Full commands/results, changed-file hashes and timing are in results/gpu01/TOOL_LEDGER.json.

| Agent seconds | Evidence | Observation |
|---|---|---|
|~12 |line15–16 |Main already reads append_tokens implementation. This establishes access to the eventual repair location, not proof the model correctly understood the issue. |
|137.75 |line71–72 |Writes reproduce_issue.py; this is a diagnostic file, NOT a production edit. |
|159.06 |line75–76 |Runs diagnostic against workspace rich.text; printed real TypeErrors but caught exceptions and exit0 do not constitute a passing behavior assertion. |
|279–281 |line103–108 |Creates another diagnostic repro.py and catches/prints TypeErrors. Repeated append_tokens grep occurs four times overall. |
|463.52–463.67 |line183–184 |Only production edit: reject non-str tokens; strip project-defined control codes; compute spans/length from sanitized content. Successful exact edit and source hashes recorded. |
|465.34 |line187–188 |Runs nonexistent tests/test_text_repro.py: exit4,0collected. |
|476–479 |line191–196 |Creates four custom tests, then real pytest returns3passed/1failed. Failure assumes NUL must be stripped; existing rich/control.py strip list is7,8,11,12,13 and excludes0. This is a test-assumption mismatch, not evidence that official repaired behavior failed. No claim of complete behavioral correctness beyond native coverage. |
|485.31 |line199–200 |Reads rich/control.py after the custom failure. No subsequent production revision or successful retest before deadline. This is investigation, not a completed counterevidence-elimination loop. |
|500.016 |events.jsonl / agent_boundary.json |Native deadline cancels the in-flight compression request. No explicit submit/diff review; native working-tree fallback captures Patch. |
|after deadline |phase2.junit.xml / official_phase2.log |Independent original verifier applies fallback Patch in a clean sandbox;108tests pass. |

EGV schema was present in all50 actual Main HTTP requests alongside six organizer tools. Absence of delegation is a model behavior observation, not a missing schema/config explanation. No EGV discovery, delivery, Main response to EGV, or EGV retest exists. H1/H2 therefore remain unsupported on real Gemma, despite repair success. H3 is untested: there is no concurrent control.

The successful production edit occurs after300s in this particular trajectory. That is a signal that more time provided an opportunity on this run, not proof that S2-300 would fail: behavior may change under a different declared budget. A500vs300 causal claim needs a separate matched comparison.

## Patch quality and source provenance

latest.patch and official_result.json retain identical native Patch text. It changes rich/text.py and includes two leftover diagnostics,repro.py and reproduce_issue.py. The temporary tests/test_text_repro.py existed in the Agent sandbox but is absent from the native Patch; no test content was removed by this analysis. No explicit final diff/whitespace check or removal of diagnostics occurred.

Phase2 executed the original tests/test_text.py command; native_command_unchanged=true in phase2_command.json. Original JUnit was captured before sandbox stop:SHA43bc54d35e28816e19ae76f1e1f2e27e712ea2cb2aad1eab9f56b462108306fe. The native verifier imports its own workspace rich/text.py SHA b041a507e6a069f0fb9da43cddf012b0668fee0b9f06ad2ffe5201736086215b, matching captured modified production bytes. See import_audit/e21d4859ca8a4690b5429b181b332009/1990-exit.json. The model's custom test also executes workspace source; it does not silently validate a system-installed package.

## Cancellation, cleanup and evidence

Final HTTP request241d4d0a98094357ba511026fa4d4d03 is a tool-free compression request, with real cancelled terminal and null usage. The early worker http_observer_summary.json conservatively says unexplained_cancellation because it is computed without deadline proof. This raw record is preserved. Final research_audit.json applies the registered deadline proof (observed500.016s plus verified cleanup) and explains that exact cancellation; it does not ignore a missing response or invent usage.

After task completion the server reports zero running/waiting requests for three consecutive snapshots; all7 observed server process-tree PIDs terminate, no forced kill, no remaining sandbox. These are scheduler/process reclamation observations, NOT a request-specific backend abort receipt.

Raw archive SHA ee3651b4ca76b8a226a9f48ddb7e614add3bd32d3a77bcf32d37b13dd01425e0 (7372413bytes),444 manifest entries; nested run archiveSHA c330131c80f54a1d337e18a45bd0058f07c4a5b14e3ba8be1480207f4726f65d,128entries. CRC and every manifest digest verified. CPU rawSHA2f62db47c19ce5462d11f19213f7b941f3dea50461ab961e28a18f4b56a386b2,341entries. FINAL_AUDIT.json and audit_complete.py reproduce read-only checks. Existing frozen candidates, Prompts, ZIPs and original experiment records remain unchanged.

## Resource measurement and decision

Platform log spans~1115.25s, about18.6minutes; it is a wall-clock proxy, not the500s Agent budget. Approximate4-GPU device-time proxy is1.24device-hours, not a hardware utilization measurement. Kaggle quota API raw values changed from18574.56.0s to20805.644.0s (format malformed in SDK), an apparent2231.084quota-seconds, approximately2× wall clock. About794.356reported quota-seconds remain; no further GPU runs launched. Platform GPU accounting cannot be assumed equal to wall time or4×wall; future resource gates must calibrate the actual machine charge. The prior resource gate disclosed this unknown and backend admitted the single2700s reservation; it did not guarantee a full45minutes would fit quota. The actual run completed and finalized.

- Infrastructure: GO for this completed run, with real model routing/context/HTTP/native Phase2/provenance/cleanup evidence.
- Single-task repair: observed success; no overall success-rate or new leaderboard claim.
- Autonomous dual-Agent loop: NOT_DEMONSTRATED, EGV calls0. There is no child permission/isolation performance evidence when no child ran.
- Full16-run study now: NO-GO, quota insufficient and the desired mechanism absent on this smoke. Both eight-task frozen drafts remain unexecuted and unmodified.
- Minimal next research: first specify a separate version if changing delegation/closure timing. Test a bounded first-Patch delegation plus enough revision/submit reserve; retain current frozen candidate and this negative mechanism evidence. Do not claim a prompt change is proven, do not combine it silently with budget changes. A separately authorized small real-Gemma mechanism check should precede investment in16runs. No new candidate is implemented or run here.

As of2026-10-20 12:57Beijing, separate formal submission57402336 still returns API PENDING with no Public Score (UI may show Scoring). S0 remains the only confirmed leaderboard score0.13. This task success does not replace that score.
