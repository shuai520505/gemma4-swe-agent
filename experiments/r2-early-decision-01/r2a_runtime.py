"""Thin shared adapters over PR43/R12 isolation and unmodified official SDK."""
import hashlib,io,json,shlex,time,zipfile
from pathlib import Path
from dataclasses import asdict
from gemma_pair.sandbox import SubprocessManager as PriorManager
from env_runtime_repair import repair
from harness_v2.evidence import Journal
from gemma_pair.common import config

HERE=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,default=str)+'\n')

def package(name,out,model_path='CPU_ONLY_NO_REQUESTS'):
    import yaml
    from adk_submission import ModelRegistry,compile_submission,validate_directory
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.config import build_submission_limits
    from swegemma.context import SwegemmaContext
    plan=json.loads((HERE/'EXECUTION_PLAN.json').read_bytes())
    raw=(HERE/'candidates'/(name+'.zip')).read_bytes();assert sha(raw)==plan['candidate_sha256'][name]
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None and set(z.namelist())=={'agent.yaml','eval_config.yaml','configs/sampling.yaml','prompts/system.md'}
        z.extractall(out)
    budget=yaml.safe_load((out/'eval_config.yaml').read_text())['evaluation']
    assert budget==dict(timeout_seconds=240,max_tool_calls=28,max_time_minutes=8,max_turns=80)
    reg=ModelRegistry();reg.register('gemma-4-31b-it-qat-w4a16-ct',LiteLlm(model='openai/'+model_path,api_base='http://127.0.0.1:8000/v1',api_key='EMPTY'))
    limits,constraints=build_submission_limits();validate_directory(out,limits=limits)
    agent=compile_submission(out,SwegemmaContext().create_tools(),reg,limits=limits,generation_constraints=constraints)
    return reg,limits,constraints,agent,budget

class SubprocessManager(PriorManager):
    """Same inherited non-root chroot; passive evidence outside tool return path."""
    def __init__(self,*args,**kwargs):
        self.project_version=kwargs.pop('project_version',None)
        self.junit_captures=[];self.command_records=[];self.production_observations=[]
        super().__init__(*args,**kwargs)
    def start(self):
        sid=super().start()
        try:
            root=self.sandboxes[sid]['root'];repair(root)
            runtime=HERE/'runtime311'
            if runtime.exists():
                import shutil,subprocess,re,os
                import stat
                # This pinned standalone build uses the normal /dev/urandom
                # fallback for hash initialization. Expose only read-only RNG
                # character devices, never /proc, host mounts or GPU devices.
                for name,minor in [('urandom',9),('random',8)]:
                    device=root/'dev'/name
                    assert not device.exists() and not device.is_symlink()
                    os.mknod(device,stat.S_IFCHR|0o444,os.makedev(1,minor));device.chmod(0o444)
                    observed=device.stat();assert stat.S_ISCHR(observed.st_mode) and observed.st_rdev==os.makedev(1,minor)
                shutil.copytree(runtime,root/'opt/python311',symlinks=True)
                dependencies={}
                for elf in [runtime/'bin/python3.11']+list(runtime.rglob('*.so*')):
                    if not elf.is_file():continue
                    linked=subprocess.run(['ldd',str(elf)],capture_output=True,text=True,timeout=20,env=dict(os.environ,LD_LIBRARY_PATH=str(runtime/'lib')))
                    assert linked.returncode==0 and 'not found' not in linked.stdout,(str(elf),linked.stdout,linked.stderr)
                    for name in re.findall(r'(?:=>\s*)?(/[^\s()]+)',linked.stdout):
                        source=Path(name).resolve()
                        if source.is_relative_to(runtime.resolve()):continue
                        target=root/name.lstrip('/');target.parent.mkdir(parents=True,exist_ok=True)
                        if not target.exists():shutil.copyfile(source,target);target.chmod(0o755)
                        dependencies[name]=sha(target.read_bytes())
                write(self.journal.directory/('PY311_SYSTEM_LIBS_'+sid+'.json'),dependencies)
                # Standalone distributions need not provide an unversioned python3.
                # Bind every task command/shebang to the same versioned interpreter;
                # the inherited host executable must not win PATH resolution.
                for relative,target in [('opt/python311/bin/python3','python3.11'),('usr/bin/python3','/opt/python311/bin/python3.11'),('usr/local/bin/python3','/opt/python311/bin/python3.11')]:
                    alias=root/relative
                    if alias.exists() or alias.is_symlink():alias.unlink()
                    alias.symlink_to(target)
                bindings={}
                for name in ('pip','pip3','pip3.11'):
                    entry=root/'opt/python311/bin'/name
                    if entry.exists() or entry.is_symlink():entry.unlink()
                    entry.write_text('#!/usr/bin/python3\nfrom pip._internal.cli.main import main\nraise SystemExit(main())\n');entry.chmod(0o755)
                    bindings[str(entry.relative_to(root))]=sha(entry.read_bytes())
                write(self.journal.directory/('TASK_INTERPRETER_BINDINGS_'+sid+'.json'),dict(Python='3.11.9',entrypoints=bindings,preload='/opt/python311/lib/libpython3.11.so.1.0',reason='Standalone DT_AUXILIARY $ORIGIN cannot resolve without /proc; explicit confined library path, no host/proc mount'))
            probe="import os,socket,sys;from pathlib import Path;print(sys.version,sys.executable);assert len(os.urandom(16))==16;assert os.getuid()!=0;assert not Path('/kaggle/input').exists() and not Path('/proc').exists();\ntry: socket.socket(socket.AF_INET,socket.SOCK_STREAM)\nexcept PermissionError: print('NONROOT_CHROOT_NETWORK_DENIED')\nelse: raise AssertionError('NETWORK_SOCKET_NOT_DENIED')"
            checked=self.exec(sid,'printf PRE_TASK_PYTHON_CHECK; type -a python3; python3 -c '+shlex.quote(probe),timeout=10)
            write(self.journal.directory/('ISOLATION_'+sid+'.json'),asdict(checked))
            if checked.exit_code:
                diagnostics={}
                for label,argv in [('host_python',[__import__('sys').executable,'--version']),('standalone_host',[str(runtime/'bin/python3.11'),'--version']),('root_elf_ldd',['ldd',str(root/'opt/python311/bin/python3.11')])]:
                    r=subprocess.run(argv,capture_output=True,text=True,timeout=20)
                    diagnostics[label]=dict(argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr)
                for label,f in [('runtime_binary',root/'opt/python311/bin/python3.11'),('runtime_library',root/'opt/python311/lib/libpython3.11.so.1.0')]:
                    diagnostics[label]=dict(sha256=sha(f.read_bytes()),has_BytesMain_symbol=b'Py_BytesMain\0' in f.read_bytes())
                debug=self.exec(sid,'type -a python3; LD_DEBUG=libs /opt/python311/bin/python3.11 --version',timeout=10)
                diagnostics['confined_loader']=asdict(debug)
                write(self.journal.directory/('STARTUP_DIAGNOSTICS_'+sid+'.json'),diagnostics)
            assert checked.exit_code==0 and 'NONROOT_CHROOT_NETWORK_DENIED' in checked.stdout,(checked.exit_code,checked.stderr)
            initialized=super().exec(sid,'git init -q /workspace',timeout=10)
            assert initialized.exit_code==0,'GIT_WORKSPACE_INITIALIZATION_FAILED'
            return sid
        except BaseException:self.stop(sid);raise
    def _process(self,sid,mode,argument,data=None,timeout=None):
        ctx=getattr(self,'context',None)
        active=ctx is not None and ctx.agent_start_time is not None and ctx.agent_end_time is None
        before=time.monotonic()
        def fingerprint():
            import subprocess
            ws=self.sandboxes[sid]['workspace']
            r=subprocess.run(['git','-c','safe.directory='+str(ws),'-C',str(ws),'ls-files','-z'],capture_output=True,check=True)
            files={}
            for n in r.stdout.decode().split('\0'):
                p=Path(n)
                if not n or p.suffix!='.py' or p.name in ('conftest.py','setup.py') or p.name.startswith('test_') or any(q in ('tests','test','testing') for q in p.parts):continue
                f=ws/p
                if f.is_file() and not f.is_symlink():files[n]=sha(f.read_bytes())
            return files
        if active and not hasattr(self,'base_production'):self.base_production=fingerprint()
        result=super()._process(sid,mode,argument,data=data,timeout=timeout)
        if active:
            current=fingerprint();changed=sorted(n for n,h in self.base_production.items() if current.get(n)!=h)
            event=dict(kind='production_version_observed',before=before,after=time.monotonic(),source_identity=sha(json.dumps(current,sort_keys=True).encode()),changed_files=changed,scope='Tracked production Python files; new/untracked source timing requires later review, not assumed zero')
            if changed and not getattr(self,'first_edit_recorded',False):
                self.first_edit_recorded=True;event['first_production_edit_observed']=True
            self.journal.append(event);self.production_observations.append(event)
        return result
    def exec(self,sid,command,*,timeout=None):
        verification='--junitxml=' in command
        def source_state():
            ws=self.sandboxes[sid]['workspace']
            return {p.relative_to(ws).as_posix():sha(p.read_bytes()) for p in ws.rglob('*.py') if '.git' not in p.relative_to(ws).parts and p.is_file() and not p.is_symlink()}
        before_files=source_state() if verification else None
        if (self.sandboxes[sid]['root']/'opt/python311').exists():
            command='export PATH=/opt/python311/bin:$PATH PYTHONHOME=/opt/python311 LD_PRELOAD=/opt/python311/lib/libpython3.11.so.1.0 LD_LIBRARY_PATH=/opt/python311/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}; '+command
        if self.project_version:
            command='export SETUPTOOLS_SCM_PRETEND_VERSION='+shlex.quote(self.project_version)+'; '+command
        before=time.monotonic();res=super().exec(sid,command,timeout=timeout)
        self.command_records.append(dict(command=command,start=before,end=time.monotonic(),result=asdict(res)))
        if '--junitxml=' in command:
            after_files=source_state()
            self.verification_guard=dict(unchanged=before_files==after_files,before_sha256=sha(json.dumps(before_files,sort_keys=True).encode()),after_sha256=sha(json.dumps(after_files,sort_keys=True).encode()),changed_files=sorted(n for n in set(before_files)|set(after_files) if before_files.get(n)!=after_files.get(n)),scope='All Python production and test files in fresh trusted workspace; observed postcondition, no write-denial claim')
            write(self.journal.directory/'VERIFICATION_SOURCE_GUARD.json',self.verification_guard)
            import re
            m=re.search(r'--junitxml=([^\s]+)',command)
            if m:
                path=self.sandboxes[sid]['root']/m.group(1).lstrip('/')
                if path.is_file():
                    data=path.read_bytes();name='native-junit-'+str(len(self.junit_captures))+'.xml'
                    dest=self.journal.directory/name;dest.write_bytes(data)
                    self.junit_captures.append(dict(path=str(dest),sha256=sha(data)))
        return res

def context_config(name,out,snapshot,taskfile,wheels,model='CPU_ONLY_NO_REQUESTS'):
    reg,lim,con,agent,budget=package(name,Path(out)/'candidate',model)
    cfg=config(Path(out)/'candidate',reg,lim,con,budget,taskfile,snapshot,wheels,out)
    return cfg,agent

def nodes_summary(xml,task):
    import xml.etree.ElementTree as ET
    root=ET.fromstring(xml);cases=[]
    for tc in root.findall('.//testcase'):
        n=tc.get('name','');c=tc.get('classname','');names={n,c+'::'+n,c+'.'+n,c.replace('.','/')+'.py::'+n}
        if '[' in n:names.add(n.split('[',1)[0])
        outcome=next((x for x in ('failure','error','skipped') if tc.find(x) is not None),'pass')
        cases.append((names,outcome))
    ambiguous=[]
    def outcomes(req):
        short=req.split('::')[-1]
        if '[' in short and not short.endswith(']'):
            ambiguous.append(req);return None
        exact=[o for names,o in cases if req in names or short in names]
        if exact:return exact
        if '[' not in short:
            return [o for names,o in cases if any(n.split('[')[0].split('::')[-1].split('.')[-1]==short for n in names)]
        return []
    controls={r:outcomes(r) for r in task.PASS_TO_PASS}
    targets={r:outcomes(r) for r in task.FAIL_TO_PASS}
    known={k:v for k,v in controls.items() if v is not None}
    return dict(tests=len(cases),errors=sum(o=='error' for _,o in cases),passed=sum(o=='pass' for _,o in cases),
        positive_controls_passed=bool(known) and all(o and set(o)=={'pass'} for o in known.values()),
        raw_all_positive_nodes_confirmed=not ambiguous and bool(controls) and all(o and set(o)=={'pass'} for o in controls.values()),
        ambiguous_metadata_nodes=ambiguous,ambiguous_metadata_outcome='UNKNOWN' if ambiguous else 'NONE',
        original_target_failure=bool(targets) and any(o and 'failure' in o for o in targets.values()),
        controls=controls,targets=targets,matching='Exact full parameter ID or exact function name; no prefix matching. Malformed metadata preserved as UNKNOWN. Official verifier and all test expectations remain unchanged.')

async def native_verify(issue,trusted,snapshot,wheels,out,patch=''):
    from swegemma.models import Task
    from swegemma.harness.verification import verify_task
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    task=Task(**issue,test_patch=trusted['test_patch'],FAIL_TO_PASS=tuple(trusted['FAIL_TO_PASS']),PASS_TO_PASS=tuple(trusted['PASS_TO_PASS']))
    cfg,_=context_config('R2',out,snapshot,HERE/'ISSUES.agent.json',wheels)
    version=next(r['version'] for r in json.loads((HERE/'TASK_IDENTITY_LOCK.json').read_bytes())['rows'] if r['instance_id']==issue['instance_id'])
    mgr=SubprocessManager(journal=Journal(out),base_dir=out/'roots',task_wheels=Path(wheels),timeout_seconds=240,project_version=version)
    try:
        result=await verify_task(mgr,cfg,task,Path(snapshot),agent_patch=patch,start_time=time.perf_counter())
        row=result.model_dump(mode='json',exclude={'trace'})
        row['error']=row.get('error_message')
        row['verification_source_guard']=getattr(mgr,'verification_guard',None)
        if mgr.junit_captures:
            xml=Path(mgr.junit_captures[-1]['path']).read_text()
            row['observed_junit']=nodes_summary(xml,task)
            from independent_exact_evaluator import validate,BARE_NODES_MODULES,infrastructure_controls
            allowed=('tests/config/test_config.py::test_csv_regex_comma_in_quantifier[foo,',) if issue['instance_id']=='pylint-dev__pylint-8898' else ()
            row['independent_exact']=validate(xml,row['test_exit_code'],task.FAIL_TO_PASS,task.PASS_TO_PASS,allowed,bare_module=BARE_NODES_MODULES.get(issue['instance_id']))
            row['infrastructure_controls']=infrastructure_controls(row['observed_junit'],issue['instance_id'])
        row['endpoint']='Unmodified swegemma SDK on selected public SWE-bench; not hidden competition or canonical harness score'
        row['junit_artifacts']=mgr.junit_captures;write(out/'NATIVE_RESULT.json',row)
        return row
    finally:
        mgr.cleanup_all()
        clean=not mgr.sandboxes and all(not Path(e['lease']).exists() for e in mgr.entries)
        write(out/'NATIVE_COMMANDS.json',mgr.command_records)
        write(out/'CLEANUP.json',dict(complete=clean,records=mgr.cleanup_records))
        assert clean,'NATIVE_CLEANUP_NOT_CONFIRMED'

async def cpu_admission(out):
    import torch
    assert torch.cuda.device_count()==0,'CPU_ADMISSION_REQUIRES_NO_GPU'
    from swegemma.harness.container_setup import extract_snapshot
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    issues=json.loads((HERE/'ISSUES.agent.json').read_bytes());trusted=json.loads((HERE/'TRUSTED_TEST_SPEC.private.json').read_bytes())
    compiled={}
    for name in ('R2','A'):
        cfg,agent=context_config(name,out/('compile-'+name),HERE/'unused',HERE/'ISSUES.agent.json',HERE/'assets/wheels')
        compiled[name]=dict(instruction_sha256=sha(agent.instruction.encode()),tools=[t.__name__ for t in agent.tools],generation=agent.generate_content_config.model_dump(mode='json',exclude_none=True),budget=str(cfg.budget))
    assert {k:v for k,v in compiled['R2'].items() if k!='instruction_sha256'}=={k:v for k,v in compiled['A'].items() if k!='instruction_sha256'}
    write(out/'COMPILE_RESULTS.json',compiled)
    rows=[]
    for issue in issues:
        ident=issue['instance_id'];directory=out/ident
        try:
            result=await native_verify(issue,next(t for t in trusted if t['instance_id']==ident),HERE/'assets/snapshots'/(ident+'.tgz'),HERE/'assets/wheels',directory)
            j=result.get('observed_junit',{})
            infra=result.get('infrastructure_controls',{})
            co_targets=infra.get('original_co_targets',{})
            admitted=result['resolved'] is False and result['test_exit_code']==1 and j.get('errors')==0 and j.get('original_target_failure') and infra.get('passed') and all(v and set(v)=={'failure'} for v in co_targets.values()) and (result.get('verification_source_guard') or {}).get('unchanged')
            rows.append(dict(task=ident,status='PASS' if admitted else 'NATIVE_ENV_OR_CONTROL_BLOCKED',resolved=result['resolved'],exit_code=result['test_exit_code'],junit_summary=j,infrastructure_controls=infra,error=result.get('error')))
        except BaseException as exc:
            import traceback
            rows.append(dict(task=ident,status='ENVIRONMENT_BLOCKED',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc()))
        write(out/'ADMISSION_RESULTS.json',dict(status='PASS' if len(rows)==4 and all(r['status']=='PASS' for r in rows) else 'CPU_INTEGRATION_BLOCKED',rows=rows,model_requests=0,GPU_allocated=0))
    return rows

if __name__=='__main__':
    import asyncio,sys
    asyncio.run(cpu_admission(sys.argv[1]))
