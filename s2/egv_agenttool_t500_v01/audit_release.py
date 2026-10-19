"""Read-only byte/ZIP/payload checks followed by a self-excluding manifest."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    base=json.loads((HERE/'BASE_INTEGRITY.json').read_text())
    for n,h in base['files'].items():assert sha(ROOT/n)==h,n
    accepted=json.loads((HERE/'CPU_FEASIBILITY.json').read_text());assert accepted['passed']
    for n,h in accepted['tested_runtime_hashes'].items():assert sha(ROOT/n)==h,n
    for directory,parent in ((HERE,ROOT/'s2/egv_agenttool_v01'),(HERE/'control_single_t500',ROOT/'s1/egv_v01')):
        metadata=json.loads((directory/'candidate.json').read_text())
        assert sha(directory/'submission.zip')==metadata['zip_sha256']
        with zipfile.ZipFile(directory/'submission.zip') as z,zipfile.ZipFile(parent/'submission.zip') as old:
            assert z.testzip() is None and set(z.namelist())==set(old.namelist())
            assert 'agent.yaml' in z.namelist()
            assert [n for n in z.namelist() if z.read(n)!=old.read(n)]==['eval_config.yaml']
            for n,h in metadata['members'].items():
                assert not n.startswith('/') and '..' not in Path(n).parts
                assert hashlib.sha256(z.read(n)).hexdigest()==h==sha(directory/'candidate'/n)
    plan_path=HERE/'GPU_PROTOCOL_T500_DRAFT.json';plan=json.loads(plan_path.read_text())
    freeze=json.loads((HERE/'GPU_DRAFT_FREEZE.json').read_text());assert sha(plan_path)==freeze['protocol_sha256']
    assert plan['shared_budget']['agent_seconds']==500 and plan['resource_window_seconds']==18000
    assert plan['status']=='DRAFT_NOT_AUTHORIZED' and not plan['GPU_authorized']
    assert len(plan['selected'])==8 and len(plan['runs'])==16
    assert sum(plan['runs'][i]['arm']=='A' for i in range(0,16,2))==4
    for batch in (1,2):
        folder=HERE/'notebooks'/f'gpu-batch{batch}-draft';notebook=json.loads((folder/'study.ipynb').read_text())
        assert sha(folder/'study.ipynb')==freeze['notebooks'][str(batch)]['notebook_sha256']
        assert sha(folder/'kernel-metadata.json')==freeze['notebooks'][str(batch)]['metadata_sha256']
        for cell in notebook['cells']:compile(cell['source'],'<guarded500s draft>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        tree=ast.parse(notebook['cells'][0]['source']);assert isinstance(tree.body[0],ast.Raise)
        literal=next(n.value.args[0] for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='payload' for t in n.targets))
        payload=base64.b64decode(ast.literal_eval(literal));assert hashlib.sha256(payload).hexdigest()==freeze['payload_sha256']
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            assert z.testzip() is None and z.read('s2/gpu_protocol.json')==plan_path.read_bytes()
            for n,h in plan['source_hashes'].items():
                assert hashlib.sha256(z.read(n)).hexdigest()==h,n
                if n.startswith('s2/egv_agenttool_t500_v01/'):assert sha(ROOT/n)==h,n
    archives={}
    for revision in ('cpu02','cpu03','cpu04','env01'):
        folder=HERE/'results'/revision;proof=json.loads((folder/'collection.json').read_text())
        assert sha(folder/'raw.zip')==proof['sha256']
        with zipfile.ZipFile(folder/'raw.zip') as z:assert z.testzip() is None
        archives[revision]=proof
    package=HERE/'submission_evidence/package_v1'
    assert sha(package/'submission.zip')==sha(HERE/'submission.zip')
    official=json.loads((HERE/'OFFICIAL_SUBMISSION_RECORD.json').read_text())
    assert official['request_attempts']==1 and official['submission_id']==57402336
    assert (HERE/'submission_evidence/SUBMISSION_INTENT.json').is_file()
    files={f.relative_to(HERE).as_posix():sha(f) for f in sorted(HERE.rglob('*')) if f.is_file()
        and not {'_local','__pycache__','snapshot_source','.git'}.intersection(f.relative_to(HERE).parts)
        and f.name!='INTEGRITY_MANIFEST.json'}
    result=dict(passed=True,scope='Local byte/ZIP/AST check, not new official CPU or GPU inference.',
        base_commit=base['base_commit'],historical_files_checked=len(base['files']),historical_changes=0,
        candidate_sha256=sha(HERE/'submission.zip'),single_factor_both_candidates=True,CPU_composite_acceptance=True,
        original_preparations=archives,guarded_GPU_drafts_match=True,research_GPU_runs=0,
        official_submission_requests=1,official_submission_id=official['submission_id'],official_last_status=official['status'],
        official_public_score=official['public_score'],files=files,self_excluded=True)
    (HERE/'INTEGRITY_MANIFEST.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in result.items() if k not in ('files','original_preparations')},indent=2))


if __name__=='__main__':main()
