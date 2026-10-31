import hashlib,json,zipfile,stat,re,statistics
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(name,d):(OUT/name).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def md(name,text):(OUT/name).write_text(text.strip()+'\n',encoding='utf8')
compiler=json.loads((OUT/'CPU_COMPILER_RESULT.json').read_bytes());assert compiler['status']=='PASS'
r2=(OUT/'submission_r2_candidate.zip').read_bytes();baseline=(ROOT/'work/gemma-r12-01/candidates/BASELINE.zip').read_bytes()
assert sha(r2)=='af918c1a65aeb211298f13a69b5b789ae6b086974922c80469df87d902eb98d5'
with zipfile.ZipFile(OUT/'submission_r2_candidate.zip') as z,zipfile.ZipFile(ROOT/'work/gemma-r12-01/candidates/BASELINE.zip') as b:
 assert z.testzip() is None;assert set(z.namelist())==set(b.namelist())=={'agent.yaml','configs/sampling.yaml','eval_config.yaml','prompts/system.md'}
 difference=[n for n in z.namelist() if z.read(n)!=b.read(n)];assert difference==['prompts/system.md']
 files={}
 for i in z.infolist():
  path=PurePosixPath(i.filename);assert not path.is_absolute() and '..' not in path.parts and '\\' not in i.filename
  assert not stat.S_ISLNK(i.external_attr>>16)
  raw=z.read(i);text=raw.decode('utf8');dest=OUT/'submission_r2_candidate'/i.filename
  assert dest.read_bytes()==raw
  assert not re.search(r'(?:AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)',text)
  for inc in re.findall(r'!include\s+([^\s#]+)',text):
   target=(dest.parent/inc).resolve();assert target.is_relative_to((OUT/'submission_r2_candidate').resolve()) and target.is_file()
  files[i.filename]=dict(bytes=len(raw),sha256=sha(raw))
 prompt=z.read('prompts/system.md');assert sha(prompt)==compiler['instruction_sha256']
 assert prompt.startswith(b.read('prompts/system.md'))
 appended=prompt[len(b.read('prompts/system.md')):].decode().strip()
 assert appended==(ROOT/'work/gemma-r12-01/R2.md').read_text(encoding='utf8').strip()
scored=json.loads((ROOT/'work/kaggle-evidence/scored_baseline_03/record.json').read_bytes());assert scored['scored_download_sha256']==sha(baseline)
archive=ROOT/'work/gemma-r12-01/gpu-run02-output/gemma-r12-authorized-gpu-02.zip'
with zipfile.ZipFile(archive) as z:
 study=json.loads(z.read('execution/PAIR_RESULTS.json'));original_probe=z.read('execution/inputs/integration/frozen-checks/probe.py')
 assert b"classification='TARGET_BEHAVIOR_FAILURE' if control_pass and target_fail else 'CHECK_PASS_NON_DISCRIMINATING' if control_pass" in original_probe
 contrasts=[]
 for record in study['records'][:3]:
  ev=record['result']['evaluation'];target_rows=[c for c in ev['receipt']['checks'] if c['kind']=='target'];assert len(target_rows)==2
  contrasts.append(dict(index=record['index'],candidate=record['candidate'],base_source_identity=ev['base_source_identity'],tested_source_identity=ev['tested_source_identity'],classification=ev['receipt']['classification'],target_passed=ev['target_passed'],target_checks=target_rows,positive_controls_passed=ev['positive_controls_passed'],check_unchanged=ev['check_unchanged'],check_write_denied=ev['check_write_denied'],source_unchanged_by_checks=ev['source_unchanged_by_checks'],patch_sha256=ev.get('patch_sha256')))
 assert len({c['base_source_identity'] for c in contrasts})==1
 assert [c['target_passed'] for c in contrasts]==[False,True,True]
 assert all(c['positive_controls_passed'] and c['check_unchanged'] and c['check_write_denied'] and c['source_unchanged_by_checks'] for c in contrasts)
save('DJANGO_DISCRIMINATION_AUDIT.json',dict(evidence=['STATIC_ANALYSIS','REAL_GPU_OBSERVATION','CPU_VERIFIED'],generation_source='Retained execution/inputs/integration/frozen-checks/probe.py run(), classification expression near line 117',probe_sha256=sha(original_probe),meaning='When controls pass and no target fails, this shared probe emits the label regardless of whether a paired unpatched target failed. It is a misleading preflight-style label, not a statistical discrimination test.',contrasts=contrasts,base_sources_match=True,paired_targets_discriminate=True,expectations_changed=False))
before=json.loads((OUT/'IMMUTABLE_INPUTS.json').read_bytes());after={p:sha(Path(p).read_bytes()) for p in before};assert before==after
save('IMMUTABILITY_VERIFICATION.json',dict(status='PASS',files=len(before),whole_original_GPU_archive_unchanged=True,frozen_candidates_unchanged=True,original_S0_unchanged=True,checked_at_utc=datetime.now(timezone.utc).isoformat()))
budget=json.loads((OUT/'R2_BUDGET_ANALYSIS.json').read_bytes())
quality=[]
for p in sorted((OUT/'cpu-results').glob('*.json')):
 d=json.loads(p.read_bytes());quality.append(dict(task=d['task'],variant=d['variant'],passed=sum(c['status']=='PASS' for c in d['checks']),failures=[c['name'] for c in d['checks'] if c['status']!='PASS']))
assert all(not r['failures'] for r in quality if r['variant']=='r2')
native=json.loads((OUT/'NATIVE_CPU_RESULTS.json').read_bytes());assert next(r for r in native if r['name']=='pytest_native_collection' and r['variant']=='r2')['returncode']==0
unknown=['OFFICIAL_TASK_COUNT_UNKNOWN: approximate organizer description about 120 is not exact N','Private scorer global timer implementation, task order, overrides and model startup charging boundary','Official scorer runtime/caching equivalence to R12 custom sandbox and server','Local CPU SDK metadata dependency closure is incomplete for model-serving-only modules; see SDK_DEPENDENCY_CHECK.txt. Actual compiler/tool registration passed without stubs. Full host serving validation: NOT_RUN this audit.','Complete historical Django functional API on a compatible pre-3.11 Python runtime: NOT_RUN; both baseline and R2 error under current Python 3.12','Full framework regression suites: NOT_RUN','Official Native Resolved and canonical SWE-bench Resolved: UNKNOWN/not measured','Hidden-task repair probability and tail-cost distribution: UNKNOWN','A deployable organizer-supported global-budget callback: not verified']
manifest=dict(gate='R2_BLOCKED_BY_BUDGET',created_at_utc=datetime.now(timezone.utc).isoformat(),reference_commit='d6bd3eb291a650b1de218df1795b753562cfd94a',candidate='Exact frozen R2 archive copied without regeneration or configuration changes',zip_sha256=sha(r2),zip_bytes=len(r2),files=files,baseline_sha256=sha(baseline),scored_baseline_receipt=dict(submission_id=scored['submission_id'],score=scored['official_score'],sha256=scored['scored_download_sha256']),
 sole_package_strategy_difference=difference,official_compiler=compiler,archive_safety='PASS: root/include paths, UTF-8, no symlinks/traversal, four whitelist files, no task patches/tests/data/private-key patterns',
 secrets_scan_scope='Whole four-file archive inspected; static known secret patterns plus declarative-file manual review. No credentials added.',
 no_new_graph_tools=True,graph_tool_note='The frozen scored BASELINE already declares three graph tools, and its prompt tells the Agent not to use them. Exact R2 retains that same registry list. None added in this audit.',
 model='gemma-4-31b-it-qat-w4a16-ct',LoRA=False,prefix_cache=dict(R12=False,package_setting=None,official_scorer_equivalence='UNKNOWN; host controlled, not a ZIP field'),
 CPU_quality=quality,unknown=unknown,official_native_resolved=None,canonical_swebench_resolved=None,GPU_Notebooks_started=0,SaveKernel_calls=0,real_Gemma_requests=0,formal_submissions=0,R3_built=False)
manifest['local_sdk_dependency_check']=dict(status='INCOMPLETE_RUNTIME_METADATA_CLOSURE',raw_report='SDK_DEPENDENCY_CHECK.txt',finding=(OUT/'SDK_DEPENDENCY_CHECK.txt').read_text(),compiler_import_path_passed=True,whole_model_serving_validation='NOT_RUN; forbidden GPU/inference operations were not used')
save('R2_SUBMISSION_MANIFEST.json',manifest)
md('R2_SUBMISSION_PACKAGE_AUDIT.md',f'''# R2 submission package audit

CPU_VERIFIED: the real frozen official compiler accepted the exact candidate extracted from ZIP, including official tool registration and configuration parsing. SDKs: swegemma 0.2.11, adk-submission 0.2.13, adk-eval-core 0.1.0, google-adk 1.36.1, google-genai 2.11.0 and LiteLLM 1.82.4. Five newly downloaded organizer wheels match the frozen R12 wheel hashes. No stubs, monkeypatched tools, model load or inference were used. CPU_COMPILER_RESULT.json records the actual result, schemas/config and source hashes. Compiler acceptance is not a repair score or a whole-platform deployment test.

The local CPU environment does not have complete swegemma distribution metadata closure: pip check reports missing accelerate, safetensors, torchvision and transformers. The actual compiler and official tool registration import/run without these modules, but full model/serving runtime dependency acceptance is NOT_RUN here, not PASS. The previous R12 Linux serving run remains separate historical evidence. Raw dependency output and installed CPU package lists are retained; no GPU library installation or fake import stub was used to conceal this gap.

Candidate `submission_r2_candidate.zip`: {len(r2)} bytes; SHA256 `{sha(r2)}`. It is byte-identical to frozen R2, including eval_config; it was not regenerated or silently retuned. The independent unpacked directory contains exactly agent.yaml, eval_config.yaml, configs/sampling.yaml and prompts/system.md. Agent YAML is at root, every include resolves inside that root, no archive symlinks/traversal, unrelated tests, research patch, data, adapters or executable framework files are present. Static credential patterns and the four actual texts were inspected; no secrets added. Full member hashes are in R2_SUBMISSION_MANIFEST.json.

STATIC_ANALYSIS: exact ZIP comparison with the historical BASELINE changes only prompts/system.md. The prefix is exactly the Baseline prompt and the suffix exactly the frozen six-rule R2.md. Model, nine registered tools, schemas, sampling .2/.95, output 8192, thinking 4096/include_thoughts true, budgets 8min/28calls/80turns/240s, and absence of LoRA are unchanged. The downloaded historical 0.15 submission receipt (ID {scored['submission_id']}) identifies the same Baseline SHA256 `{sha(baseline)}`. This is stronger package identity evidence than copying the current Notebook's output; that later output had a different hash. R2 has no official score yet.

The graph tools already existed in the scored BASELINE registry; its own prompt forbids using them. They are retained without adding a mechanism. R12's host prefix-cache setting was false; server caching and scorer environment are outside these four ZIP files. Equality of package configs is verified, but equivalence of historical/private host serving is UNKNOWN.

The repository-at-R12 `submission/` is a separate older six-tool Agent with a different prompt, no explicit sampling include, 60min/100calls/300s local defaults and verification_timeout_seconds=300. It does not already contain R2. It is not overwritten. We do not merge R2 into that old configuration because doing so would lose the scored Baseline single-factor comparison. Instead the requested independent directory preserves the actual tested R2 exactly. No unverified field is added to make packaging appear complete.

## Official eval_config schema audit

OFFICIAL_RULE / STATIC_ANALYSIS: the freshly downloaded [organizer Starter](https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent) explicitly parses the four inference fields below. Current HARNESS_README section 7.1 maps them to Stage 1 `scripts/inference.py`; the frozen actual EvalConfig and real CPU parse agree. Official source identities are saved separately. The private inference controller's full source was not available; its runtime environment overrides are not assumed absent.

| Key | Actual meaning and support | R2 | Older submission |
|---|---|---:|---:|
| timeout_seconds | Per-command execution ceiling, not total task/session time; run_command clamps to local remaining time | 240 | 300 |
| max_time_minutes | Valid per-task Agent loop wall-clock budget; begins after sandbox setup | 8 | 60 |
| max_tool_calls | Valid charged-tool cap; get_status and submit_patch are uncharged | 28 | 100 |
| max_turns | Valid model turn limit; absent defaults are host controlled | 80 | absent |
| verification_timeout_seconds | Valid local EvalConfig/Starter Phase 2 field, but official scorer table fixes verification at 300s; not a supported Stage 1 submission override | absent | 300, local-only |

All four R2 keys have official support; no R2 UNVERIFIED_CONFIG_FIELD is retained. Older verification_timeout_seconds is classified LOCAL_ONLY_NOT_SCORER_OVERRIDE, not evidence of global runtime control. Verification is outside the stated 12-hour generation budget and cannot be added to it again. Agent time includes model waiting and tool runtime; command timeout is not additive; sandbox preparation is outside the local Agent timer but inside the all-task generation limit. Model server startup charging and exact private admission implementation remain UNKNOWN; budget scenarios include startup conservatively.

The real get_status schema exposes only current session time/calls/patch status. It provides no global remaining seconds or remaining-task count. The Starter's two published examples are not official task-count evidence. No arbitrary submission controller can be assumed callable by the Harness.

## Gate

Package/compiler gate PASS. Overall decision R2_BLOCKED_BY_BUDGET, because an unchanged eight-minute cap has no demonstrated safe full-workload coverage. The exact compiled ZIP is ready for inspection, not dispatched or formally submitted. See R2_FINAL_DECISION.md and the explicit unknown list in the manifest. GPU-specific serving libraries/runtime were not revalidated; compilation uses the genuine CPU import path with a non-listening localhost model endpoint and never invokes it.
''')
md('R2_QUALITY_AUDIT.md','''# R2 quality audit

REAL_GPU_OBSERVATION: original R2 target/control receipts and source identities were preserved, not regraded into official results. STATIC_ANALYSIS: all three diffs and relevant locked source were reviewed without reference solutions or hidden tests. CPU_VERIFIED: independent isolated base/R2 copies ran expanded owned tests; receipts include every assertion and failure. No original trusted expected outcome was modified.

## Django and the misleading label

The exact archived probe source `execution/inputs/integration/frozen-checks/probe.py`, run(), near line 117, emits CHECK_PASS_NON_DISCRIMINATING whenever controls pass and no target fails. The same helper was used to identify an unpatched reproduction during preflight, hence the unfortunate label. It does not calculate discrimination, compare candidates, or check source identity. The evaluator separately records target_passed, target_failed, patch identity and isolation.

The original Baseline Django receipt fails both fresh string targets while controls pass. R1 and R2 pass both with controls passing. All three have identical base_source_identity; tested_source_identity differs as their retained patches differ. All assert check_unchanged, check_write_denied and source_unchanged_by_checks. The captured exact probe code and comparison are hashed in DJANGO_DISCRIMINATION_AUDIT.json. Expanded CPU tests repeat the base-fail/patched-pass contrast. There is no evidence from this comparison of a nondiscriminating target, different base source, or mutated check. The label remains unchanged in historical evidence.

The helper would be unsafe as a generic no-target acceptance rule because all([]) is true, but both expected target rows are present in each of the three actual Django receipts; the empty-target edge case did not occur. The trusted frozen probe bytes also equal extension/r12_issue_checks.py. This audit does not silently repair its historical label or expected outcomes.

R2 expanded CPU checks: 13/13 pass, including fresh TextChoices/IntegerChoices representation, SQLite readback, choices/labels/values/names, enum inheritance, equality/hash/value lookup, JSON primitive serialization, auto values, custom date Choice values, repr/copy, formatting and integer arithmetic. Base fails the three representation targets and passes the controls. The fix changes generic Choices string conversion too, which is a wider inherited behavior; values, types and metaclass remain unchanged.

Original locked Django model_enums suite: 16 executed on base and R2, 14 pass and the same two functional-API tests error in both. Python 3.12 Enum passes `boundary` to the old ChoicesMeta.__new__, which does not accept it. This is a pre-existing runtime compatibility error, not an R2 regression or a suite pass. A compatible older-Python rerun is NOT_RUN. No production workaround or test weakening was applied. A guarantee across all historical Django usages is NOT_RUN.

## xarray

R2 expanded CPU checks: 10/10 pass, including the source-identity receipt, NumPy empty chunk metadata, real Dask chunks and multi-dimension aggregation, preservation of the inconsistent-chunk ValueError, actual Zarr chunks=None metadata without data reads, Zarr+Dask chunks, real value read counter, duck arrays with/without chunks and a LazilyIndexedArray backend with zero __getitem__ calls. Base fails the Zarr and explicit lazy-backend no-materialization targets. Existing required R12 controls already passed for all arms.

STATIC_ANALYSIS: _data is a private interface, but the locked Variable.chunks and chunksizes implementation already uses it to inspect the original storage. The change avoids calling Variable.data merely to ask if chunks exist; it leaves chunksizes iteration, metadata shapes and the inconsistency exception intact. For recognized duck/Dask arrays the data accessor retains their array identity. This supports the locked version, not a promise for future xarray versions or every third-party backend. Unrecognized objects forced through the private fastpath remain an unsupported-coverage risk; broad backend compatibility across versions is NOT_RUN. The Agent fix is not being distributed as an xarray library release.

The newly written expanded fixture initially used zero as a real Zarr value, which the default fill_value=0 decoder masks to NaN on both versions. Its first receipts are preserved. Positive fixture values resolve that audit-fixture defect without changing historical checks, expected behavior or production code; CPU_PROBE_FIXTURE_CORRECTION.json records it. Final Zarr controls still require real reads for values and zero reads for metadata.

## pytest

R2 expanded exact-function CPU checks: 10/10 pass including a source identity receipt. Array replacement, real DEFAULT, explicit Mock, attribute_name filtering, mixed counts, empty/no patchings, dual mock-module DEFAULT objects and a custom equality trap are covered. Base fails array/mixed/equality targets. Unit extraction executes the exact AST function, separately labeled from native framework collection.

The actual locked pytest 5.0.2.dev58 framework was also run against five owned collection tests: R2 passes 5/5, base raises the original ambiguous-array ValueError during collection. Tests cover array replacement, default mock injection, explicit Mock without injection, ordinary fixture argument preservation and a plain function. Raw commands and output are retained. The new fixture initially replaced os.getcwd globally, interfering with NumPy's lazy sysconfig import; it was moved to an owned Target attribute while preserving the original failing array comparison. Initial output is retained separately. No historical trusted check was changed.

STATIC_ANALYSIS: DEFAULT is a singleton identity contract; equality is inappropriate for arbitrary replacements that overload __eq__ and return an array. Identity matching still recognizes both installed mock-module DEFAULT objects and preserves the existing attribute_name exclusion. No legitimate injected argument should be counted by value equality with a non-DEFAULT replacement. Existing broader framework suites are NOT_RUN, not implied by these focused checks.

## Quality conclusion

No R2-attributable regression was observed in the expanded focused checks. The two Django compatibility errors are shared by the base, and compatible-runtime resolution remains unverified. The three R2 research patches retain their validated development status with these explicit limits. Official Native Resolved and canonical SWE-bench Resolved remain UNKNOWN; no claim of official 3/3 is made. These task-specific patches are not included in the submission candidate.
''')
md('R2_FINAL_DECISION.md',f'''# R2 final decision

**R2_BLOCKED_BY_BUDGET**

R2 is worth preserving as the next formal-candidate basis. It is not recommended for immediate unchanged full-workload submission. The exact frozen ZIP passes a new real CPU official Compiler run and remains byte-identical to the tested R2. Its only package difference from the historical 0.15 Baseline is the appended R2 system prompt. The old repository submission directory is not the scored Baseline and was not overwritten.

| Review gate | Result |
|---|---|
| R2 prompt/includes and root packaging | CPU_VERIFIED PASS |
| Baseline/S0/R1/R2/history preservation | Hash verification PASS |
| Single strategy difference vs scored Baseline | ZIP member comparison PASS |
| Actual frozen official Compiler | CPU_VERIFIED PASS |
| Three patch reviews | Completed; expanded checks pass, original Django suite has two shared Python compatibility errors |
| Django label explained | Exact generator and same-base contrast verified |
| Official 12-hour model and scenarios | Completed, but safe full workload coverage is not demonstrated |
| eval_config meaning/support | Four R2 keys verified; old verification override is local-only |
| Unknowns explicit | Listed below |
| Final ZIP SHA256 | `{sha(r2)}` |

R2's three development successes remain 3/3 in owned Issue-grounded evaluation, not official Native Resolved or canonical SWE-bench. The focused CPU audit supports patch semantics; it does not establish hidden-task success probability. get_status was called zero times by R2, and all three lack explicit git diff; full compliance with its six rules is not demonstrated. pytest's first production edit and total Agent time are worse than Baseline. Do not attribute the pilot difference causally to the Prompt.

The R12 R2 Agent mean is {budget['agent_summary']['mean']:.2f}s; measured setup/save-inclusive generation proxy is {budget['task_cost_proxy_summary']['mean']:.2f}s. With assumed N=120, setup/model allowance 1500s and 10% reserve, the safe task average is 311.5s. Conditional mean-profile capacity is 91 tasks; the corresponding mean cost reduction required is about 23.5%. Exact N remains OFFICIAL_TASK_COUNT_UNKNOWN; organizer materials describe approximately 120, not a guaranteed 60-task workload. The current eight-minute cap plus setup cannot guarantee all-task coverage. This budget block expresses insufficient safe-execution evidence, not a proven measured private-scorer timeout.

Next priorities toward 0.50: establish scorer timing/override boundaries and task-count assumptions; design a separate budget-only or explicitly prompt-consistent budget experiment; measure tail costs and early-stop behavior on a pre-frozen holdout with paired runs; count all failures and protect independent semantic/regression checks. Compare validated repairs per global generation second, not just per attempted task. Obtain official feedback only after a later explicit submission authorization. R3 is neither necessary for this audit nor created here.

Unknown / NOT_RUN items:
'''+ '\n'.join('- '+s for s in unknown)+'''

No GPU Notebook, SaveKernel, model inference, competition submission, model switch, selective R12 rerun or frozen-candidate mutation occurred in this audit. The required package is delivered for inspection only. This final gate does not authorize submission.
''')
print(json.dumps(dict(gate=manifest['gate'],zip_sha256=sha(r2),compiler=compiler['status'],quality=quality,protected_files=len(before))))
