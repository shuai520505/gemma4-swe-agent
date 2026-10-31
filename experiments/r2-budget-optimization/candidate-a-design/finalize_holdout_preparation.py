"""Freeze metadata-only selection rules and honest blocked session slots."""
import hashlib,json,random
from pathlib import Path

DESIGN=Path(__file__).resolve().parent
OUT=DESIGN/'holdout-preparation'
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
    registry=json.loads((OUT/'EXPOSURE_REGISTRY.json').read_bytes())
    refresh=json.loads((OUT/'OFFICIAL_POOL_REFRESH.json').read_bytes())
    native=json.loads((OUT/'NATIVE_CPU_CONTRACT_RESULT.json').read_bytes())
    policy=json.loads((DESIGN/'CANDIDATE_A_POLICY_SPEC.json').read_bytes())
    assert registry['remaining_count']==0 and registry['excluded_public_count']==129
    assert refresh['current_sha256']==registry['dataset_sha256'] and refresh['same_bytes_as_historical']
    assert all(c['passed'] for c in native['junit_cases'])
    seed=20261031
    pair_orders=['R2_A','R2_A','A_R2','A_R2']
    random.Random(seed).shuffle(pair_orders)
    selection={
        'status':'RULES_FROZEN_NO_ELIGIBLE_TASKS',
        'seed':seed,'seed_use':'Metadata task ranking and session order only; never model generation',
        'candidate_policy_spec_sha256':sha((DESIGN/'CANDIDATE_A_POLICY_SPEC.json').read_bytes()),
        'control_zip_sha256':policy['control_zip_sha256'],
        'input_pool_sha256':registry['dataset_sha256'],
        'required_tasks':4,'available_eligible_tasks':0,
        'selection_keys':['instance_id','repo','base_commit','issue_sha256'],
        'exposure_policy':'Exclude actual, screened, analyzed, historically reserved/planned or uncertain identities. Metadata-only pool registration is not itself exposure. Prior frozen exclusions are not silently relaxed.',
        'alias_policy':'Exclude same normalized repo+base_commit+issue_sha256 under any ID; add known equivalent Issue URLs if available. Nonidentical Issue paraphrase equivalence remains UNKNOWN; no guarantee of global absence of exposure.',
        'ranking':'SHA256(UTF8("R2A-v1|20261031|" + repo.lower() + "|" + instance_id + "|" + base_commit + "|" + issue_sha256)); ascending hex, instance_id tie-break',
        'repository_blocking':'Choose the minimum-ranked eligible task per repository, rank repository representatives by the same digest and take four. If fewer than four repository blocks exist, round-robin the remaining within-repository ranks to maximize available diversity; disclose reduced scope before execution.',
        'issue_type_stratification':'UNKNOWN_NOT_USED; no task-content/ease/outcome ranking',
        'selection_execution':'NOT_RUN_ZERO_ELIGIBLE',
        'selected_task_ids':[],
        'new_sources':'Any additional cohort/source requires a versioned amendment, metadata exposure audit and official-native compatibility evidence before selection; never swap after outcomes.',
        'primary_endpoint':'Actual official native result plus separate effective-production/semantic validation; generated XML contract fixtures are not repairs.'
    }
    (OUT/'HOLDOUT_SELECTION_RULES.json').write_text(json.dumps(selection,indent=2)+'\n',encoding='utf8')
    sessions=[]
    for pair,order in enumerate(pair_orders,1):
        for arm in order.split('_'):
            sessions.append({'index':len(sessions)+1,'pair':pair,'arm':'R2' if arm=='R2' else 'Candidate_A',
                'instance_id':None,'repo':None,'base_commit':None,'issue_sha256':None,
                'status':'NOT_RUN','reason':'HOLDOUT_POOL_BLOCKED_TASK_IDENTITY_NOT_FROZEN',
                'agent_seconds':480,'charged_tools':28,'max_turns':80,'command_timeout_seconds':240})
    assert len(sessions)==8 and pair_orders.count('R2_A')==pair_orders.count('A_R2')==2
    order={'status':'ARM_TEMPLATE_ONLY_TASK_ORDER_NOT_FROZEN','seed':seed,'paired_orders':pair_orders,'sessions':sessions,'model_requests':0,'GPU_allocations':0}
    (OUT/'SESSION_ORDER_TEMPLATE.json').write_text(json.dumps(order,indent=2)+'\n',encoding='utf8')
    verification={
        'status':'PREPARATION_BLOCKED_HOLDOUT_AND_NATIVE_RUNTIME',
        'budget_audit_gate_unchanged':'R2_BUDGET_AUDIT_COMPLETE',
        'candidate_policy':'DESIGN_FROZEN_NOT_DISPATCH_READY',
        'historical_registry_files_hashed':registry['inventory_records'],
        'historical_registry_read_errors':registry['read_errors'],
        'excluded_public_tasks':129,'eligible_public_tasks':0,
        'official_pool_refresh':'IDENTICAL_CURRENT_129_ROWS',
        'native_CPU_contract_cases':8,'native_missing_spec_guard':'PASS',
        'native_full_lifecycle':'NOT_RUN','native_bug_and_positive_controls':'NOT_RUN',
        'Linux_sandbox_available':native['linux_sandbox_available'],
        'selected_task_ids':[],'frozen_full_task_session_order':False,
        'originals_mutated':False,'candidate_packages_created':0,
        'R3_created':False,'GPU_calls':0,'SaveKernel_calls':0,'model_requests':0,'competition_submissions':0,
        'input_hashes':{str(p.relative_to(DESIGN)):sha(p.read_bytes()) for p in [DESIGN/'CANDIDATE_A_POLICY_SPEC.json',OUT/'EXPOSURE_REGISTRY.json',OUT/'PUBLIC_POOL_IDENTITIES.json',OUT/'OFFICIAL_POOL_REFRESH.json',OUT/'NATIVE_CPU_CONTRACT_RESULT.json',OUT/'HOLDOUT_SELECTION_RULES.json',OUT/'SESSION_ORDER_TEMPLATE.json']},
        'limitations':['Local available corpus is not proof of no deleted/remote exposure.','Conservative exclusion does not mean every task was run.','CPU XML/guard checks do not establish official Native correctness or trustworthy sandbox execution.']
    }
    (OUT/'PREPARATION_GATE.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:verification[k] for k in ('status','historical_registry_files_hashed','eligible_public_tasks','native_full_lifecycle','GPU_calls')}))

if __name__=='__main__':main()
