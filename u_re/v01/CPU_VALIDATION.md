# Official Linux CPU acceptance

CPU02 v1 COMPLETE: **110/110 test methods passed**, no failures/errors/skips. The existing entry point actually ran71 methods (38 original official API/tool tests,5 static tests,28 S1 tests); the folder name legacy77 is a historical label, not the count. The new suite ran39:13 U-RE Runner methods,3 package tests,10 HTTP lifecycle tests and13 structured Verifier tests. Compiler/empty-State gates for both candidates and CPU tokenizer measurement are additional explicitly recorded checks, not extra test-count inflation.

Commands: `python -m u_re.v01.prepare_cpu cpu02 full`, `python -m u_re.v01.launch_cpu cpu02`. Saved wudangdexiaodoashi/gemma4-u-re-v01-cpu02 version1 uses pinned official Linux image, enableGpu=false, enableTpu=false, offline inputs. Exact Notebook/payload SHA and one-save HTTP receipt are in registrations/cpu02_build.json and results/cpu02/SAVE_REQUEST.json/SAVE_RESPONSE.json. Within that Notebook: `python -m u_re.v01.cpu <new-output> full`. Collection downloads the canonical original ZIP, verifies CRC and every manifest entry; source is preserved inside raw.zip. One oversized output-listing page request returnedHTTP400; recovery read the same completed version with default page size, without compute rerun. CPU01 failures and its distinct frozen source remain unchanged.

Actual public packages: swegemma0.2.11,adk-submission0.2.13,adk-eval-core0.1.0,google-adk1.36.1,google-genai2.11.0,litellm1.82.4,pytest8.4.2,transformers5.13.1. GPU count was asserted0. No model server/inference ran; only HTTP model replies were scripted. Native Compiler, empty-State ADK Runner, tool schemas, Git edits, assertions, budget counting and submit were real. Observers do not return fake tool results, end invocations or change scoring logic.

| Requirement | Actual evidence under results/cpu02/validation |
|---|---|
| A basic repair/test/diff/submit, both arms | cases/noegv_basic and full_basic, returned.patch/native_trace.json |
| B failing real assertion→production revision→same assertion passes | cases/full_closed_loop; CPU_MECHANISM_EVENTS.json joins actual ordered events |
| C wrong self-test expectation | cases/full_wrong_test: wrong assertion fails, correct production retained, SPEC checked and correct checks pass |
| D no-progress | cooperative case avoids unchanged repeat; repeat_negative deliberately repeats and offline audit detects1; it is not Runtime-blocked |
| E closure and retry | basic cases finish after one successful submit; submit_failure uses an actual temporary Git-metadata failure, recovery and successful retry |
| E negative termination guarantee | full_post_submit_negative executes a real check and a second identical successful submit after first success; Runtime does not immediately stop per-tool |
| F300s native deadlines | NoEGV 300.072975s; Full 300.100224s. Both unfinished HTTP replies cancelled with usage=null and patch persisted |
| F60 counted operations | both exact_tools cases reach60; extra counted edit denied, free status/submit still work |
| F120s command | actual maximum command 120.073350s; real process absent and delayed write absent after wait |
| F near closure/cancellation | ten-second supplemental fixture submits near its end; separate actual external CancelledError propagates and patch survives |
| G package and request | three-member CRC/hash equality, six legal tools, no child, full Prompt in actual HTTP system instruction, Issue JSON retained |

The unchanged frozen HTTP auditor only admits native deadline cancellation; the deliberate external-cancel fixture records the real boundary and leaves that auditor's unexplained_cancellation flag intact instead of falsely calling it a native deadline. Missing-response usage is null/partial. Scripted usage is synthetic and is never reported as Gemma Token cost. Ten-second supplemental timing is not substituted for the two300s measurements. Private scoring scripts/inference.py is not available: candidate YAML is matched to actual EvalConfig/boundary values, not claimed to have run through the private scoring loader.

CPU03 is a separate evaluator-only task-identity/clean-baseline inspection; it runs zero Agents/models. Its results do not count toward U-RE repair rate or the110 scripted-test total. Admission=False; details in results/cpu03/validation. No task is replaced if its gate blocks. These baseline tests are not shown to either candidate.

**CPU_PASS is compatibility and observability evidence. GPU_ALGORITHM_VALIDATED remains false.** Compliant Mock scripts do not prove autonomous evidence selection, error recognition, soft phase timing, no-progress judgment or reliable closure by real Gemma. The two arms are not algorithmically compared using scripted responses.
