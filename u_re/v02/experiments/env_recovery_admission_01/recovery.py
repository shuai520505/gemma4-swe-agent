"""Actual CPU diagnostic group; never screens a new prospective task."""
import ast,asyncio,json,importlib,inspect,sys,subprocess
from pathlib import Path
from .dependencies import HERE,ROOT,sha
from .runtime import native,fingerprint,install_extras

async def run(output):
    import torch
    assert sys.platform=='linux' and sys.version_info[:2]==(3,12) and torch.cuda.device_count()==0
    from s1.task_identity import find_data,identify
    from harness_v2.evidence import atomic_json,atomic_bytes
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    data=find_data();expected=json.loads((HERE/'APPROVED_INPUT_IDENTITIES.json').read_bytes())
    lock=json.loads((ROOT/'u_re/v01/experiments/action_priority_01/integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json').read_bytes())
    sources={n:sha(Path(inspect.getfile(importlib.import_module(n))).read_bytes()) for n in lock['native_verifier_source_sha256']}
    assert sources==lock['native_verifier_source_sha256'];atomic_json(output/'official_source_hashes.json',sources)
    all_inputs=identify(data,list(expected));assert all_inputs==expected
    atomic_json(output/'INPUT_IDENTITIES.json',all_inputs)
    original=fingerprint();atomic_json(output/'ORIGINAL_ENVIRONMENT.json',original)
    assert next(r for r in original['packages'] if r['name']=='inline-snapshot')['version'] is None
    rows=[]
    for ident in ('fastapi_14246','fastapi_14609'):
        row,audit=await native(data,ident,output/'original'/ident,expected[ident]);assert row['evidence_ok']
        assert any('No module named' in e.get('details','') and 'inline_snapshot' in e.get('details','') for e in audit.get('events',[]))
        rows.append(dict(environment='ORIGINAL',**row))
    recovered=install_extras(output);atomic_json(output/'RECOVERED_ENVIRONMENT.json',recovered)
    # Owned positive AND negative assertions prove that installation did not
    # suppress mismatches or enable source/snapshot auto-update.
    canary=output/'owned_snapshot_canary';canary.mkdir()
    results=[]
    for name,value,exit_code in [('positive',1,0),('negative',2,1)]:
        file=canary/('test_'+name+'.py');file.write_text('from inline_snapshot import snapshot\ndef test_owned():\n    assert '+str(value)+' == snapshot(1)\n')
        before=sha(file.read_bytes());junit=canary/(name+'.junit.xml')
        p=subprocess.run([sys.executable,'-m','pytest',str(file),'-q','--junitxml='+str(junit)],cwd=canary,capture_output=True,text=True,timeout=60)
        atomic_bytes(canary/(name+'.stdout.log'),p.stdout.encode());atomic_bytes(canary/(name+'.stderr.log'),p.stderr.encode())
        assert p.returncode==exit_code and before==sha(file.read_bytes())
        results.append(dict(name=name,exit_code=p.returncode,source_unchanged=True,JUnit_sha256=sha(junit.read_bytes())))
    atomic_json(canary/'CANARY_RESULTS.json',dict(passed=True,results=results))
    for ident in ('fastapi_14246','fastapi_14609','fastapi_5077'):
        row,audit=await native(data,ident,output/'recovered'/ident,expected[ident]);assert row['evidence_ok']
        assert not any('No module named' in e.get('details','') and 'inline_snapshot' in e.get('details','') for e in audit.get('events',[]))
        rows.append(dict(environment='RECOVERED',role='CARRY_MIGRATION' if ident=='fastapi_5077' else 'DIAGNOSTIC_ONLY',**row))
    assert fingerprint()==recovered,'Environment drift during diagnostics'
    source=json.loads((output/'recovered/fastapi_14609/PRIVATE_BASE_SOURCE.json').read_bytes())
    classes=[n.name for n in ast.walk(ast.parse(source['fastapi/exceptions.py']['text'])) if isinstance(n,ast.ClassDef)]
    assert 'PydanticV1NotSupportedError' not in classes
    atomic_json(output/'SOURCE_API_AUDIT.json',dict(task='fastapi_14609',exception_module_sha256=source['fastapi/exceptions.py']['sha256'],exception_class_absent=True,exception_classes=classes,source_is_original_workspace=True,reference_patch_accessed=False,interpretation='Workspace API is absent irrespective of installed Pydantic version. Exact public Issue does not mandate this spelling; evaluator requires it as its realization of v1 rejection. Conditional target-related collection failure, never formally eligible.'))
    atomic_json(output/'ENVIRONMENT_RECOVERY.json',dict(status='INDEPENDENT_DEPENDENCY_RECOVERED',original=original,recovered=recovered,rows=rows,owned_assertion_canary_passed=True,native_Verifier_source_unchanged=True,inputs_unchanged=True,Agent_runs=0,Gemma_requests=0,GPU=False))
    print(json.dumps(dict(status='INDEPENDENT_DEPENDENCY_RECOVERED',rows=[dict(task=r['instance_id'],environment=r['environment'],counts=r['counts']) for r in rows])),flush=True)

if __name__=='__main__':
    import sys
    asyncio.run(run(sys.argv[1]))
