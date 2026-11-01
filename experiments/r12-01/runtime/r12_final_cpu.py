"""CPU plumbing replay through PR43 worker/Runner/supervisor, never a model benchmark."""
import asyncio,hashlib,http.server,json,os,shlex,sys,threading,time,zipfile
from pathlib import Path
from unittest.mock import patch
from r12_adapter import run,HASHES,trusted_binding
from gemma_pair.common import write
from harness_v2.supervisor import supervise

HERE=Path(__file__).parent
sha=lambda b:hashlib.sha256(b).hexdigest()
MARKER='# R12 CPU plumbing marker; no repair inference.\n'

def admission(row,supervisor):
    if not supervisor['allow_next_run'] or row is None:return 'STOP_INFRASTRUCTURE'
    if row.get('evidence_complete') is not True:return 'STOP_EVIDENCE'
    e=row.get('evaluation',{})
    if not row.get('cleanup') or not e.get('check_unchanged') or not e.get('source_unchanged_by_checks'):return 'STOP_TRUST'
    if not e.get('positive_controls_passed'):return 'STOP_ENVIRONMENT'
    if 'context_length_exceeded' in str(row.get('agent_error')):return 'STOP_BACKEND_COMPATIBILITY'
    return 'CONTINUE'

def child(specfile,out):
    import torch
    assert torch.cuda.device_count()==0
    spec=json.loads(Path(specfile).read_bytes());case=spec['simulation_case'];binding=spec['binding']
    if case=='behavior_failure':binding['edit_new']=binding['edit_old']+'# CPU deliberate failing sentinel.\n'
    calls=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            assert body['model']=='SIMULATED_CPU_NO_MODEL' and not body.get('stream')
            k=len(calls);calls.append(body)
            if case=='context_error':
                response=dict(error=dict(message='SIMULATED context_length_exceeded',type='invalid_request_error',code='context_length_exceeded'));status=400
            else:
                sequence=[('get_status',{})]
                if case=='missing_argument':sequence.append(('edit_file',dict(filepath=binding['edit_path'],new_string='invalid_missing_old_string')))
                sequence.append(('run_command',dict(command=binding['boundary_command'])))
                if case!='no_patch':sequence.append(('edit_file',dict(filepath=binding['edit_path'],old_string=binding['edit_old'],new_string=binding['edit_new'])))
                if case not in ('timeout_fallback','no_patch'):sequence.append(('submit_patch',{}))
                if k<len(sequence):
                    name,args=sequence[k];message=dict(role='assistant',content=None,tool_calls=[dict(id='cpu_'+str(k),type='function',function=dict(name=name,arguments=json.dumps(args)))])
                    finish='tool_calls'
                else:message=dict(role='assistant',content='CPU simulation complete.');finish='stop'
                response=dict(id='cpu-simulation-'+str(k),object='chat.completion',created=1,model='SIMULATED_CPU_NO_MODEL',choices=[dict(index=0,message=message,finish_reason=finish)])
                # Deliberately omit usage: absent measurements must remain unknown.
                status=200
            raw=json.dumps(response).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',8000),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    import gemma_pair.worker as worker
    import r12_adapter as adapter
    original_binding=adapter.bind_manager
    def fault_manager(binding):
        Parent=original_binding(binding)
        class SubprocessManager(Parent):
            def start(self):
                sid=super().start()
                if case=='isolation_failure':raise RuntimeError('CPU_INJECTED_ISOLATION_ADMISSION_FAILURE')
                return sid
            def cleanup_all(self):
                super().cleanup_all()
                if case=='cleanup_failure':raise RuntimeError('CPU_INJECTED_CLEANUP_RECEIPT_FAILURE_AFTER_SAFE_CLEANUP')
        return SubprocessManager
    Original=worker.DurableContext
    class SimulationContext(Original):
        def handle_adk_event(self,event,agent_name=None):
            super().handle_adk_event(event,agent_name)
            if case=='timeout_fallback' and not getattr(self,'clock_injected',False):
                parts=getattr(getattr(event,'content',None),'parts',[]) or []
                if any(getattr(p,'function_response',None) and p.function_response.name=='edit_file' for p in parts):
                    self.clock_injected=True;self.agent_start_time-=481
                    self.journal.append(dict(kind='CPU_SIMULATED_CLOCK_ADVANCE',seconds=481,frozen_budget_unchanged=True))
    try:
        with patch.object(worker,'DurableContext',SimulationContext),patch.object(adapter,'bind_manager',fault_manager):asyncio.run(run(spec,out))
        if case=='evidence_incomplete':
            (Path(out)/'adk_events.jsonl').unlink()
            from r12_evidence import finalize
            assert not finalize(out)['evidence_complete']
    finally:
        server.shutdown();server.server_close();thread.join(timeout=10)
        write(Path(out)/'SIMULATED_TRANSPORT.json',dict(requests=len(calls),usage=None,real_model_requests=0,server_stopped=not thread.is_alive(),case=case))

def main(out):
    import torch
    from swegemma.harness.container_setup import extract_snapshot
    from egrd.v032.evaluate import source_identity
    assert torch.cuda.device_count()==0
    out=Path(out);out.mkdir()
    environment=json.loads((Path(__import__('gemma_pair.coordinator',fromlist=['x']).__file__).with_name('GPU_ENVIRONMENT_LOCK.json')).read_bytes())
    model=next(p.parent for p in Path('/kaggle/input').rglob('config.json') if 'gemma-4-31b-it-qat-w4a16-ct' in p.parts and p.parent.name=='2' and (p.parent/'model.safetensors').is_file())
    assets={}
    for p in model.rglob('*'):
        if p.is_file():
            h=hashlib.sha256()
            with p.open('rb') as stream:
                for block in iter(lambda:stream.read(8388608),b''):h.update(block)
            assets[p.relative_to(model).as_posix()]=h.hexdigest()
    assert assets==environment['model_files']
    write(out/'READONLY_MODEL_MOUNT.json',dict(source=environment['model_source'],files=assets,CPU_only=True,inference_calls=0,weights_loaded_into_model=False))
    cohort=json.loads((HERE/'COHORT_LOCK.json').read_bytes())
    assert sha((HERE/'COHORT_LOCK.json').read_bytes())=='3e8dddc0b06c1d3cbffb2786b90b01c12593fe8041bf79d09a7599881d633269'
    for n,h in HASHES.items():assert sha((HERE/'candidates'/(n+'.zip')).read_bytes())==h
    archive=next(Path('/kaggle/input').rglob('gemma-r12-preflight-v4.zip'))
    assert sha(archive.read_bytes())=='a553bcd5150eecd6a6d92dc6d7555f8f88035e43111ed69b2d1557582102227b'
    prepared=out/'prepared';prepared.mkdir()
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        # Only prepared snapshots, locked wheels and prior receipts. No acceptance rerun.
        for info in z.infolist():
            p=Path(info.filename)
            if p.parts[0]=='tasks' and (p.name in ('base-flat.tgz','TASK_RESULT.json') or 'wheels' in p.parts and p.suffix=='.whl'):
                assert '..' not in p.parts and not p.is_absolute();dest=prepared/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(info))
        trusted=out/'frozen-checks';trusted.mkdir()
        (trusted/'probe.py').write_bytes(z.read('extension/r12_issue_checks.py'))
        # Exact programs from the prior accepted adapter, including unchanged assertions.
        import ast
        tree=ast.parse(z.read('extension/r12_preflight.py'))
        assignment=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='programs' for t in n.targets))
        for key,value in zip(assignment.value.keys,assignment.value.values):
            if ast.literal_eval(key)!='probe.py':(trusted/ast.literal_eval(key)).write_bytes(ast.literal_eval(value))
    inputpath=next(Path('/kaggle/input').rglob('R12_INPUTS.json'));inputs=json.loads(inputpath.read_bytes())
    assert sha(inputpath.read_bytes())=='a842ac64857cf6b5710e594ba82ac733b8b186f2dc88bbc1ae6b73b025d3872d'
    assert inputs['rows']==cohort['rows']
    for s in inputs['sources']:
        row=next(r for r in cohort['rows'] if r['instance_id']==s['instance_id'])
        assert s['repo']==row['repo'] and s['base_commit']==row['base_commit'] and s['issue_sha256']==sha(row['problem_statement'].encode())
        assert s['git_tree_verified'] and s['actual_git_tree']==s['expected_git_tree']
    for n,h in inputs['files'].items():assert sha((inputpath.parent/n).read_bytes())==h
    bindings={};assembly=[]
    import tarfile
    targets={'django__django-11964':'django/db/models/enums.py','pydata__xarray-6721':'xarray/core/dataset.py','pytest-dev__pytest-5631':'src/_pytest/python.py'}
    for row in cohort['rows']:
        ident=row['instance_id'];base=prepared/'tasks'/ident;prior=json.loads((base/'TASK_RESULT.json').read_bytes());assert prior['status']=='PASS'
        extras={n:h for n,h in prior['extra_wheels'].items()}
        for n,h in extras.items():assert sha((inputpath.parent/n).read_bytes())==h
        taskfile=out/(ident+'.json');write(taskfile,row)
        with tarfile.open(base/'base-flat.tgz') as tar:
            production={m.name.lstrip('./'):sha(tar.extractfile(m).read()) for m in tar.getmembers() if m.isfile() and m.name.endswith('.py') and Path(m.name).name not in ('conftest.py','setup.py') and not any(p in ('tests','test','docs','.git') for p in Path(m.name).parts)}
            raw=tar.extractfile(targets[ident]).read().decode();first=raw.splitlines(keepends=True)[0]
        binding=dict(issue=row,task={},data=str(out),taskfile=str(taskfile),snapshot=str(base/'base-flat.tgz'),wheels=str(base/'wheels'),base_source_identity=prior['source_identity'],runtime_extra_wheels=[str(inputpath.parent/n) for n in extras],runtime_extra_sha256=extras,production_files=production,edit_path=targets[ident],edit_old=first,edit_new=first+MARKER)
        real=trusted_binding(binding,trusted)
        write(out/(ident+'.GPU_BINDING.json'),real)
        # Separate CPU-only sentinel check; no original Issue behavior executed.
        probe=out/(ident+'.simulation-probe.py')
        probe.write_text("import json,os\nfrom pathlib import Path\nassert os.geteuid()!=0\np=Path('/workspace/"+targets[ident]+"')\npassed="+repr(MARKER)+" in p.read_text()\nPath('/tmp/probe.json').write_text(json.dumps(dict(classification='CHECK_PASS_NON_DISCRIMINATING' if passed else 'TARGET_BEHAVIOR_FAILURE',controls_passed=True)))\nraise SystemExit(0 if passed else 1)\n")
        common=out/'simulation-common.py';common.write_text('# CPU sentinel, not an Issue test.\n')
        binding.update(task=dict(diagnostic_path=probe.name),evaluation_programs={'probe.py':str(probe),'common.py':str(common)},evaluation_scope='CPU plumbing sentinel only; NOT repair capability or original Issue acceptance')
        boundary="import os,socket; from pathlib import Path; assert os.geteuid()!=0; assert not Path('/evaluation').exists(); assert not Path('/kaggle/input').exists(); assert not Path('/proc').exists(); assert not os.access('/opt/approved',os.W_OK); print('BOUNDARY_PASS')"
        binding['boundary_command']='python -c '+shlex.quote(boundary)
        bindings[ident]=binding
        assembly.append(dict(instance_id=ident,base_commit=row['base_commit'],issue_sha256=sha(row['problem_statement'].encode()),source_identity=prior['source_identity'],snapshot_sha256=sha((base/'base-flat.tgz').read_bytes()),wheels={p.name:sha(p.read_bytes()) for p in (base/'wheels').glob('*.whl')},extra_wheels=extras,production_files=len(production),trusted_check_hashes={n:sha(Path(p).read_bytes()) for n,p in real['evaluation_programs'].items()}))
    write(out/'ASSEMBLY.json',assembly)
    dispatch=out/'R12_DISPATCH_INPUTS.zip'
    with zipfile.ZipFile(dispatch,'w',zipfile.ZIP_DEFLATED) as z:
        for p in [*prepared.rglob('*'),*trusted.rglob('*'),*out.glob('*.GPU_BINDING.json')]:
            if p.is_file():z.write(p,'integration/'+p.relative_to(out).as_posix())
    dispatch_manifest=dict(CPU_dispatch_archive_sha256=sha(dispatch.read_bytes()),cohort_lock_sha256=sha((HERE/'COHORT_LOCK.json').read_bytes()),candidate_zip_sha256=HASHES,task_input_manifest_sha256=sha(inputpath.read_bytes()),sessions=[dict(instance_id=i,candidate=n) for i,n in cohort['order']])
    from r12_coordinator import materialize
    rematerialized=materialize(dispatch,dispatch_manifest,out/'dispatch-rebinding')
    for ident,binding in rematerialized.items():
        original=bindings[ident]
        assert sha(Path(binding['snapshot']).read_bytes())==sha(Path(original['snapshot']).read_bytes())
        assert binding['issue']==original['issue'] and binding['base_source_identity']==original['base_source_identity']
        assert Path(binding['taskfile']).is_file() and Path(binding['wheels']).is_dir()
        assert all(Path(p).is_file() for p in binding['evaluation_programs'].values())
    write(out/'DISPATCH_REBINDING.json',dict(passed=True,manifest=dispatch_manifest,bindings=rematerialized))
    cases=['normal','missing_argument','timeout_fallback','no_patch','behavior_failure','normal','normal','normal','context_error'];records=[]
    # Exercise the existing Coordinator's actual schedule AST, excluding only
    # GPU/server allocation. No separately reimplemented scheduling loop.
    import ast,types
    import gemma_pair.coordinator as coordinator
    source=Path(coordinator.__file__).read_text();tree=ast.parse(source)
    function=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='run')
    loop=next(n for n in ast.walk(function) if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple) and any(isinstance(x,ast.Name) and x.id=='index' for x in n.target.elts))
    replay=ast.AsyncFunctionDef(name='replay',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[loop],decorator_list=[])
    async def idle(*args,**kwargs):pass # only the readiness wait is simulated
    namespace=dict(coordinator.__dict__,asyncio=asyncio,supervise=supervise,require_idle=idle,
        out=out,data=bindings,order=cohort['order'],window=18000,started=time.monotonic(),
        seconds_for=lambda _:480,model='SIMULATED_CPU_NO_MODEL',server=types.SimpleNamespace(base_url='CPU_MOCK_NO_SERVER'),
        results=[],journal=__import__('harness_v2.evidence',fromlist=['Journal']).Journal(out),
        plan=dict(CPU_simulation=True,simulation_cases=cases,worker_module='r12_final_cpu',new_explicit_GPU_authorization=False))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[replay],type_ignores=[])),'PR43_COORDINATOR_CPU_SCHEDULE','exec'),namespace)
    stop=None
    try:asyncio.run(namespace['replay']())
    except AssertionError as e:stop=str(e)
    for index,item in enumerate(namespace['results']):
        records.append(dict(index=index+1,instance_id=item['task'],candidate=item['candidate'],simulation_case=cases[index],supervisor=item['worker'],result=item['result'],admission=admission(item['result'],item['worker'])))
    write(out/'INTEGRATION_RESULTS.json',dict(CPU_only=True,records=records,coordinator_stop=stop,real_Gemma_requests=0,original_Issue_acceptance_reruns=0,repair_evidence=False))
    assert len(records)==9 and stop=='R12 infrastructure/trust/backend stop condition',(len(records),stop)
    for r in records:
        row=r['result'];case=r['simulation_case'];assert row is not None and row['cleanup'] and r['supervisor']['allow_next_run']
        if case in ('normal','missing_argument'):assert row['patch_submitted'] and row['patch_bytes']>0 and row['evaluation']['scoped_development_pass']
        if case=='timeout_fallback':assert not row['patch_submitted'] and row['patch_bytes']>0 and row['agent_seconds']>=480 and row['evaluation']['scoped_development_pass']
        if case=='no_patch':assert row['patch_bytes']==0 and not row['patch_submitted']
        if case=='behavior_failure':assert row['evaluation']['target_failed'] and not row['evaluation']['scoped_development_pass']
        if case=='context_error':assert r['admission']=='STOP_BACKEND_COMPATIBILITY'
    # Admission faults use persisted copies; never create an actual leaked sandbox.
    import copy
    good=records[0];faults=[]
    for kind in ['isolation','cleanup','evidence','context']:
        row=copy.deepcopy(good['result']);supervisor=copy.deepcopy(good['supervisor'])
        if kind=='isolation':row['evaluation']['check_unchanged']=False
        elif kind=='cleanup':row['cleanup']=False
        elif kind=='evidence':row=None
        else:row['agent_error']='context_length_exceeded'
        decision=admission(row,supervisor);assert decision.startswith('STOP')
        faults.append(dict(injected_receipt_fault=kind,decision=decision,executed_prefix=[1,2,3],remaining=[dict(index=i,status='NOT_RUN') for i in range(4,10)]))
    write(out/'STOP_RULE_TESTS.json',dict(scope='Admission receipt fault injection, not real isolation/cleanup failure execution',cases=faults))
    actual_faults=[]
    for case in ('isolation_failure','cleanup_failure','evidence_incomplete'):
        binding=bindings[cohort['order'][0][0]]
        spec=dict(binding=binding,candidate='BASELINE',model_path='SIMULATED_CPU_NO_MODEL',CPU_simulation=True,simulation_case=case)
        path=out/'specs'/(case+'.json');write(path,spec);directory=out/'fault-injection'/case
        outcome=supervise([sys.executable,str(Path(__file__)),str(path),str(directory)],directory,outer_seconds=1080,stage_caps=dict(prepare_agent=240,agent=525,save_patch=60,verification=240,persist=60,cleanup=120),cwd=str(HERE))
        row=json.loads((directory/'SESSION_RESULT.json').read_bytes()) if (directory/'SESSION_RESULT.json').exists() else None
        decision=admission(row,outcome);assert decision.startswith('STOP')
        registries=list(directory.rglob('owned_uids.json'));assert registries
        for p in registries:
            for entry in json.loads(p.read_bytes())['entries']:assert not Path(entry['root']).exists() and not Path(entry['lease']).exists()
        actual_faults.append(dict(case=case,decision=decision,supervisor=outcome,owned_roots_and_leases_removed=True,remaining=[dict(index=i,status='NOT_RUN') for i in range(4,10)]))
    write(out/'WORKER_FAULT_TESTS.json',actual_faults)
    result=dict(CPU_only=True,records=records,stop_rule_tests=faults,worker_fault_tests=actual_faults,real_Gemma_requests=0,GPU_sessions=0,original_Issue_acceptance_reruns=0,repair_evidence=False)
    write(out/'INTEGRATION_RESULTS.json',result)
    print('CPU_REPLAY_FINISHED',flush=True)

if __name__=='__main__':
    if len(sys.argv)==3:child(sys.argv[1],sys.argv[2])
    else:main(sys.argv[1])
