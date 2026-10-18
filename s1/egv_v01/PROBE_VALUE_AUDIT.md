# Verification value audit: actual frozen Control/E3

All16 behavioral verification attempts are enumerated below (7Control,9E3). Searches/reads are supporting investigation,not tests. This is a read-only audit of historical Gemma behavior,not new inference or an EGV model experiment. Times are actual call-to-result intervals after native Agent start. Full commands,source/probe hashes,ADK line links and provenance are in analysis/verification_actions.json.

| Arm/tool/time(s) | Executed command | Target and outcome | Assertion/new information | Observed next action |
|---|---|---|---|---|
|control/12/81.260–81.699|`python3 repro.py`|yes; valid table/output truncation;exit1|none; prints then invalid Console.export;new negative evidence plus independent script API error|No production correction until tool23; invalid export remains|
|control/24/167.102–167.441|`python3 repro.py`|yes; restored table visible before script error;exit1|none; print only;new post-edit content evidence, incomplete script|No export correction or further production repair|
|control/25/171.209–172.536|`pytest tests/rich/markdown.py`|no; nonexistent test path;exit4|none; zero tests collected;actionable path error; not a correctness check|find tests at26 then correct command27|
|control/27/198.836–200.912|`pytest tests/test_markdown.py tests/test_markdown_no_hyperlinks.py`|yes; existing tests execute changed module;exit1|existing pytest assertions;new regression evidence,4fail1pass|same command repeated28|
|control/28/203.722–205.742|`pytest tests/test_markdown.py tests/test_markdown_no_hyperlinks.py`|yes; same file/set/state;exit1|same assertions;redundant as executed; desire closer failures did not change visibility|repeated29 under claimed cwd hypothesis, but actual command unchanged|
|control/29/209.545–211.537|`pytest tests/test_markdown.py tests/test_markdown_no_hyperlinks.py`|yes; same file/set/state;exit1|same assertions;redundant as executed; new cwd suspicion without cwd/env intervention|read original tests30 then change selector/verbosity31|
|control/31/225.126–227.110|`pytest tests/test_markdown.py -vv`|yes; existing tests execute changed module;exit1|existing pytest assertions;legitimate narrower verbose diagnostic; unresolved failures|returns to source searches; no production edit or submit|
|e3_locate/9/51.010–51.451|`python3 reproduce_issue.py`|no; pipe paragraph lacks header separator;exit0|none; plain print/export_text;input does not exercise target; exit0 not repair evidence|different text input10,still no table|
|e3_locate/11/66.349–66.680|`python3 reproduce_issue.py`|no; same missing table grammar;exit0|none; plain print/export_text;changed input reasonably tests fragment hypothesis,but target invalid|adds handler debug print12|
|e3_locate/13/79.919–80.252|`python3 reproduce_issue.py`|no; changed handler debug print absent;exit0|none; plain print/export_text;absence provides route counterevidence; repeat justified by instrumentation change|fixes probe grammar14|
|e3_locate/15/88.012–88.343|`python3 reproduce_issue.py`|yes; debug calls prove handler receives fragments;exit0|none; print/export_text;new valid negative evidence; only last fragment survives|later repair edits28/29|
|e3_locate/30/192.600–192.936|`python3 reproduce_issue.py`|table constructor yes; on_text blocked by init failure;exit1|none; real AttributeError;new counterevidence against repair initialization|tool31 swaps assignment order|
|e3_locate/32/226.629–226.969|`python3 reproduce_issue.py`|yes; complete table content restored;exit0|none; print/export_text;new post-correction positive content evidence|inspects tests and ANSI representation|
|e3_locate/41/260.334–260.664|`python3 test_output.py`|yes; ANSI styled fragment visible;exit0|none; prints repr;new style representation evidence beyond plain text; not assertion proof|adds weak substring test42|
|e3_locate/43/269.246–271.254|`pytest tests/test_markdown.py`|yes; original file plus new weak test;exit1|existing assertions plus new substring checks;new regression evidence,3fail2pass|selects only new test44; no production correction|
|e3_locate/44/275.765–277.203|`pytest tests/test_markdown.py::test_markdown_table_inline_styles`|yes; narrow valid styled-table input;exit0|assert a/b/c substrings,not exact style/output;legitimate isolation of new test,positive but insufficient old-behavior scope|cutoff before explicit submit|

## Evidence boundaries

All actual Python/pytest checks except the nonexistent path have passive import records tying rich.markdown execution to the workspace realpath and SHA. Module execution is not function coverage. Valid table input plus rendered table supports handler reach;E3 debug output at15 directly records handler calls;constructor traceback30 directly proves failure before on_text. Early E3 pipe-paragraph output and absent debug at13 demonstrate the missing route. No invented function hit count is assigned to the historical runs. New diagnostic tracing,if obtained,is a separate CPU investigation.

Control27→28→29 has unchanged production code,input selection and actual command. However its native reasoning does contain a new working-directory suspicion before29. The defect is that the repeated action does not intervene on that suspicion or output truncation. It is inaccurate to say that no new hypothesis was mentioned. Tool31 changes selector and verbosity and is a reasonable diagnostic repeat. E3 checks11/13/15 also change input,instrumentation or route;they are not mechanically classified as pointless repetition.

Both remaining official failures already occur on clean baseline. Neither Agent knew the later evaluator comparison. A failed test after editing is useful counterevidence even when later attribution finds a preexisting cause. EGV must inspect it,not skip regressions based on task labels. The new weak E3 test has three character-presence assertions;passing it is not exact rendering/style coverage.

Neither arm explicitly invokes submit_patch. Both DO retain native fallback Patches which apply and receive original Phase2 evaluation;"no explicit submit" is not "no Patch". Each retains a reproducer. Control does not repair its nonexistent Console.export call;E3 removes the debug print and corrects its real init AttributeError. Full original Phase2/JUnit/Patch remain at the historical paths and are unchanged.

The snapshot Agent test file and final evaluator overlay are different states. A golden output assertion can encode earlier behavior;its post-edit failure requires diagnosis against the Issue rather than automatic Patch reversion or assertion weakening. This audit does not assume that every failing old test is a newly introduced regression.
