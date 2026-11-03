# Failure analysis
The eleven questions for every retained record are explicit in [FAILURE_DATASET.json](FAILURE_DATASET.json). There are no imputed semantic answers. Five EGRD-lineage/control traces were manually reviewed; all other records have mechanical action/patch/Native inventories with semantic UNKNOWNs. This limits cross-family root-cause frequency claims.

## Relevant code inspection did not ensure a repair
1. Skill V0.1 A Pylint: reads pylint/config/argument.py at legacy elapsed47.728s and again136.661/273.406; attempts repeated config reproduction. No tracked production change, no official submit; XML20cases/2failures/0errors.
2. Skill V0.1 B Pylint: reads argument.py49.012s, utilities64.009/68.948/164.913/261.336s. Repeats identical grep _splitstrip at158.320,208.351,276.820s. No production change, no submit; XML20cases/2failures/0errors. The repeated grep did not change its query; whether a reread added semantic information remains UNKNOWN. Skill calls0.
3. Skill V0.1 B Sphinx: reads parsers.py64.195 and rst.py69.504/134.690. Edits prepend_prolog, then reverses it. Raw source observer confirms transient tracked code change and return to baseline. Final diff is reproduction/generated docs, not a production repair. No submit; XML10cases/2failures/0errors. It is not established that the reverted patch ever worked. The inserted SECTIONING_CHARS reference was not validated. CLI/workdir failures and the4.7s clock discrepancy confound performance attribution.
4. Legacy V0.3.2 S0: reads UserCreationForm at18.675s, explores test environment, edits production only around the deadline. No submit and original target behavior remains failing in separate owned checks. Context/task runtime differs from Skill Pilot.
5. Legacy V0.3.2 B: reads UserCreationForm17.193s and ModelForm save32.920s, later edits tests, not production. Backend explicitly rejects32769 required tokens against32768 capacity. No submit. This is a witnessed context allocation failure, not proof of failed semantic reasoning.

Raw sources: archive/member hashes per session in HISTORICAL_EXPERIMENT_DATASET; current Pilot archive c04fa7872bd13eae46a8da482cc15b0fdebb25e8a20009a1b3ef203048d98759, recovered legacy archive67386d9aa8... (full hash in ARCHIVE_PROVENANCE). Legacy elapsed_s belongs to the recorder's clock, not the SDK deadline. Source-observer SDK-relative intervals are stored separately; never subtract incomparable clocks.

## Dominant observed signals, with appropriate denominators
Current active Skill B:2/2 did not activate Skill,2/2 did not submit,0/2 retained a production repair,1/2 made an issue-relevant transient edit. Both have raw Native false. This is a small failed engineering pilot, not an efficacy estimate. Diagnostic prompts and ordinary tool usage did execute, so this is MODEL_DID_NOT_CALL, not unavailable Skill proved from missing calls.

Recovered MEER batch2: all3 traces terminate with explicit host context-admission rejections around15.6–16.0k input +16,384 reserved output +1,024 safety. U-RE v02b similarly has4/4 admission rejections. Action-First ABBA has2 admission rejections, while raw Native still reports true for one of them: fallback evaluation and execution failure can coexist. These directly support auditing context accounting before adding reasoning mechanisms. They do not identify which semantic action would have succeeded with more context.

## What is not established
No aggregate percentage of localization/root-cause/revision failure is justified without blinded semantic coding of the remaining transcripts. Time between tool calls is not model thinking time. A file read is not correct localization; an edit is not repair; an all-green weak test is not success. Native raw failures can contain environment problems, so VERIFICATION_FAILURE tags are provisional observations, not automatically valid unsuccessful repairs. The Requests CPU02187setup errors +4network-confinement failures are environment failure, excluded from model performance.

## Immediate interpretation
H2 and H6 have concrete failure observations worth testing; H1's benefit remains untested because current Skill never ran. H3–H5 remain plausible but incompletely adjudicated. Instrumentation cannot establish the causal effect of EGRD on these runs.
