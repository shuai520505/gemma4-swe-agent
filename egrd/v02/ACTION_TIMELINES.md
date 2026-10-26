# Observable action timelines

Times are seconds from each actual Agent start. Event indices are zero-based in
the archived `execution/runs/<session>/agent/adk_events.jsonl`. All 40 actions
and response times/hashes are in `ACTION_OBSERVATIONS.json`. Model text was
read privately as emitted reasoning, not assumed to reveal unobservable beliefs.
No reference fix or new evaluator assertion was consulted for these alternatives.

## C: 04-fastapi_14459-C

- Events 0/2/4 search OAuth 2/dependency/OpenAPI symbols.
- Event 6 returns the OpenAPI implementation window at 18.982 s.
- Events 8/10 return consecutive dependency utility windows at 32.531/35.381 s.
- Event 12 returns the dependency model at 44.463 s.
- Emitted text at event 8 proposes flattening/cache handling; event 14 develops
  a conditional scope/cache-key hypothesis but notices that visited state is
  per flattening call and new dependency objects are constructed. It explicitly
  asks where sharing/reuse could occur. This is an unresolved hypothesis, not
  a validated cause or ready patch.
- Event 14 requests another 150 line source window, returned at 130.278 s after
  the long model response. The next generation is blocked at 130.349 s/input 15989.

No executable reproduction, scratch write, production edit, Skill call or submit.
About 111.37 s elapses from the first implementation-window result to rejection.
First post-read input 5906 grows to 15989 (+10083 tokens). This is combined history
growth, not 10083 isolated source-output tokens.

## B: 05-fastapi_14459-B

- Events 0/2/4/6 follow the same initial search/read pattern, first implementation
  window returned at 12.143 s. Event 8 names flattening as a possible explanation.
- Event 10 returns dependency flattening code at 26.468 s; event 12 continues the
  file at 32.866 s, overlapping the earlier window by only one line.
- Event 14 searches caching references; event 16 reads runtime dependency solving,
  returned at 39.767 s. Event 18's emitted text recognizes this is runtime resolution
  rather than OpenAPI generation and redirects toward dependency cache keys.
- Event 20 returns the model/cache properties at 58.262 s. Event 22 considers
  conditional inherited-scope identity, then questions the proposed global-cache
  explanation and searches callers instead of treating it as established.
- The next generation is blocked at 80.648 s/input 15684 after the event 22 result.

No reproduction, scratch write, production edit, Skill call or submit. About
68.51 s elapses after the first implementation-window result. First post-read
input 5906 grows to 15684 (+9778). Continued inspection supplied new source; it is
not automatically pointless because the critical sharing/causal question remained.

## A: 06-fastapi_14459-A

| Event(s) | Actual result/time | Interpretation |
|---|---|---|
| 0,2 | File/directory discovery | Related navigation; overlapping purpose is not proof of zero information |
| 4,6 | Scratch written 33.879 s; execution errors 36.893 s | Invalid dependency declaration construction, not a framework defect witness |
| 8,10 | Scratch corrected 46.426 s; schema printed 49.072 s | Interior dependency still declared incorrectly; no assertion |
| 12,14 | Routes reordered 63.165 s; schema printed 65.766 s | Order is varied before the scratch graph is valid; weak/confounded evidence |
| 16,18,20 | One failed exact-string edit; scratch read 81.019 s; corrected 90.663 s | Model repairs its reproduction, not production code |
| 22 | Schema printed 93.364 s | Selected graph now displays expected scope information; no discriminating assertion |
| 24,26 | Scratch variant 118.317 s; schema printed 120.959 s | Related inherited-scope case, still no demonstrated defect or assertion |
| 28,30,32 | Targeted implementation searches 124.921 s onward | First concrete implementation excerpt, rather than path discovery |
| 34,36,38 | Utility window 133.008 s; caller search; model window 141.945 s | Source localization arrives near the eventual context stop |

Guard at 142.013 s/input 15607 prevents using the last source result in a further
generation. First concrete implementation excerpt→stop is 17.09 s; the first
read_file implementation window→stop is 9.00 s. Five scratch executions contain
zero AST assertions. No production edit or explicit submit occurs.

All source-change metrics exclude trusted snapshot deployment before Agent
start and diagnostic-file edits. The previously hash-locked PR33 outcome-blind
review is retained. This new autopsy is retrospective/outcome-known; it is not
misrepresented as a second blind review.
