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
            probe="import os,socket,sys;from pathlib import Path;print(sys.version,sys.executable);assert os.getuid()!=0;assert not Path('/kaggle/input').exists() and not Path('/proc').exists();\ntry: socket.socket(socket.AF_INET,socket.SOCK_STREAM)\nexcept PermissionError: print('NONROOT_CHROOT_NETWORK_DENIED')\nelse: raise AssertionError('NETWORK_SOCKET_NOT_DENIED')"
            checked=self.exec(sid,'python3 -c '+shlex.quote(probe),timeout=10)
            write(self.journal.directory/('ISOLATION_'+sid+'.json'),asdict(checked))
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
        if (self.sandboxes[sid]['root']/'opt/python311').exists():
            command='export PATH=/opt/python311/bin:$PATH PYTHONHOME=/opt/python311 LD_LIBRARY_PATH=/opt/python311/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}; '+command
        if self.project_version:
            command='export SETUPTOOLS_SCM_PRETEND_VERSION='+shlex.quote(self.project_version)+'; '+command
        before=time.monotonic();res=super().exec(sid,command,timeout=timeout)
        self.command_records.append(dict(command=command,start=before,end=time.monotonic(),result=asdict(res)))
        if '--junitxml=' in command:
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
        if mgr.junit_captures:row['observed_junit']=nodes_summary(Path(mgr.junit_captures[-1]['path']).read_text(),task)
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
            admitted=result['resolved'] is False and result['test_exit_code']==1 and j.get('errors')==0 and j.get('original_target_failure') and j.get('positive_controls_passed')
            rows.append(dict(task=ident,status='PASS' if admitted else 'NATIVE_ENV_OR_CONTROL_BLOCKED',resolved=result['resolved'],exit_code=result['test_exit_code'],junit_summary=j,error=result.get('error')))
        except BaseException as exc:
            import traceback
            rows.append(dict(task=ident,status='ENVIRONMENT_BLOCKED',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc()))
        write(out/'ADMISSION_RESULTS.json',dict(status='PASS' if len(rows)==4 and all(r['status']=='PASS' for r in rows) else 'CPU_INTEGRATION_BLOCKED',rows=rows,model_requests=0,GPU_allocated=0))
    return rows

if __name__=='__main__':
    import asyncio,sys
    asyncio.run(cpu_admission(sys.argv[1]))
