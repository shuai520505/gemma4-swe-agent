"""Derive research reports from raw audit records; never modify historical inputs."""
import collections,datetime,hashlib,json,re,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from audit_history import OUT,ROOT,OLD,sha,dump,loc,is_prod

def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(n,t):(OUT/n).write_text(t.strip()+'\n',encoding='utf-8')
data=load(OUT/'HISTORICAL_EXPERIMENT_DATASET.json');ss=data['sessions']
registry={}
paths={'S0':ROOT/'outputs/verified_candidates/S0.zip','SCORED_BASELINE_015':ROOT/'outputs/verified_candidates/SUPERAGENT_SCORED_015.zip',**{k:ROOT/f'outputs/r12_candidates/{k}.zip' for k in ['R1','R2']},'Full_V01':ROOT/'outputs/r12_redispatch/mount-mirror/source/u_re/v01/submission_noegv.zip','EGR_V04':ROOT/'outputs/r12_redispatch/mount-mirror/source/u_re/v04/experiments/evidence_guided_repair_01/submission_egr_v04.zip'}
for a in 'ABCD':paths['EGRD_V01_FROZEN_'+a]=ROOT/f'experiments/egrd-v01-12b/pilot-frozen/packages/{a}.zip'
for a in 'BD':paths['EGRD_V02_'+a]=ROOT/f'experiments/egrd-v02-entrypoint-hardening/packages/{a}.zip'
for label,p in paths.items():
    if not p.exists():registry[label]={'path':loc(p),'status':'NOT_AVAILABLE'};continue
    with zipfile.ZipFile(p) as z:
        members={n:sha(z.read(n)) for n in z.namelist() if not n.endswith('/')}
        registry[label]={'path':loc(p),'sha256':sha(p.read_bytes()),'members':members,'prompt_sha256':members.get('prompts/system.md'),'skill_members':{k:v for k,v in members.items() if '/skills/' in '/'+k}}
dump('CANDIDATE_IDENTITIES.json',registry)
v01=load(ROOT/'experiments/egrd-v01-12b/pilot-frozen/PACKAGE_MANIFEST.json')
for s in ss:
    fam=s['family'];cand=s['candidate'];p=Path(s['evidence']['archive'])
    if not p.is_absolute():p=ROOT/p
    with zipfile.ZipFile(p) as z:
        ns=z.namelist();prefix=s['evidence']['result_member'].rsplit('/',1)[0]+'/'
        # JUnit inventory re-audits raw Native tests without changing their verdict.
        junit=[]
        for n in ns:
            if n.startswith(prefix) and n.endswith('.xml') and ('junit' in n.lower()):
                try:
                    t=ET.fromstring(z.read(n));cases=list(t.iter('testcase'))
                    junit.append({'member':n,'sha256':sha(z.read(n)),'testcases':len(cases),'errors':len(list(t.iter('error'))),'failures':len(list(t.iter('failure'))),'skips':len(list(t.iter('skipped')))})
                except ET.ParseError:junit.append({'member':n,'parse_error':True})
        s['native_junit_inventory']=junit
        if fam=='EGRD_SKILL_V01':
            s['package_sha256']=v01['arms'][cand]['sha256'];s['packaged_prompt_sha256']=v01['arms'][cand]['members']['prompts/system.md']
            s['skill']['identity']=v01['arms'][cand]['members']['skills/egrd-repair/scripts/egrd.py']
            s['commit']=None # Dispatch BUILD hashes, not today's source commit, identify runtime.
            s['native_trust']='RAW_JUNIT_INSPECTED_ZERO_SETUP_ERRORS' if junit and all(r.get('errors')==0 and r.get('testcases',0)>0 for r in junit) else 'UNKNOWN'
            s['identity_evidence'].append({'local_path':'experiments/egrd-v01-12b/gpu-notebook/BUILD.json','sha256':sha((ROOT/'experiments/egrd-v01-12b/gpu-notebook/BUILD.json').read_bytes())})
        if fam=='R12' and cand in ['BASELINE','R1','R2']:
            key='SCORED_BASELINE_015' if cand=='BASELINE' else cand
            s['package_sha256']=registry[key]['sha256'];s['packaged_prompt_sha256']=registry[key]['prompt_sha256']
        if fam=='S0_SUPERAGENT_PAIR':
            key='S0' if cand=='S0' else 'SCORED_BASELINE_015'
            s['package_sha256']=registry[key]['sha256'];s['packaged_prompt_sha256']=registry[key]['prompt_sha256']
        if fam=='RECOVERED_egrd-v032-real-gemma-evidence-ab':
            s['candidate']='S0' if cand=='A' else 'EGRD_LEGACY_V032_PROMPT'
            if cand=='A':s['package_sha256']=registry['S0']['sha256']
            s['skill']['activation_confirmed']=None;s['skill']['activation_applicable']=False
        if fam=='LEGACY_cure-gpu-mechanism-01' and 'cure_v01' in cand:
            s['evidence_kind']='ENTRYPOINT_FAILED_BEFORE_MODEL_REQUEST'
        if '/gpu_host_environment/' in s['evidence']['result_member']:s['evidence_kind']='CPU_ENVIRONMENT_BASELINE'
        # Agent step trace gives effective instruction identity when direct record absent.
        if not s['prompt_sha256']:
            names=[n for n in ns if n.startswith(prefix) and n.endswith(('native_trace.json','agent_boundary_trace.json'))]
            for n in names:
                try:
                    trace=json.loads(z.read(n));first=next((x for x in trace.get('steps',[]) if x.get('source')=='system'),None)
                    if first and isinstance(first.get('message'),str):s['prompt_sha256']=sha(first['message'].encode());break
                except (ValueError,KeyError):pass
        # Source-code archive identity is a composite, distinct from evaluator file identity.
        evals=[x for x in s['runtime_members'] if 'evaluat' in Path(x['member']).name]
        s['evaluator_sha256']=sha(json.dumps(evals,sort_keys=True).encode()) if evals else None
        s['evaluator_identity_scope']='composite archived evaluator-code SHA; null when unavailable; not assumed identical to installed SDK'
data['non_session_records'][0]['source']='experiments/egrd-v02-entrypoint-hardening/NATIVE_TRUST_AUDIT.json'
data['non_session_records'] += [
 {'family':'EGRD_SKILL_V01','evidence_kind':'NOT_RUN','planned_not_executed_sessions':9,'source':'experiments/egrd-v01-12b/gpu-output/egrd-v01-12b-pilot01.zip#execution/PAIR_RESULTS.json'},
 {'family':'MEER_MATCHED_BATCH01','evidence_kind':'UNAVAILABLE','source':'Kaggle kernels_list_files wudangdexiaodoashi/meer-v01-authorized-matched-batch-01','files_returned':0,'scope':'No output currently returned by read-only API; not evidence that model never ran'},
 {'family':'Full_V01_AND_EGR_V04','evidence_kind':'OFFICIAL_AGGREGATE_SCORE','source':'OFFICIAL_SUBMISSION_OBSERVATIONS.json','per_hidden_task_traces':'UNAVAILABLE'}]
dump('HISTORICAL_EXPERIMENT_DATASET.json',data)

# Every record has eleven explicit questions; semantics remain unknown unless reviewed.
fail=[]
for s in ss:
    tags=[];obs=[];err=str(s.get('agent_error') or s.get('native_error_raw') or '')
    if 'ContextWindow' in err or '"decision": "reject"' in err:tags.append('CONTEXT_EXHAUSTION');obs.append('Backend context error or host admission rejection in raw agent result; allocation versus semantic failure is not inferred.')
    if 'timeout' in err.lower() or 'exceeded session' in err.lower():tags.append('BUDGET_FAILURE')
    if s['evidence_kind']=='ENTRYPOINT_FAILED_BEFORE_MODEL_REQUEST':tags.append('ENTRYPOINT_FAILURE');obs.append('CURE instruction preprocessing could not resolve context variable JSON before first model request.')
    if s['patch_submitted'] is False:tags.append('SUBMISSION_FAILURE')
    if s['native_resolved_raw'] is False:tags.append('VERIFICATION_FAILURE');obs.append('Raw SDK resolved=false; Native trust must be considered independently.')
    if s['native_resolved_raw'] is True:obs.append('Raw SDK resolved=true; not promoted to independently trusted repair or hidden-task success.')
    q={
      'inspected_relevant_production_code':{'value':None,'status':'UNKNOWN','evidence':s['production_code_inspected_paths'],'note':'Observed file reads alone do not establish causal relevance.'},
      'identified_correct_behavioral_contract':{'value':None,'status':'UNKNOWN'},
      'plausible_causal_explanation':{'value':None,'status':'UNKNOWN'},
      'production_code_edit':{'value':None,'status':'UNKNOWN','observed_final_production_paths_heuristic':sorted(set(f for p in s['patches'] for f in p['production_paths_heuristic']))},
      'first_meaningful_edit_seconds':{'value':None,'status':'UNKNOWN','source_observation':s['source_edit_observation'],'reported_metrics':s['first_production_edit_record']},
      'first_patch_behaviorally_relevant':{'value':None,'status':'UNKNOWN'},
      'meaningful_tests':{'value':None,'status':'UNKNOWN','test_command_attempts':s['test_command_attempts']},
      'feedback_influenced_revision':{'value':None,'status':'UNKNOWN'},
      'earlier_patch_improved_or_destroyed':{'value':None,'status':'UNKNOWN'},
      'submitted':{'value':s['patch_submitted'],'status':'OBSERVED' if s['patch_submitted'] is not None else 'UNKNOWN'},
      'native_result':{'value':s['native_resolved_raw'],'status':s['native_trust'],'scope':'Original SDK result, distinct from independent semantic correctness and formal Public Score'} }
    if s['family']=='EGRD_SKILL_V01':
        q['inspected_relevant_production_code'].update(value=True,status='OBSERVED',note='Manual raw-trace review: Pylint argument regexp transformer/utilities, Sphinx prepend_prolog implementation. Relevant location is not a correct root-cause proof.')
        q['identified_correct_behavioral_contract'].update(value=True,status='INFERRED',note='Initial reasoning describes comma-bearing regex or rst_prolog heading failure. Completeness unproved.')
        if s['candidate']=='B':tags.append('SKILL_ACTIVATION_FAILURE');obs.append('Complete observed ADK tool list contains zero load_skill/run_skill_script calls. MODEL_DID_NOT_CALL, not TOOL_CALL_FAILED.')
        if 'sphinx' in s['task_id']:
            q['production_code_edit'].update(value=True,status='OBSERVED',note='Transient edit to sphinx/util/rst.py; source observer later returns to baseline. No final production repair.')
            q['first_patch_behaviorally_relevant'].update(value=True,status='INFERRED',note='prepend_prolog is issue-relevant; use of SECTIONING_CHARS was not validated. Relevance is not correctness.')
            q['earlier_patch_improved_or_destroyed'].update(value='REVERTED_UNVALIDATED_PATCH',status='OBSERVED',note='Reversal is not proof a working repair was destroyed.')
            tags.extend(['PATCH_GENERATION_FAILURE','ENVIRONMENT_FAILURE'])
            obs.append('Initial wrong working-directory build; later sphinx-build launcher unavailable in Agent. SDK and late Worker clocks disagree. These confound causal interpretation of timeout.')
        else:
            q['production_code_edit'].update(value=False,status='OBSERVED',note='Tracked production source stayed at baseline; final changes are reproduction/configuration only.')
            q['first_patch_behaviorally_relevant'].update(value=False,status='OBSERVED',note='No production patch observed.')
            tags.append('PATCH_GENERATION_FAILURE')
        q['plausible_causal_explanation']['note']='Semantic root-cause correctness UNKNOWN; relevant code reads and reasoning do not certify it.'
    if s['family']=='RECOVERED_egrd-v032-real-gemma-evidence-ab':
        q['inspected_relevant_production_code'].update(value=True,status='OBSERVED',note='Reads UserCreationForm.save and, in B, ModelForm save implementation.')
        q['identified_correct_behavioral_contract'].update(value=True,status='INFERRED',note='Transcript discusses saving custom-user many-to-many selections.')
        if s['candidate']=='S0':
            q['production_code_edit'].update(value=True,status='OBSERVED',note='Very late UserCreationForm.save edit; collected fallback patch is not evidence of successful application/validation.')
        else:
            q['production_code_edit'].update(value=False,status='OBSERVED',note='Writes and edit attempts target tests/reproduction. No surviving production edit.')
            tags.append('PATCH_GENERATION_FAILURE')
    if not tags:tags=['INDETERMINATE']
    fail.append({'session_id':s['session_id'],'execution_kind':s['evidence_kind'],'classification':sorted(set(tags)),'classification_scope':'Multi-factor observed/provisional failure signals, not an adjudicated cause of repair failure','questions':q,'observations':obs,'causal_attribution':'UNKNOWN unless explicitly INFERRED in question record','source':s['evidence']})
dump('FAILURE_DATASET.json',{'schema':'RESET_V1_FAILURE_1','records':fail,'semantic_review_limit':'Five EGRD-lineage/control trajectories manually reviewed. Other historical sessions have mechanical action/Native audit; unreviewed semantic questions are UNKNOWN, never automatically inferred from filenames or raw resolved.'})

# Prospective selection reads only allowed task metadata, never patch/hints/evaluator answers.
pool=Path('D:/kaggle/Gemma 4 Developer Agent Competition/official-inputs/tasks.jsonl')
tasks=[]
for line in pool.read_text(encoding='utf-8').splitlines():
    t=json.loads(line);tasks.append({k:t.get(k) for k in ['instance_id','repo','base_commit','problem_statement']})
exposed={s['task_id'] for s in ss if s['task_id']}
# Also exclude published planned tasks and historical run filenames, including failed/not-run.
for a in load(OUT/'ARCHIVE_PROVENANCE.json')['archives']:
    p=Path(a['path']);p=p if p.is_absolute() else ROOT/p
    with zipfile.ZipFile(p) as z:
        for n in z.namelist():
            exposed.update(re.findall(r'(?:fastapi|requests|httpx|rich)_\d+',n))
for name in ['experiments/egrd-v01-12b/TASK_IDENTITY_MANIFEST.json','experiments/egrd-v02-entrypoint-hardening/TASK_IDENTITY_MANIFEST.json','experiments/r2-early-decision-01/TASK_IDENTITY_LOCK.json']:
    p=ROOT/name
    if p.exists():exposed.update(re.findall(r'(?:fastapi|requests|httpx|rich)_\d+',p.read_text()))
seed='GEMMA-RESET-V1-2026-11-03-LOCK-01'
repos=sorted(set(t['repo'] for t in tasks));pilot=[];confirm=[];availability={}
for i,repo in enumerate(repos):
    eligible=[t for t in tasks if t['repo']==repo and t['instance_id'] not in exposed]
    eligible.sort(key=lambda t:sha((seed+'|'+t['instance_id']).encode()))
    availability[repo]=len(eligible)
    if len(eligible)<6:continue
    n=2;confirmation_n=4 if repo=='psf/requests' else 6
    assert len(eligible)>=n+confirmation_n
    for cohort,selected in [('diagnostic',eligible[:n]),('confirmation',eligible[n:n+confirmation_n])]:
        for t in selected:
            target=pilot if cohort=='diagnostic' else confirm
            target.append({'instance_id':t['instance_id'],'repo':repo,'base_commit':t['base_commit'],'issue_sha256':sha(t['problem_statement'].encode()),'snapshot_sha256':None,'snapshot_status':'NOT_MATERIALIZED','order_key':sha((seed+'|order|'+t['instance_id']).encode())})
for cohort in [pilot,confirm]:
    cohort.sort(key=lambda t:t['order_key'])
    # Block-balanced AB/BA; full assigned schedule frozen before outcomes.
    for i,t in enumerate(cohort):t['pair_sequence']=i+1;t['arm_order']=['S0','EGRD_V02_D'] if i%2==0 else ['EGRD_V02_D','S0']
lock={'status':'TASK_AND_ISSUE_IDENTITIES_LOCKED_SNAPSHOTS_PENDING','seed':seed,'selection':'Deterministic SHA256 ranking within eligible public repositories, excluding audited exposed run/planned IDs;2 diagnostic per eligible repo, confirmation6FastAPI/6Rich/4Requests. Public pool has only one HTTPX task, already exposed, so no independent HTTPX holdout exists. No outcome-based selection. Prior unaudited exposure UNKNOWN. NOT competition hidden task count.','eligible_by_repo':availability,'task_pool_sha256':sha(pool.read_bytes()),'task_pool_size':len(tasks),'fields_read':['instance_id','repo','base_commit','problem_statement'],'gold_patch_or_hints_used':False,'excluded_exposed_task_ids':sorted(exposed),'diagnostic_pilot':pilot,'confirmation':confirm,'dispatch_allowed':False,'execution_blockers':['Linux Native trust gate','materialize all exact snapshot hashes','freeze final runtime/evaluator/model-file identities and full common configuration receipt','authorization and live resource check']}
dump('TASK_COHORT_LOCK.json',lock)

real=[s for s in ss if s['evidence_kind']=='REAL_GEMMA_OBSERVATION']
counts=collections.Counter(s['family'] for s in real)
lines=['| Family | Confirmed Gemma sessions | Interpretation |','|---|---:|---|']
for f,n in counts.items():lines.append(f'| {f} | {n} | Raw execution; endpoint trust kept separate |')
table='\n'.join(lines)
dump('AUDIT_SUMMARY.json',{'records':len(ss),'confirmed_real_gemma_sessions':len(real),'by_family':dict(counts),'current_EGRD_V01_treatment_sessions':2,'current_EGRD_V01_control_sessions':1,'current_EGRD_V01_skill_activations':0,'legacy_prompt_EGRD_treatment_sessions':1,'EGRD_V02_real_sessions':0,'trusted_exact_S0_vs_V02_pairs':0,'new_GPU_calls':0,'new_SaveKernel_calls':0,'Native_efficacy':'UNKNOWN','research_status':'INVENTORY_COMPLETE_SEMANTIC_AUDIT_PARTIAL','experiment_readiness':'BLOCKED_NATIVE_TRUST_AND_SNAPSHOT_LOCK'})

write('HISTORICAL_EXPERIMENT_AUDIT.md',f'''# Historical evidence audit
Research branch research-reset-v1; parent ff111c21f8926367fe440e254070db38c2ca3f4a, the reviewed PR46 successor to the directive's stale9ef032a. Created {datetime.datetime.now(datetime.timezone.utc).isoformat()}.

## What can be counted
{len(real)} records have actual model/ADK execution evidence, out of {len(ss)} retained execution/evaluator records. Copies are deduplicated by exact raw result plus trace hashes, not candidate/task names; repeated real runs retain separate IDs. CPU replay found inside the R2-A GPU archive is explicitly excluded. A CPU host-environment baseline, pre-first-request CURE failure, and incomplete legacy traces are not counted as confirmed Gemma sessions. See [dataset](HISTORICAL_EXPERIMENT_DATASET.json) and [archive inventory](ARCHIVE_PROVENANCE.json).

{table}

## Candidate identities must not be collapsed
- Exact S0 ZIP {registry['S0'].get('sha256')} has six official tools, no Skill, and no explicit generation block. Its historical official submission57261002 now reports0.13.
- Later nine-tool Baseline/SUPERAGENT ZIP {registry['SCORED_BASELINE_015'].get('sha256')} reports0.15 in submission57666970. It is not S0.
- R2 ZIP {registry['R2'].get('sha256')} reports0.15 in submission57843305, COMPLETE. It did not exceed that Baseline's public score. R12's3/3 is a scoped development result, not Native3/3.
- EGR V0.4 formal submission57566588 reports0.10. Full's historical0.12 is consistent with submission57505115; the current API description is empty, so that candidate-to-submission mapping remains historical attribution, not a newly proven ZIP binding.
- Current executable-Skill EGRD V0.1 used frozen A/B packages, not today's edited source tree. A is a matched-interface, S0-derived control with shared prompt/generation; it is not exact S0. Two B sessions actually ran. Nine planned sessions did not run.
- Older EGRD V0.3.2 A/B is a different Prompt lineage. Its B is not the current executable Skill system. Two31B sessions do not provide a current Skill activation denominator.
- EGRD V0.2 has CPU scripted sessions only, zero real Gemma sessions. Native trust remains BLOCKED_INFRASTRUCTURE.

Current score observations are read-only Kaggle API observations in [OFFICIAL_SUBMISSION_OBSERVATIONS.json](OFFICIAL_SUBMISSION_OBSERVATIONS.json). Exact immutable candidate/member hashes are in [CANDIDATE_IDENTITIES.json](CANDIDATE_IDENTITIES.json). Prompt file hash and compiled instruction hash are separate: compiler expansion changes the effective instruction bytes.

## Endpoint audit
R12 and the S0/SUPERAGENT development pair have official_native_resolved=null. CHECK_PASS_NON_DISCRIMINATING must not be promoted to Native success. R2-A preserves raw SDK booleans separately from the previously authorized exact-case/semantic evaluation amendment; weak matcher successes are not trusted automatically. CURE C1 and Checklist successes are on lumen_interface_01 synthetic tasks, not hidden public-code repair evidence. Context-guard batches contain both admission rejections and raw verification failures; do not equate them.

For current Skill Pilot Native XML, A Pylint and B Pylint each execute20 cases with2 failures,0 setup errors; B Sphinx executes10 cases with2 failures,0 setup errors. These are real negative results. A separate Sphinx Agent dependency/clock confound remains. These XML observations do not repair the newer Requests CPU02 trust failure.

## Completeness and uncertainty
Dataset fields include exact raw result/trace hashes and member references for each row. Missing commit, exact start/end, hardware allocation, evaluator binary identity or token usage remains null. Earliest/latest model-event timestamps are NOT relabeled as session boundaries. Runtime composite hashes are explicitly identified as composites. Source path classification is a heuristic, not semantic repair adjudication. Model usage from received responses is not total billed usage when cancelled responses are unknown.

MEER matched batch01 currently returns zero output files by API: execution remains UNKNOWN. Full/EGR formal hidden-task trajectories are inaccessible. Three older legacy result wrappers lack sufficient available model trace identity. This is a complete inventory of the inspected sources, not a claim that every historical session ever executed has been recovered or semantically reviewed. Newly recovered raw ZIPs remain locally preserved under raw_recovered/; publication includes hashes/indexes and sanitized derived records rather than duplicating large archives.
''')

write('FAILURE_ANALYSIS.md','''# Failure analysis
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
''')

print('derived records',len(ss),'confirmed real',len(real),'cohort',len(pilot),len(confirm))
