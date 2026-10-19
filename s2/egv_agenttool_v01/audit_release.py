"""Reproducible byte/packaging audit; standard library only, no model execution."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    baseline=json.loads((HERE/'BASE_INTEGRITY.json').read_text())
    changed=[n for n,h in baseline['files'].items() if not (ROOT/n).is_file() or digest(ROOT/n)!=h]
    assert not changed,changed
    acceptance=json.loads((HERE/'CPU_FEASIBILITY.json').read_text())
    assert acceptance['passed'] and acceptance['revision']=='cpu05'
    for n,h in acceptance['tested_runtime_hashes'].items():assert digest(ROOT/n)==h,n
    expected=json.loads((HERE/'candidate.json').read_text())
    assert digest(HERE/'submission.zip')==expected['zip_sha256']
    with zipfile.ZipFile(HERE/'submission.zip') as z:
        assert z.testzip() is None
        assert set(z.namelist())==set(expected['members']) and len(z.namelist())==5
        assert 'agent.yaml' in z.namelist()
        for n,h in expected['members'].items():
            assert hashlib.sha256(z.read(n)).hexdigest()==h==digest(HERE/'candidate'/n),n
    plan_path=HERE/'MULTITASK_GPU_PROTOCOL_DRAFT.json'
    plan=json.loads(plan_path.read_text())
    freeze=json.loads((HERE/'GPU_DRAFT_FREEZE.json').read_text())
    assert plan['status']=='DRAFT_NOT_AUTHORIZED' and not plan['GPU_authorized']
    assert digest(plan_path)==freeze['protocol_sha256']
    assert len(plan['selected'])==8 and len(plan['runs'])==16
    assert len({r['instance_id'] for r in plan['selected']})==8
    assert all(r['eligible'] and r['counts']['errors']==0 for r in plan['selected'])
    orders=[]
    for pair in range(1,9):
        rows=[r for r in plan['runs'] if r['pair']==pair]
        assert len(rows)==2 and {r['arm'] for r in rows}=={'A','B'}
        orders.append(''.join(r['arm'] for r in rows))
    assert orders.count('AB')==orders.count('BA')==4
    for batch in (1,2):
        folder=HERE/'notebooks'/f'gpu-batch{batch}-draft'
        assert digest(folder/'study.ipynb')==freeze['notebooks'][str(batch)]['notebook_sha256']
        assert digest(folder/'kernel-metadata.json')==freeze['notebooks'][str(batch)]['metadata_sha256']
        notebook=json.loads((folder/'study.ipynb').read_text())
        for cell in notebook['cells']:
            compile(cell['source'],'<guarded GPU draft>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        setup=notebook['cells'][0]['source'];tree=ast.parse(setup)
        assert isinstance(tree.body[0],ast.Raise),'Draft must fail before any side effect'
        literal=next(node.value.args[0] for node in tree.body if isinstance(node,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='payload' for t in node.targets))
        payload=base64.b64decode(ast.literal_eval(literal))
        assert hashlib.sha256(payload).hexdigest()==freeze['payload_sha256']
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            assert z.testzip() is None
            assert z.read('s2/gpu_protocol.json')==plan_path.read_bytes()
            for n,h in plan['source_hashes'].items():
                assert hashlib.sha256(z.read(n)).hexdigest()==h,n
                # Legacy SDK payloads come byte-for-byte from the accepted
                # Linux archive; a Windows checkout may have CRLF conversion.
                # Compare new runtime bytes directly, and preserve/check all
                # historical checkout bytes against their separate baseline.
                if n.startswith('s2/egv_agenttool_v01/'):
                    assert digest(ROOT/n)==h,n
        assert "authorization={'authorized':False}" in notebook['cells'][1]['source']
    archives={}
    for revision in ('cpu01','cpu02','cpu03','cpu04','cpu05','env01','budget01'):
        folder=HERE/'results'/revision
        proof=json.loads((folder/'collection.json').read_text())
        assert digest(folder/'raw.zip')==proof['sha256']
        with zipfile.ZipFile(folder/'raw.zip') as z:
            assert z.testzip() is None
        archives[revision]=proof
    files={p.relative_to(HERE).as_posix():digest(p) for p in sorted(HERE.rglob('*'))
        if p.is_file() and not {'_local','__pycache__','snapshot_source','.git'}.intersection(p.relative_to(HERE).parts)
        and p.name!='INTEGRITY_MANIFEST.json'}
    result=dict(passed=True,scope='Local standard-library byte/ZIP/AST audit; not an official Runner test or GPU experiment.',
        baseline_commit=baseline['base_commit'],historical_files_checked=len(baseline['files']),historical_changed=changed,
        candidate_zip_sha256=expected['zip_sha256'],candidate_members=expected['members'],
        CPU_final_runtime_matches=True,CPU_archives=archives,GPU_drafts_match=True,GPU_runs=0,
        protocol_sha256=digest(plan_path),files=files,self_hash_excluded=True)
    (HERE/'INTEGRITY_MANIFEST.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps({k:result[k] for k in ('passed','historical_files_checked','historical_changed','CPU_final_runtime_matches','GPU_drafts_match','GPU_runs')},indent=2))


if __name__=='__main__':main()
