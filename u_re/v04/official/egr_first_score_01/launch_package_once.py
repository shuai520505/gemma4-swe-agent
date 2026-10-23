"""One authorized CPU packaging save; scoring submission is a separate dispatch."""
import json,types,hashlib,subprocess,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
SMOKE=ROOT/'u_re/v01/experiments/gemma_smoke_01'
def main():
    spec=json.loads((HERE/'BUILD.json').read_text(encoding='utf-8'))
    original=ROOT/'u_re/v01/experiments/fastapi_pilot_01/attempts/cpu02/dispatch.py'
    m=types.ModuleType('full_packaging_dispatch');exec(compile(original.read_bytes(),str(original),'exec'),m.__dict__)
    m.EXECUTION_ID=spec['execution_id'];m.SLUG=spec['slug']
    def auth(grant,identity):
        assert grant['execution_id']==identity['execution_id'] and grant['slug']==identity['slug']
        assert grant['max_SaveKernel_dispatches']==1 and grant['human_message_reference']
        for k in ('Notebook_sha256','wire_sha256','payload_sha256'):assert grant[k]==identity[k]
    m.checked_authorization=auth
    pre=HERE/'preflight';pre.mkdir(exist_ok=True)
    from u_re.v01.experiments.fastapi_pilot_01 import auth_diagnose
    auth_diagnose.HERE=pre
    auth_diagnose.diagnose()
    launcher=SMOKE/'cpu_launch_once.py';l=types.ModuleType('full_packaging_preflight');l.__file__=str(launcher);l.__package__='u_re.v01.experiments.gemma_smoke_01'
    exec(compile(launcher.read_bytes(),str(launcher),'exec'),l.__dict__);l.CPU=HERE;l.SLUG=spec['slug']
    raw=(HERE/'notebook/study.ipynb').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==spec['Notebook_sha256']
    assert hashlib.sha256(json.dumps(json.loads(raw)).encode()).hexdigest()==spec['wire_sha256']
    gates=l.preflight();gates.update(payload_integrity=True,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    grant=dict(execution_id=spec['execution_id'],slug=spec['slug'],max_SaveKernel_dispatches=1,human_message_reference='Human user: 你把当前EGR提交并且取得分数. One frozen EGR V0.4 CPU packaging Notebook and one official scoring submission; no research GPU.',**{k:spec[k] for k in ('Notebook_sha256','wire_sha256','payload_sha256')})
    m.exclusive(HERE/'AUTHORIZATION.json',grant)
    from kaggle import api
    c=m.Controller(HERE/'execution',spec)
    try:
        result=c.execute(grant,gates,lambda:api.kernels_push(str(HERE/'notebook'),timeout='600',acc=None))
        # Safe canonical ref is independently checked during collection; keep UNKNOWN events.
        ref=getattr(result,'ref',None)
        if ref not in (spec['slug'],'/code/'+spec['slug']):ref=None
        m.exclusive(HERE/'SDK_SAFE_RESULT.json',dict(id=getattr(result,'kernel_id',None),version=getattr(result,'version_number',None),ref=ref))
    finally:m.exclusive(HERE/'DISPATCH_SUMMARY.json',dict(dispatches=c.dispatches,states=c.journal.states(),GPU=False,model_inference=False))
if __name__=='__main__':main()
