# Evidence-Guided Repair V0.4

The candidate replaces the119-word Action-First priority block with a237-word
evidence-guided block. Opening rules, triage, ordinary-test protection, budget
and closure remain byte-identical. agent.yaml/eval_config.yaml remain identical.
This is one instruction-strategy intervention, not an ablation proving each
sentence separately effective. No runtime decision controller is added.

Considered: append more instructions to Action-First (duplicated priorities),
rewrite the entire Prompt (unnecessary factors), or replace its strategy block
(chosen: auditable and reversible while preserving the tested scaffold).

The loop is: identify expected behavior and one unresolved question; choose a
cheap relevant observation; form a falsifiable local hypothesis; make the
smallest supported behavioral edit; check actual workspace execution and a
relevant assertion; submit the defensible patch. If static contract/source
evidence is already adequate, a failing reproduction is not mandatory before
every edit. Correctness still outranks early editing and deadlines are unchanged.

New priorities address observed failure modes: unchanged searches, reproductions
that catch failures or contain no assertion, invalid test paths, whole-suite
optional-dependency failures, and extra exploration after sufficient evidence.
They do not enforce a search/edit/test quota or hide a genuine failure. Broad
tests remain possible when justified by a concrete risk. Novel source reads
are observations, not automatically useful progress. Hypotheses need not be
written into long reports or new files.

All wording is task-independent: no historical task IDs, functions, evaluator
assertions, successful patches or reference fixes enter the candidate. This is
not the historical Full EGV block: no mandatory counterexample-search phase or
independent verifier Agent is added. The single model still uses only the six
official tools. No compression, output truncation, dynamic budget, training,
LoRA or model replacement is bundled into the treatment.

Both arms retain output16384, context32768/safety1024/input15360,
thinking4096, seed17,300s/60charged tools/120s command. V03's8192 treatment is
not inherited. Compatibility is assessed by real Compiler/ADK and actual model
request instruction visibility in CPU, then native synthetic TaskResult/JUnit.
Scripted CPU completion cannot establish instruction following or repair benefit.
