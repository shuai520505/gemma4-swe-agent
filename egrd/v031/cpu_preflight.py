"""Actual pinned Compiler/Runner on the real Django source; SCRIPTED_ONLY HTTP."""
import asyncio
import difflib
import importlib.metadata as md
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tarfile
import time
import zipfile

from .prepare import HERE,ROOT,S0_SHA,sha,write,arm_input


def fixture_actions(data):
    forbidden=str(data/'diagnostics/django__django-16333.py')
    canary="""from pathlib import Path
for value in ('/kaggle/input','/proc','/evaluation','/kaggle/working','/trusted-evidence'):
 assert not Path(value).exists(),value
link=Path('/workspace/owned-host-link')
link.symlink_to('/kaggle/input')
assert not link.exists()
link.unlink()
print('AGENT_FILESYSTEM_ISOLATION_PASS')
"""
    diagnostic="import django\nassert django.get_version().startswith('4.2')\nprint('SCRIPTED_RUNTIME_ASSERTION_PASS; not a repair diagnostic')\n"
    return [('get_status',{}),('read_file',dict(filepath='django/contrib/auth/forms.py',start_line=1,end_line=20)),
        ('read_file',dict(filepath=forbidden)),
        ('write_file',dict(filepath=forbidden,content='ATTEMPTED_AGENT_TAMPER_MUST_FAIL')),
        ('run_command',dict(command='python3 -c '+shlex.quote(canary))),
        ('write_file',dict(filepath='owned-cpu-diagnostic.py',content=diagnostic)),
        ('run_command',dict(command='python3 owned-cpu-diagnostic.py')),
        ('edit_file',dict(filepath='django/contrib/auth/forms.py',old_string='import unicodedata\n',
            new_string='import unicodedata\n# EGRD_SCRIPTED_ONLY_TRANSPORT_MARKER: inert engineering comment, no repair.\n')),
        ('run_command',dict(command='python3 owned-cpu-diagnostic.py && rm owned-cpu-diagnostic.py && git diff --check && git diff --stat')),
        ('submit_patch',{}),'End SCRIPTED_ONLY engineering fixture; no repair claim.']


async def session(arm,out,data,task,snapshot,wheels,regression):
    from adk_submission import ModelRegistry,compile_submission,validate_directory
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.config import EvalConfig,build_submission_limits
    from swegemma.models import Task
    from swegemma.context import SwegemmaContext
    from swegemma.harness.agent_runner import run_agent_sandbox
    from harness_v2.evidence import Journal
    from harness_v2.official import DurableContext
    from .sandbox_adapter import SubprocessManager
    from .scripted_boundary import ScriptedBoundary
    from .development_evaluator import evaluate
    out.mkdir(parents=True,exist_ok=False)
    directory=out/'candidate'
    package=ROOT/'candidates/s0/submission.zip';assert sha(package.read_bytes())==S0_SHA
    with zipfile.ZipFile(package) as z:z.extractall(directory)
    receipt=json.loads((HERE/'EVIDENCE_RECEIPT.json').read_bytes())
    original=json.loads((HERE/'private/original_task.json').read_bytes())
    actual=Task(instance_id=original['instance_id'],repo=original['repo'],base_commit=original['base_commit'],
        problem_statement=arm_input(original['problem_statement'],receipt,arm))
    assert not actual.test_patch and not actual.hints_text
    transport=ScriptedBoundary(fixture_actions(data)).start()
    manager=None;started=time.monotonic()
    try:
        registry=ModelRegistry();registry.register('gemma-4-31b-it-qat-w4a16-ct',LiteLlm(
            model='openai/gemma-4-31b-it-qat-w4a16-ct',api_base=transport.base_url,api_key='EMPTY'))
        limits,constraints=build_submission_limits();validate_directory(directory,limits=limits)
        compiled=compile_submission(directory,SwegemmaContext().create_tools(),registry,
            limits=limits,generation_constraints=constraints)
        assert compiled.instruction==(directory/'prompts/system.md').read_text()
        gen=compiled.generate_content_config.model_dump(mode='json',exclude_none=True)
        write(out/'COMPILED_CONFIGURATION.json',dict(generation=gen,instruction_sha256=sha(compiled.instruction.encode()),
            candidate_sha256=S0_SHA,seed=gen.get('seed'),include_thoughts=gen.get('thinking_config',{}).get('include_thoughts')))
        tools=[t.__name__ for t in compiled.tools]
        assert tools==['get_status','run_command','read_file','edit_file','write_file','submit_patch']
        assert not compiled.sub_agents
        journal=Journal(out/'agent')
        manager=SubprocessManager(journal=journal,base_dir=out/'agent/roots',task_wheels=wheels,timeout_seconds=120)
        cfg=EvalConfig(tasks_path=HERE/'private/original_task.json',snapshots_dir=snapshot.parent,
            results_dir=out/'harness',submission_dir=directory,models=registry,sandbox='subprocess',wheels_dir=wheels,
            max_time_minutes=5,max_tool_calls=60,timeout_seconds=120,verification_timeout_seconds=300,
            limits=limits,generation_constraints=constraints,enable_sandbox_testing=True,display_mode='quiet')
        context=DurableContext(journal=journal,docker_manager=manager,task=actual,budget=cfg.budget,harness=cfg.harness)
        manager.context=context
        patch,error,trace=await run_agent_sandbox(manager,cfg,actual,snapshot,context=context)
        write(out/'RUNNER_RETURN.json',dict(error=error,patch_bytes=len(patch.encode()),patch_submitted=context.patch_submitted,
            charged_tools=context.tool_calls_used,agent_seconds=context.agent_elapsed_seconds))
        assert error is None,(arm,error)
        assert context.patch_submitted and patch and 'EGRD_SCRIPTED_ONLY_TRANSPORT_MARKER' in patch
        assert 'owned-cpu-diagnostic' not in patch
        (out/'submitted.patch').write_bytes(patch.encode())
        events=[json.loads(l) for l in (out/'agent/adk_events.jsonl').read_bytes().splitlines()]
        responses=[p['function_response'] for e in events for p in e.get('event',{}).get('content',{}).get('parts',[]) if p.get('function_response')]
        assert set(tools)<={r['name'] for r in responses}
        assert any('AGENT_FILESYSTEM_ISOLATION_PASS' in json.dumps(r) for r in responses)
        failed_paths=[r for r in responses if r['name'] in ('read_file','write_file') and 'error' in json.dumps(r).lower()]
        assert len(failed_paths)>=2
        assert sha((data/task['diagnostic_path']).read_bytes())==task['diagnostic_sha256']
        write(out/'SCRIPTED_HTTP_REQUESTS.json',transport.calls)
        assert transport.calls
        for request in transport.calls:
            contents=json.dumps(request['messages'],ensure_ascii=False)
            assert original['problem_statement'] in '\n'.join(str(m.get('content','')) for m in request['messages'])
            assert ('<EGRD_DEVELOPMENT_OBSERVATION>' in contents)==(arm=='B')
            assert request.get('max_completion_tokens',request.get('max_tokens'))==gen['max_output_tokens']
            assert request['thinking_token_budget']==gen['thinking_config']['thinking_budget']
            assert request.get('seed')==gen.get('seed')
            assert (data/task['diagnostic_path']).read_text() not in contents
        manager.cleanup_all();assert not manager.sandboxes
        checked=evaluate(task,data,out/'trusted-postedit',snapshot,wheels,regression,patch)
        assert checked['patch_applicable'] and checked['original_failing_probe_still_fails']
        assert not checked['target_probe_passed'] and checked['bounded_regression']['exit_code']==0
        assert checked['trusted_probe_unchanged'] and checked['cleanup']
        checked['production_behavior_changed']=False  # Reviewed inert-comment-only fixture.
        write(out/'trusted-postedit/DEVELOPMENT_RESULT.json',checked)
        summary=dict(arm=arm,CPU_MODEL='SCRIPTED_ONLY',package_sha256=S0_SHA,full_compiler=True,
            generation=gen,compiled_tools=tools,instruction_sha256=sha(compiled.instruction.encode()),
            scripted_requests=len(transport.calls),real_Gemma_requests=0,
            actual_model_tokens=None,charged_tools=context.tool_calls_used,agent_seconds=context.agent_elapsed_seconds,
            worker_seconds=time.monotonic()-started,patch_submitted=context.patch_submitted,patch_sha256=sha(patch.encode()),
            synthetic_edit_kind='INERT_PRODUCTION_COMMENT_NOT_REPAIR',development_result=checked,
            official_native_resolved=None,canonical_swebench_resolved=None,
            agent_cleanup=not manager.sandboxes,path_read_write_attacks_denied=True,
            no_evaluator_content_in_requests=True,events_sha256=sha((out/'agent/adk_events.jsonl').read_bytes()))
        write(out/'SUMMARY.json',summary)
        return summary,transport.calls[0]
    finally:
        write(out/'SCRIPTED_HTTP_REQUESTS.json',transport.calls)
        if manager:manager.cleanup_all()
        transport.stop();write(out/'TRANSPORT_CLEANUP.json',dict(complete=transport.cleaned))


async def run(output):
    import torch
    assert torch.cuda.device_count()==0,'CPU-only authorization'
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    sdk={n:md.version(n) for n in ('swegemma','adk-submission','google-adk','adk-eval-core')}
    expected=json.loads((ROOT/'egrd/v023/RECOVERED_DEPENDENCY_IDENTITIES.json').read_bytes())
    assert sdk==expected['SDK']
    for member,digest in expected['installed_official_source_hashes'].items():
        dist=md.distribution('google-adk' if member.startswith('google/') else member.split('/')[0].replace('_','-'))
        assert sha(Path(dist.locate_file(member)).read_bytes())==digest,member
    manifest_digest=json.loads((ROOT/'egrd/v03/DATASET_BUILD_V1.json').read_bytes())['manifest_sha256']
    candidates=[p for p in Path('/kaggle/input').rglob('MANIFEST.json') if sha(p.read_bytes())==manifest_digest]
    assert len(candidates)==1;data=candidates[0].parent
    manifest=json.loads(candidates[0].read_bytes())
    for name,digest in manifest['files'].items():assert sha((data/name).read_bytes())==digest,name
    task=next(r for r in json.loads((data/'metadata/task_registry.json').read_bytes())['tasks'] if r['instance_id']=='django__django-16333')
    wheels=out/'task-wheels';wheels.mkdir()
    deps=json.loads((data/'environments/dependency_lock.json').read_bytes())
    for name in deps['groups']['django']:
        record=deps['packages'][name];path=data/'wheels'/record['filename']
        assert sha(path.read_bytes())==record['sha256'];(wheels/path.name).symlink_to(path)
    from egrd.v03.runtime import restore,tree_identity,cleanup
    restored=restore(data/task['snapshot_path'],out/'restored',task['archive_root'])
    lock=json.loads((HERE/'TASK_IDENTITY_LOCK.json').read_bytes())
    assert tree_identity(restored)==lock['source_tree_before']
    env=dict(os.environ,GIT_AUTHOR_NAME='Synthetic snapshot metadata',GIT_AUTHOR_EMAIL='cpu@example.invalid',
        GIT_COMMITTER_NAME='Synthetic snapshot metadata',GIT_COMMITTER_EMAIL='cpu@example.invalid',
        GIT_AUTHOR_DATE='2026-10-26T00:00:00+00:00',GIT_COMMITTER_DATE='2026-10-26T00:00:00+00:00')
    for args in (['init','-q'],['add','.'],['commit','-qm','Unmodified base content; synthetic research Git metadata']):
        subprocess.run(['git',*args],cwd=restored,env=env,check=True,capture_output=True)
    snapshot=out/'django-base-flat.tgz'
    with tarfile.open(snapshot,'w:gz') as t:
        for path in sorted(restored.iterdir()):t.add(path,arcname=path.name)
    cleanup(out/'restored',out)
    from .development_evaluator import evaluate
    regression=HERE/'private/regression.py'
    baseline=evaluate(task,data,out/'baseline',snapshot,wheels,regression)
    assert baseline['original_failing_probe_still_fails'] and baseline['positive_controls_passed']
    assert baseline['bounded_regression']['exit_code']==0 and baseline['cleanup']
    records=[];requests=[]
    for arm in ('A','B'):
        record,request=await session(arm,out/arm,data,task,snapshot,wheels,regression)
        records.append(record);requests.append(request)
    a,b=requests
    assert a['tools']==b['tools'] and records[0]['generation']==records[1]['generation']
    assert records[0]['instruction_sha256']==records[1]['instruction_sha256']
    original=json.loads((HERE/'private/original_task.json').read_bytes())['problem_statement']
    receipt=json.loads((HERE/'EVIDENCE_RECEIPT.json').read_bytes())
    suffix=arm_input(original,receipt,'B')[len(original):]
    fixed=json.loads(json.dumps(b));n=0
    for msg in fixed['messages']:
        if isinstance(msg.get('content'),str):n+=msg['content'].count(suffix);msg['content']=msg['content'].replace(suffix,'')
    assert n==1 and fixed==a,'Only the evidence supplement may differ at the first model request'
    full_diff='\n'.join(difflib.unified_diff(json.dumps(a,indent=2,ensure_ascii=False).splitlines(),
        json.dumps(b,indent=2,ensure_ascii=False).splitlines(),fromfile='A',tofile='B'))
    (out/'RENDERED_INPUT_DIFF.txt').write_text(full_diff,encoding='utf8')
    write(out/'INPUT_BOUNDARY_AUDIT.json',dict(only_B_has_receipt=True,original_issue_exact=True,
        instructions_equal=True,tools_equal=True,generation_equal=True,first_request_diff_sha256=sha(full_diff.encode()),
        supplement_bytes=len(suffix.encode()),token_overhead=None,tokenizer_replay='NOT_AVAILABLE',
        first_request_sha256={arm:sha(json.dumps(req,sort_keys=True).encode()) for arm,req in zip(('A','B'),requests)}))
    write(out/'CPU_TEST_RESULTS.json',dict(CPU_MODEL='SCRIPTED_ONLY',status='CPU_PREFLIGHT_PASS',SDK=sdk,
        baseline=baseline,records=records,real_Gemma_requests=0,model_weights_loaded=False,GPU=0,
        input_boundary_pass=True,original_task_identity_pass=True,source_snapshot_sha256=task['snapshot_sha256'],
        flattened_snapshot_sha256=sha(snapshot.read_bytes()),synthetic_Git_metadata=True,
        GPU_experiment_frozen=False,generation_discrepancy_requires_review=True))
    print('CPU_PREFLIGHT_PASS; SCRIPTED_ONLY; no real model outcome.',flush=True)


if __name__=='__main__':asyncio.run(run(sys.argv[1]))
