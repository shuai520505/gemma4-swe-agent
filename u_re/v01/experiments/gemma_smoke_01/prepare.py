"""Offline manifest/Notebook preparation; only reads pinned Git blobs and local files."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
S2='9aed40fa0fff10aff242fe30798d9c8c808b00c4'
BASE='cc9c18ee4eb8c1dcb767ab427064e4f07af618d4'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(name):return subprocess.check_output(['git','show',S2+':'+name],cwd=ROOT)
def write(name,data):
    (HERE/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def main():
    from u_re.v01.experiments.gemma_smoke_01.inputs import candidate,ZIPS
    protocol=json.loads(read('s2/experiments/earlyegv_mechanism_01/AUTHORIZED_PROTOCOL.json'))
    origin='s2/experiments/earlyegv_mechanism_01/results/gpu01/'
    admission_path=origin+'gpu_host_environment/fastapi_14492/environment_admission.json'
    baseline=json.loads(read(admission_path))
    versions=json.loads(read(origin+'gpu_runtime_admission.json'))
    task=protocol['task_inputs']['fastapi_14492']
    assert baseline['eligible'] and baseline['cleanup_complete'] and not baseline['reference_patch_used']
    assert task['base_commit']==baseline['base_commit'] and task['issue_sha256']==baseline['issue_sha256']
    # Source bytes already executed in S2, available unchanged on the U-RE branch.
    shared={n:h for n,h in protocol['source_hashes'].items()
            if n.startswith(('harness_v2/','s1/')) and (ROOT/n).is_file()}
    assert all(sha((ROOT/n).read_bytes())==h for n,h in shared.items())
    write('S2_REUSE_BINDINGS.json',dict(source_commit=S2,source_protocol_sha256=sha(read('s2/experiments/earlyegv_mechanism_01/AUTHORIZED_PROTOCOL.json')),
        unchanged_shared_files=len(shared),execution_sources=shared,
        excluded='S2 workers, nested AgentTool observer, prompts/candidates, results, task answers, original authorization, dispatch claims and four-run coordinator'))
    write('TASK_IDENTITY.json',dict(**task,scope='ENGINEERING_SMOKE_ONLY',
        historical_baseline=dict(eligible=True,counts=baseline['counts'],category=baseline['category'],cleanup_complete=True,
            source_commit=S2,source_path=admission_path,source_sha256=sha(read(admission_path))),
        runtime_recheck='Required on the exact mounted snapshot/dependencies; no task substitution'))
    write('MODEL_RUNTIME_CONFIG.json',dict(model_alias='gemma-4-31b-it-qat-w4a16-ct',
        model_source='google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2',
        model_files=protocol['model_files'],historical_versions=versions['versions'],historical_CUDA=versions['torch_cuda'],
        tensor_parallel_size=4,devices='4xNVIDIA L4',max_model_len=32768,context_safety=1024,
        gpu_memory_utilization=.90,tool_call_parser='gemma4',reasoning_parser='gemma4',
        dtype='bfloat16',enable_auto_tool_choice=True,enable_lora=False,scheduler_reserve_full_isl=False,
        generation_source='Frozen candidate agent.yaml, unchanged',runtime_status='RUNTIME_RECHECK_REQUIRED'))
    write('SMOKE_PLAN.json',dict(experiment_id='U-RE-V01-GEMMA-SMOKE-01',execute=False,gpu_authorized=False,
        formal_submission=False,task=task,candidate='noegv',candidate_zip_sha256=ZIPS['noegv'],
        candidates={a:candidate(ROOT/f'u_re/v01/submission_{a}.zip',h) for a,h in ZIPS.items()},
        model_files=protocol['model_files'],official_wheels=protocol['wheel_hashes'],task_wheels=protocol['task_wheel_hashes'],
        official_versions=versions['versions'],execution_sources=shared,admission_sha256=sha(read(admission_path)),
        historical_admission_source=S2+':'+admission_path,
        stages='PREFLIGHT LOAD_MODEL READY_CHECK INIT_AGENT LOAD_TASK RUN_AGENT COLLECT_PATCH NATIVE_VERIFY EXPORT CLEANUP'.split(),
        agent_runs=1,agent_seconds=300,tool_budget=60,command_seconds=120,
        conservative_seconds=4230,finalization_seconds=600,target_notebook_seconds=5400,
        minimum_reported_quota_seconds=10800,quota_basis='Planning factor2 only; real API units and account allocation must be revalidated',
        task_replacement_allowed=False,extra_READY_generation=False))
    installed={m:bool(importlib.util.find_spec(m)) for m in ('google.adk','adk_submission','swegemma')}
    write('LOCAL_RUNTIME_AVAILABILITY.json',dict(python=platform.python_version(),platform=platform.system(),modules=installed,
        real_official_interface_tests='BLOCKED_MISSING_LOCAL_PACKAGES' if not all(installed.values()) else 'AVAILABLE',
        new_dependency_installation=False,official_historical_CPU_acceptance='u_re/v01/CPU_VALIDATION.md (110/110); not a new test'))
    write('GPU_PREFLIGHT.json',dict(experiment_id='U-RE-V01-GEMMA-SMOKE-01',execute=False,gpu_authorized=False,
        formal_submission=False,model_weights='RUNTIME_RECHECK_REQUIRED',GPU_quota='RUNTIME_RECHECK_REQUIRED',
        devices='RUNTIME_RECHECK_REQUIRED',window='RUNTIME_RECHECK_REQUIRED',installed_runtime='RUNTIME_RECHECK_REQUIRED',
        task_identity='HISTORICAL_PINS_BOUND',candidate_integrity='PASS',
        input_projection='STATIC_PASS',filesystem_isolation='UNVERIFIED_SUBPROCESS_IS_NOT_A_SECURITY_BOUNDARY',
        local_official_interface_tests='BLOCKED_MISSING_LOCAL_PACKAGES',human_authorization='NOT_GRANTED'))
    # Safe draft: saving these metadata could not request GPU; first cell stops before any setup/import.
    notebook=dict(nbformat=4,nbformat_minor=5,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},cells=[
        dict(cell_type='code',id='authorization-lock',metadata={},execution_count=None,outputs=[],
             source="raise RuntimeError('NOT_AUTHORIZED: offline Smoke draft; a separate reviewed build and explicit GPU authorization are required')\n"),
        dict(cell_type='code',id='future-entry',metadata={},execution_count=None,outputs=[],source=
            "# Future authorized build only; no payload, weights, credentials or evaluator data embedded.\n"
            "# Stage approved wheels/runtime sources outside Agent access, then import the existing worker adapter.\n"
            "from u_re.v01.experiments.gemma_smoke_01.SMOKE_RUNNER import run_authorized\n"
            "# await run_authorized(reviewed_grant, runtime_identity, private_output)\n")])
    for c in notebook['cells']:compile(c['source'],'<offline-draft>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    write('GPU_NOTEBOOK.ipynb',notebook)
    write('kernel-metadata.json',dict(id='wudangdexiaodoashi/gemma4-u-re-gemma-smoke01',
        title='gemma4-u-re-gemma-smoke01',code_file='GPU_NOTEBOOK.ipynb',language='python',kernel_type='notebook',
        is_private=True,enable_gpu=False,enable_tpu=False,enable_internet=False,dataset_sources=[],model_sources=[]))
    print(json.dumps(dict(shared_sources=len(shared),task=task['instance_id'],candidate_verified=True,Notebook_dispatched=False)))

if __name__=='__main__':main()
