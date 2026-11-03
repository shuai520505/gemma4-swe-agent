"""Prospective host adapter; frozen packages and prior execution bytes untouched."""
import json,shlex
from dataclasses import asdict
from pathlib import Path
from r2a_runtime import SubprocessManager as FrozenManager,write,sha
from harness_v2.official import DurableContext as FrozenContext
from stop_policy import StopLatch,InfrastructureStop

class SubprocessManager(FrozenManager):
    # Official SDK dispatch requires this literal class name.
    def start(self):
        sid=super().start()
        try:
            if getattr(getattr(getattr(self,'context',None),'task',None),'repo',None)=='sphinx-doc/sphinx':
                p=self.sandboxes[sid]['root']/'usr/local/bin/sphinx-build'
                assert not p.exists() and not p.is_symlink(),'Unexpected preexisting CLI'
                p.write_text("#!/usr/bin/python3\nimport sys\nsys.path.insert(0, '/workspace')\nfrom sphinx.cmd.build import main\nraise SystemExit(main())\n")
                p.chmod(0o755)
                write(self.journal.directory/('CLI_BINDING_'+sid+'.json'),dict(path='/usr/local/bin/sphinx-build',sha256=sha(p.read_bytes()),target='sphinx.cmd.build.main from /workspace',task_source_modified=False))
            return sid
        except BaseException as exc:
            ctx=getattr(self,'context',None)
            if hasattr(ctx,'infrastructure_latch'):
                ctx.infrastructure_latch.evidence=dict(reason='SANDBOX_SETUP_FAILED',error_type=type(exc).__name__)
                write(self.journal.directory/'INFRASTRUCTURE_STOP.json',ctx.stop_receipt())
            self.stop(sid);raise
    def exec(self,sid,command,*,timeout=None):
        # Portable libc locale, Python UTF-8 mode; applies equally to both arms
        # and all sandbox commands, including initial SDK source preparation.
        return super().exec(sid,'export LC_ALL=C LANG=C LANGUAGE=C PYTHONUTF8=1; '+command,timeout=timeout)
    def admit_source(self,sid):
        assert self.context.llm_calls_used==0,'Admission must precede first model request'
        commands=["python3 -c "+shlex.quote("import locale,os;assert locale.setlocale(locale.LC_ALL,'')=='C';assert os.getuid()!=0;print('LOCALE_NONROOT_PASS')")]
        if self.context.task.repo=='sphinx-doc/sphinx':
            commands+=['command -v sphinx-build && sphinx-build --version',
              "python3 -c "+shlex.quote("import sphinx;assert sphinx.__file__.startswith('/workspace/sphinx/');print(sphinx.__file__)")]
            # Generic CLI capability, not the benchmark Issue or its answer.
            commands += ["mkdir -p /tmp/infra-smoke/docs; printf 'project = \"infra-smoke\"\\n' > /tmp/infra-smoke/docs/conf.py; printf 'Infrastructure smoke\\n====================\\n\\nPlain text.\\n' > /tmp/infra-smoke/docs/index.rst; sphinx-build -q -b html /tmp/infra-smoke/docs /tmp/infra-smoke/html && test -s /tmp/infra-smoke/html/index.html"]
        rows=[]
        for command in commands:
            result=self.exec(sid,command,timeout=60);rows.append(dict(command=command,result=asdict(result)))
            if result.exit_code:
                write(self.journal.directory/'SOURCE_CLI_ADMISSION.json',dict(status='FAIL',rows=rows))
                raise InfrastructureStop('SOURCE_CLI_ADMISSION_FAILED')
        write(self.journal.directory/'SOURCE_CLI_ADMISSION.json',dict(status='PASS',rows=rows,SDK_llm_calls_before_admission=self.context.llm_calls_used,scope='Locale/nonroot and source CLI generic HTML smoke, not Issue fix validation'))

class DurableContext(FrozenContext):
    def __init__(self,**kwargs):
        self.infrastructure_latch=StopLatch();super().__init__(**kwargs)
        write(self.journal.directory/'INFRASTRUCTURE_STOP.json',self.stop_receipt())
    def start_agent_session(self):
        # SDK calls this after snapshot/dependency/baseline preparation and
        # immediately before requesting the first Agent completion.
        try:self.docker.admit_source(self.container_id)
        except InfrastructureStop:
            self.infrastructure_latch.evidence=dict(reason='SOURCE_CLI_ADMISSION_FAILED')
            write(self.journal.directory/'INFRASTRUCTURE_STOP.json',self.stop_receipt());raise
        super().start_agent_session()
    def handle_adk_event(self,event,agent_name=None):
        super().handle_adk_event(event,agent_name=agent_name)
        data=event.model_dump(mode='json',exclude_none=True)
        for part in (data.get('content') or {}).get('parts',[]):
            response=part.get('function_response')
            if response and self.infrastructure_latch.observe(response):
                write(self.journal.directory/'INFRASTRUCTURE_STOP.json',self.stop_receipt())
        self.infrastructure_latch.require_running()
    def stop_receipt(self):
        return dict(coverage='LIVE_ADK_TOOL_RESPONSES_V1',stopped=self.infrastructure_latch.evidence is not None,evidence=self.infrastructure_latch.evidence)
