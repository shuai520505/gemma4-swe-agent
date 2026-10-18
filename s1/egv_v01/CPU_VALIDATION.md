# Official Linux CPU/Runner acceptance

Accepted run:gemma4-s1-egv01-cpu03,version1,COMPLETE. **115/115** actually pass,
zero failures/errors/skips:the unchanged113 infrastructure/API regressions plus
two new candidate tests. This is CPU compatibility,not Gemma inference or a
repair success rate. The seven semantic review cases are human reviews and
are not added to this test count.

The new complete path uses official Compiler,real ADK Runner,an empty session
state,official six-tool creation,LiteLLM/Guard and mocked HTTP. Control and EGV
each take two real Runner turns,including an official get_status function call
and returned tool message. Mock reasoning history is preserved;the counter's
serialized message body agrees with the outgoing client body. The added Prompt
is fully present in the actual HTTP system message. The Issue's literal JSON
example survives. Six schema objects are exactly equal across arms;output16384,
thinking4096,seed17 and omitted sampling/include_thoughts are unchanged.

The package test checks exact ZIP SHA/member bytes,three permitted files,
root agent.yaml,unchanged YAML/eval budget,unaltered S0 prefix,103-word addition,
no added interpolation braces,official directory validation and compilation.
Compiled instruction and Runner-rendered system are saved separately under
validation/candidate. No external policy or research Python enters the ZIP.

The113 frozen tests rerun on this exact source payload,including actual HTTP
cancellation propagation/terminal audit,context boundaries,Patch checkpoints,
Agent/Verifier/outer timeout,cleanup delay,wrong-package provenance and original
JUnit A–G classification. No frozen implementation was edited to pass them.

## Preparations and retained failures

| CPU version | Actual outcome | Change before next version |
|---|---|---|
| cpu01 | frozen113 pass;full Runner candidate test passes;package test errors because upload omitted new submission.zip | include existing frozen ZIP in research payload only |
| cpu02 | frozen113 pass;full Runner passes;package/compile comparison fails on CRLF versus LF | test compares official universal-newline text semantics;raw package hashes unchanged |
| cpu03 | frozen113 +2 candidate tests pass;all separate read-only attribution completes | accepted final source;no Prompt change |

Official !include text loading normalizes actual CRLF to LF. Package/member
bytes stay unchanged. The comparison normalizes only those physical line
endings,not words,whitespace within lines,JSON escapes or template content.
Full Runner already passed in the earlier attempts;this was a false strict
byte expectation in a supplemental test,not an ADK candidate rendering error.
All three preparations and raw error logs are retained,never spliced into one
successful run. They are not three algorithms or model experiments.

Raw ZIP SHA256:

- cpu01:5662a4063d64be1340bf49564b19f649e25fc99eea7cae0236a494acc41c4f5d
- cpu02:aebe4f862d426f9bf23cde99cc2e82d1161e94c314963773b085b289c3c91788
- cpu03:e0625e923ac128a33f762062f23b050156b9be5be256a4f3696ed129906a53e6

CPU03 CRC and895 manifest entries verify. registration_cpu03.json pins every
uploaded source/member/ZIP and the official model/task Wheelhouses. Full source
and all113 regression evidence are inside each raw archive. Companion extracted
logs/reports are convenience copies,not replacements. A disconnected download
may be retried read-only;it never causes a computation rerun.

Separate native read-only reproduction uses only the known public Rich task,
original tests and observed historical Agent Patches. It is not part of the
115 test count,an EGV repair result or a new scoring experiment. No GPU,LoRA,
new model generation or formal Kaggle submission occurred. Actual versions
remain swegemma0.2.11,adk-submission0.2.13,google-adk1.36.1,litellm1.82.4.

CPU03 captures pure compiled instruction SHA4942a480f7ad6c4ee3d1d2178a5f799404a03d613b952d044f2174dadec3647f and actual Runner-rendered system SHAd1092f2096c84e293d9b297125646b221923e20b4fdbd3f7ce664afd0db44ac9. All148 execution-source/member files match registration;the preexisting unused V1 checkout CRLF/archivedLF distinction is preserved,as in the earlier structured study. Both actual payloads use its pinnedLF bytes;no old Prompt was changed.
