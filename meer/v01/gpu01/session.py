"""Source-bound three-session batches reusing the proven GPU03 coordinator.

The caller must supply a separate owner authorization record. No Kaggle API.
"""
import hashlib
import inspect
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKAGE = 'meer.v01.gpu01'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def authorize(grant, manifest, batch, payload_identity):
    """Fail closed before imports, dependency deployment, or model access.

    This validates binding, not human identity. The trusted dispatch operator
    must obtain the owner's explicit grant; model-generated JSON is not one.
    """
    if not grant or grant.get('GPU_authorized') is not True or not grant.get('owner_authorization_reference'):
        raise PermissionError('Gate F: separate explicit owner authorization is absent')
    if type(batch) is not int or batch not in (1, 2):
        raise ValueError('Batch must be 1 or 2')
    required = dict(experiment_id=manifest['experiment_id'],
                    manifest_sha256=sha(HERE / 'EXECUTION_MANIFEST.json'),
                    payload_sha256=payload_identity['payload_sha256'], batch=batch,
                    order=manifest['batches'][str(batch)], arms=manifest['arms'],
                    environment_lock_sha256=manifest['environment_lock_sha256'],
                    model_files=manifest['model']['files'], max_SaveKernel_dispatches=1,
                    max_Agent_runs=3, GPU_count=4, GPU_type='NVIDIA L4', TP=4,
                    Agent_seconds=300, platform_window_seconds=10000)
    for key, value in required.items():
        if grant.get(key) != value:
            raise PermissionError('Authorization binding mismatch: ' + key)
    if payload_identity.get('production_entry') != PACKAGE + '.session.run':
        raise ValueError('Wrong production entry')
    return dict(grant)


def coordinator(lock, grant):
    from u_re.v01.experiments.action_priority_01.real_gemma_abba03 import session as proven
    from u_re.v04.experiments.prospective_admission_01.session import native_baseline
    source = inspect.getsource(proven.run)
    def replace(before, after):
        nonlocal source
        if source.count(before) != 1:
            raise ValueError('Accepted coordinator anchor drift: ' + before)
        source = source.replace(before, after)
    replace("lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())", 'lock=LOCK')
    replace("admitted=json.loads((HERE/'ADMISSION_RECONCILIATION.json').read_bytes())", 'admitted=None')
    replace("grant=json.loads((HERE/'GPU_AUTHORIZATION.json').read_bytes())", 'grant=GRANT')
    replace("grant['max_Agent_runs']==4", "grant['max_Agent_runs']==3")
    replace("    assert admitted['status']=='EVIDENCE_RECONCILED_TWO_TASKS_ADMITTED'\n    assert [r['instance_id'] for r in admitted['tasks']]==['fastapi_9425','fastapi_14786']", "    assert mode=='GPU' and cpu_transport is None")
    replace("agent=ROOT/'u_re/v01/candidate_noegv' if arm=='A' else ROOT/'u_re/v01/experiments/action_priority_01/candidate_action_v01'", "agent=ROOT/'meer/v01/candidates'/arm")
    replace("spec=dict(instance_id=ident,arm=arm,", "spec=dict(execution_mode='GPU',instance_id=ident,arm=arm,")
    replace('from ..integrated_cpu_01.agent_phase import SubprocessManager',
            'from u_re.v01.experiments.action_priority_01.integrated_cpu_01.agent_phase import SubprocessManager')
    replace('from .ISOLATION_CANARY import CANARY',
            'from u_re.v01.experiments.action_priority_01.real_gemma_abba03.ISOLATION_CANARY import CANARY')
    replace("'GPU03_REAL_GEMMA_ABBA_COMPLETE'", "'MEER_GPU_BATCH_COMPLETE'")
    ns = dict(proven.__dict__, ROOT=ROOT, HERE=HERE,
              PRIOR=ROOT/'u_re/v01/experiments/action_priority_01/integrated_cpu_01',
              LOCK=lock, GRANT=grant, native_baseline=native_baseline, __package__=PACKAGE)
    exec(compile(source, '<MEER-bound-GPU03-coordinator>', 'exec'), ns)
    return ns['run']


async def run(output, session_started, *, batch, authorization=None, quota_at_dispatch=None):
    manifest = json.loads((HERE/'EXECUTION_MANIFEST.json').read_bytes())
    identity = json.loads((Path(output).parent/'PAYLOAD_IDENTITY.json').read_bytes())
    grant = authorize(authorization, manifest, batch, identity)
    if quota_at_dispatch is None or float(quota_at_dispatch) < 20600:
        raise ValueError('Contemporaneous quota gate failed')
    grant['quota_at_dispatch_report_seconds'] = quota_at_dispatch
    lock = json.loads((HERE/'RUNTIME_LOCK.json').read_bytes())
    lock['order'] = manifest['batches'][str(batch)]
    # Preserve the existing native PR26 environment on both sides of a batch.
    from u_re.v02.experiments.env_recovery_admission_01.runtime import install_extras, fingerprint
    from harness_v2.evidence import atomic_json
    expected = json.loads((HERE/'ENVIRONMENT_LOCK.json').read_bytes())['fingerprint']
    before = install_extras(Path(output).parent/'environment')
    if before != expected:
        raise ValueError('Frozen trusted environment drift')
    atomic_json(Path(output).parent/'PRODUCTION_ENVIRONMENT_BEFORE.json', before)
    await coordinator(lock, grant)(output, session_started, mode='GPU', quota_at_dispatch=quota_at_dispatch)
    if fingerprint() != before:
        raise ValueError('Trusted environment changed during batch')
    atomic_json(Path(output).parent/'PRODUCTION_ENVIRONMENT_AFTER.json', before)
