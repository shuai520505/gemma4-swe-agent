# Paired S0 / SuperAgent development study

Compare the frozen S0 (observed public 0.13) and scored SuperAgent content (0.15)
on three already exposed development tasks. This is a complete-system contrast,
not a single-factor prompt ablation, independent confirmation or score forecast.

Fixed schedule: Django16333 S0→SuperAgent; xarray3095 SuperAgent→S0;
FastAPI14297 S0→SuperAgent. S0 retains300s/60tools/120s commands;
SuperAgent retains480s/28tools/240s commands/80turns. Generation settings,
tools and prompts are compiled from exact original archives. No LoRA/training.

The shared serving configuration uses the frozen Gemma4 31B QAT instance v2,
TP4 on four L4s, no prefix caching, no custom context guard. Both use the pinned
guide's ADK compaction15/overlap2/token14336/retention5. Historical exact scorer
equivalence is not established. Model generation is allowed only inside the six
independent native Agent sessions; any native compaction is part of its session.

Each task uses a separate locked offline wheel group. Isolated non-root chroots
prevent Agent access to host data or the separate check sandbox. A fresh base
must reproduce the original target failure while passing controls. Evaluate
submitted and retained fallback patches, with their identities kept separate.
Checks cover owned Issue-grounded targets/controls; broader regression and
canonical SWE-bench/official Native grading are not run. Semantic review remains
required. A local probe pass is not a competition score.

CPU setup failures are retained: wheel-local NumPy ELF resolution, asynchronous
Git-gc during archive creation, and old-xarray distutils availability. Runtime
fixes use locked wheel members, disable background GC in fresh synthetic Git
snapshots and expose setuptools' vendored distutils through a confined alias.
No reference repair/test overlay, Agent prompt or candidate archive is changed.

GPU attempt 1 stopped before model load: the supervisor precreated its output
directory, whereas the coordinator required it not to exist. Zero model HTTP
requests and zero repair sessions occurred; GPU allocation/setup may still be
billed. The corrected coordinator accepts the supervisor-owned fresh directory
and rejects existing results. CPU preflight now exercises this entry in a
separate subprocess and verifies rejection at the four-L4 gate without loading
a model. CPU revision 5 exposed a nested notebook asyncio issue in the new test;
revision 6 uses the same process boundary as the GPU entry. All attempts remain
preserved. A corrected batch is an infrastructure recovery, not an Agent rerun.

Private operational inputs are intentionally excluded: ISSUES.json contains only
instance_id/repo/base_commit/problem_statement selected from legitimate public
sources; paired_candidates/ contains exact S0 and scored SuperAgent archives;
the private EGRD development dataset supplies unchanged snapshots and wheel locks.
Do not add these raw inputs, model traces, generated checks or patches to this repo.
Reproduction requires those authorized inputs and the official pinned wheelhouse.
Run `python -m gemma_pair.cpu <new_output>` before any GPU use; the real entry is
`python -m gemma_pair.coordinator <new_output> <first_cell_monotonic>`.
Every attempt uses a fresh evidence directory. No selective model reruns or
automatic competition submissions are part of this study.
