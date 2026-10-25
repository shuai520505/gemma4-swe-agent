# Evidence inventory and access limits

The audit opened and CRC-checked 11 original archives and reconstructed 26 real-model sessions. `EVIDENCE_MANIFEST.json` records every consumed member hash, archive SHA, location, size and the number of consumed members cross-checked against an original embedded manifest. An archive hash is a byte-integrity check, not independent proof of historical provenance or correctness. Candidate packages inside the archives were matched to actual extracted Agent member bytes, not inferred from arm letters.

| Cohort | Real sessions | Tool actions / outcomes |
|---|---:|---|
| GPU03 | 4 | Two FastAPI tasks; 3 true / 1 false |
| V0.2b Batch1 | 4 | Two FastAPI tasks; 0 true / 4 false |
| V0.3 | 4 | Same two development tasks; 2 true / 2 false; both arms Action-First with different output budgets |
| CURE01 + CURE C1 | 3 | Owned synthetic migration task; 3 true; not independent SWE samples |
| S2 EarlyEGV | 4 | Rich/FastAPI; 4 true; 500s and optional AgentTool/compaction |
| S2 T500 | 1 | Rich; true; 500s |
| S1 output cap | 1 | Requests; native raw false, assessed null due 194 fixture errors |
| S1 localization | 1 | Rich; false; final summary 4 failed / 19 passed, no environment error |
| S1 structured | 2 | Rich; both false |
| S1 EGV | 2 | FastAPI; both false, one Agent-introduced SyntaxError |

Total 784 tool actions. One additional CURE worker failed before inference and is retained separately, never counted as a model repair failure. Unstarted paired arms, CPU scripted sessions, raw baselines and probes are excluded. The enumerated set is not claimed to be every experiment ever performed by this project.

Raw ADK calls/responses, HTTP requests/usage, tool traces, Agent-generated patches and original native results were accessible. Some older S1 archives lack standalone JUnit XML; their original phase2 execution text and TaskResult remain available. Exact tests, raw patches and hidden assertion text are not republished. No reference/gold patch was fetched. Native exception metadata was inspected to distinguish an Agent syntax regression from missing environment dependencies, not to design a task-specific repair.

Missing/limited evidence:

- Formal S0/Full/EGR per-task trajectories: unavailable. Archived official rows confirm COMPLETE 0.13 / 0.12 / 0.10; total scores cannot identify a reasoning failure.
- MEER: source, frozen protocol and scripted CPU reports are accessible, but no completed real-Gemma MEER result in the audited frozen PR31. Its optional Skill adoption is unknown. Existing external authorization/work-in-progress is not changed.
- PR27 Batch2 HTTP499 remains UNKNOWN; no reconstructed session or outcome is invented.
- Older source-hash observers are incomplete. Successful edit acknowledgements are weaker than hash-observed changes; the dataset records this distinction.
- Earliest internal hypothesis, semantic information gain for every action, and intermediate native correctness are not observable. Null is intentional.
- Original external snapshots/model weights were not downloaded again. Archived task identity records and executed candidate bytes were checked; this is retrospective provenance, not a new runtime admission.

Formal status archive SHA: `5742b63aaf2b3e8cb84eaccf3d771d7d54bdff01506e8c3e6c7058b28c467da9`. `SOURCE_AUDIT.json` contains the actual three selected official rows, organizer wheel/module hashes and candidate member hashes. CPU evidence is engineering evidence; offline interpretations are separately labeled.
