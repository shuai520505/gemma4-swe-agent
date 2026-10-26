"""Exact N/D packages through the full pinned SDK, with SCRIPTED_ONLY actions.

No candidate rewrite, Compiler replacement, callback injection or model weights.
The existing accepted chroot adapter is a research sandbox, not a submitted hook.
"""
import asyncio
import hashlib
import importlib.metadata as md
import inspect
import json
from pathlib import Path
import platform
import shlex
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HASHES = dict(N='c0618f4a996883600b1353a7a7e5fe0d8588f4393613984f30f725b4cfa98e69',
              D='253002dcea2f077945aebacee3c9ea3a6033601aedcf4b55964d99fe8b5b09d7')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str)+'\n', encoding='utf8')


def actions():
    probes = {
        'target': 'from fastapi.owned import accepts\nassert accepts(0)\nassert accepts(3)\nassert not accepts(-1)\n',
        'vacuous': 'print("no assertions")\n',
        'dependency': 'import meer_owned_dependency_that_does_not_exist\nassert True\n',
        'malformed': 'def broken(:\n',
        'exception': 'raise ValueError("owned non-target exception")\n',
        'timeout': 'import time\ntime.sleep(10)\nassert time.monotonic() > 0\n',
        'large': 'print("x"*200000)\nx=1\nassert x == 1\n',
    }
    setup = 'from pathlib import Path\n'+'\n'.join(
        f'Path("/tmp/egrd_{name}.py").write_text({body!r})' for name, body in probes.items())
    call = lambda name, **extra: ('run_skill_script', dict(skill_name='meer-evidence',
        file_path='scripts/verify.py', args=dict(check=f'/tmp/egrd_{name}.py', seconds='1', **extra)))
    bad = 'def accepts(value):\n    return value > 0\n'
    return [
        ('get_status', {}), ('read_file', dict(filepath='fastapi/owned.py')),
        ('write_file', dict(filepath='owned-scratch.txt', content='synthetic CPU fixture')),
        ('run_command', dict(command='python3 -c '+shlex.quote(setup))),
        # These actual official tool errors must be returned, not crash the Agent.
        ('run_skill_script', {}),
        ('run_skill_script', dict(skill_name='meer-evidence', file_path='scripts/absent.py')),
        ('run_skill_script', dict(skill_name='meer-evidence', file_path='scripts/verify.py', args={})),
        call('absent'), call('target', workspace='/absent-workspace'),
        call('vacuous'), call('dependency'), call('malformed'), call('exception'),
        call('timeout'), call('large'), call('target'),
        ('edit_file', dict(filepath='fastapi/owned.py', old_string=bad,
                           new_string=bad.replace('> 0', '>= 0'))),
        call('target'), call('target'),
        ('run_command', dict(command='python3 checks.py && rm owned-scratch.txt && git diff --check && git diff')),
        ('submit_patch', {}), 'End.'
    ]


async def session(arm, out, data):
    from adk_submission import ModelRegistry, compile_submission, validate_directory
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.config import EvalConfig, build_submission_limits
    from swegemma.context import SwegemmaContext
    from swegemma.models import Task, load_tasks
    from swegemma.harness.verification import verify_task
    from harness_v2.evidence import Journal
    from u_re.v01.experiments.action_priority_01.integrated_cpu_01 import agent_phase
    from s1.verifier_v3.environment import SubprocessManager as Trusted, research_environment
    from meer.v01.cpu_acceptance import transport

    out.mkdir(parents=True, exist_ok=False)
    package = ROOT / f'egrd/v022/submission_{arm}.zip'
    assert sha(package.read_bytes()) == HASHES[arm]
    directory = out/'candidate'
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
        assert all(not n.startswith('/') and '..' not in Path(n).parts for n in archive.namelist())
        archive.extractall(directory)
    t = transport(actions()).start(data, out)
    trusted = None
    try:
        registry = ModelRegistry()
        registry.register('gemma-4-31b-it-qat-w4a16-ct', LiteLlm(
            model='openai/gemma-4-31b-it-qat-w4a16-ct', api_base=t.base_url, api_key='EMPTY'))
        limits, constraints = build_submission_limits()
        validate_directory(directory, limits=limits)
        native_tools = SwegemmaContext().create_tools()
        agent = compile_submission(directory, native_tools, registry,
                                   limits=limits, generation_constraints=constraints)
        expected = (directory/'prompts/system.md').read_text(encoding='utf8')
        assert agent.instruction == expected and not agent.sub_agents
        gen = agent.generate_content_config.model_dump(mode='json', exclude_none=True)
        assert gen == dict(max_output_tokens=16384, seed=17, thinking_config=dict(thinking_budget=4096))
        entries = [getattr(tool, '__name__', type(tool).__name__) for tool in agent.tools]
        assert 'SkillToolset' in entries
        cfg = EvalConfig(tasks_path=t.data/'tasks.jsonl', snapshots_dir=t.data/'snapshots',
            results_dir=out/'harness', submission_dir=directory, models=registry, sandbox='subprocess',
            wheels_dir=data/'wheels', max_time_minutes=5, max_tool_calls=60, timeout_seconds=120,
            verification_timeout_seconds=300, limits=limits, generation_constraints=constraints,
            enable_sandbox_testing=True, display_mode='quiet')
        original = load_tasks(t.data/'tasks.jsonl')[0]
        task = Task(instance_id=original.instance_id, repo=original.repo, base_commit=original.base_commit,
                    problem_statement=original.problem_statement)
        assert not task.test_patch
        started = time.perf_counter()
        # Unmodified official Runner compiles the same candidate with its sandbox executor.
        patch, error, context = await agent_phase.run(cfg, task,
            t.data/'snapshots/ure_gpu03_owned.tgz', out/'agent')
        assert error is None and context.patch_submitted and patch
        (out/'final.patch').write_text(patch, encoding='utf8')
        native = out/'verifier'; native.mkdir()
        trusted = Trusted(journal=Journal(native), base_dir=native/'roots', audit_modules=['fastapi'],
                          task_wheels=data/'wheels', timeout_seconds=120)
        trusted.agent_id = 'TRUSTED_EVALUATOR_NO_AGENT'
        try:
            with research_environment(audit_modules=['fastapi'], task_wheels=data/'wheels'):
                result = await verify_task(trusted, cfg, original, t.data/'snapshots/ure_gpu03_owned.tgz',
                                          agent_patch=patch, start_time=started)
            write(out/'TaskResult.json', result.model_dump(mode='json', exclude={'trace'}))
        finally:
            trusted.cleanup_all()
        junit = native/'phase2.junit.xml'; xml = ET.parse(junit).getroot()
        assert result.resolved and not list(xml.iter('failure')) and not list(xml.iter('error'))
        events = [json.loads(line) for line in (out/'agent/adk_events.jsonl').read_bytes().splitlines()]
        responses = [p['function_response'] for e in events
            for p in e.get('event', {}).get('content', {}).get('parts', []) if p.get('function_response')]
        names = [r['name'] for r in responses]
        assert {'get_status','read_file','write_file','edit_file','run_command','submit_patch'} <= set(names)
        assert not set(names) & {'list_skills', 'load_skill', 'load_skill_resource'}
        scripts = [r['response'] for r in responses if r['name'] == 'run_skill_script']
        assert len(scripts) == 14, len(scripts)
        assert scripts[0]['error_code'] == 'INVALID_ARGUMENTS'
        assert scripts[1]['error_code'] == 'SCRIPT_NOT_FOUND'
        reports = [json.loads(r['stdout']) for r in scripts[3:]]
        expected_verdicts = ['UNKNOWN','UNKNOWN','UNKNOWN','CONTRADICTED','CONTRADICTED',
                             'CONTRADICTED','UNKNOWN','SUPPORTED','CONTRADICTED','SUPPORTED','OBSERVED']
        assert [r['verdict'] for r in reports] == expected_verdicts, reports
        assert reports[6]['timed_out']
        assert len(scripts[10]['stdout']) < 4096  # Compact receipt, not a raw-disk size guarantee.
        assert reports[-3]['source_sha256'] != reports[-2]['source_sha256']
        assert reports[-1]['subprocess_invocations'] == 0
        assert all(r['native_resolved'] is None and r['semantic_correctness']=='UNKNOWN' for r in reports)
        cleanup = json.loads((out/'agent/cleanup.json').read_bytes())
        assert cleanup['complete']
        for request in t.calls:
            system = '\n'.join(str(m.get('content','')) for m in request['messages'] if m.get('role')=='system')
            assert expected.strip() in system
            assert request.get('max_completion_tokens', request.get('max_tokens')) == 16384
            assert request['thinking_token_budget'] == 4096 and request['seed'] == 17
        write(out/'SCRIPTED_HTTP_REQUESTS.json', t.calls)  # Private archive only.
        summary = dict(arm=arm, full_compiler=True, empty_state_compile=True,
            package_sha256=HASHES[arm], instruction_sha256=sha(expected.encode()), generation=gen,
            compiled_tool_entries=entries, actual_tool_names=sorted(set(names)), direct_without_list_load=True,
            skill_responses=len(scripts), scripted_HTTP_requests=len(t.calls), CPU_MODEL='SCRIPTED_ONLY',
            charged_tools=context.tool_calls_used, synthetic_native_resolved=result.resolved,
            TaskResult_sha256=sha((out/'TaskResult.json').read_bytes()), JUnit_sha256=sha(junit.read_bytes()),
            patch_sha256=sha(patch.encode()), explicit_submit=context.patch_submitted,
            cleanup=cleanup, local_receipts=reports, worker_seconds=time.perf_counter()-started,
            actual_Gemma_requests=0, research_sandbox_adapter='inherited_chroot',
            adoption_or_real_repair_efficacy='NOT_MEASURED')
        write(out/'SUMMARY.json', summary)
        return summary
    finally:
        if trusted: trusted.cleanup_all()
        t.stop()
        write(out/'TRANSPORT_CLEANUP.json', dict(complete=t.cleaned))


async def run(output):
    import torch
    assert torch.cuda.device_count() == 0, 'CPU-only authorization'
    from meer.v01.cpu_acceptance import source_audit
    from s1.task_identity import find_data
    out = Path(output); out.mkdir(parents=True, exist_ok=False)
    sdk = {name: md.version(name) for name in ('swegemma','adk-submission','google-adk','adk-eval-core')}
    assert sdk == {'swegemma':'0.2.11','adk-submission':'0.2.13','google-adk':'1.36.1','adk-eval-core':'0.1.0'}
    pins=json.loads((ROOT/'meer/v01/OFFICIAL_SOURCE_PINS.json').read_bytes())
    member_checks={}
    for wheel,pin in pins.items():
        if not wheel.endswith('.whl'):continue
        distribution=md.distribution(wheel.split('-')[0].replace('_','-'))
        for member,record in pin.get('members',{}).items():
            digest=sha(Path(distribution.locate_file(member)).read_bytes())
            assert digest==record['sha256'],member
            member_checks[member]=digest
    write(out/'INSTALLED_OFFICIAL_MEMBER_HASHES.json',member_checks)
    write(out/'ENVIRONMENT.json', dict(sdk=sdk, Python=platform.python_version(), GPU_count=0,
        CUDA_visible_devices=__import__('os').environ.get('CUDA_VISIBLE_DEVICES'), CPU_MODEL='SCRIPTED_ONLY',
        installed_distributions=sorted((d.metadata['Name'], d.version) for d in md.distributions())))
    write(out/'OFFICIAL_SOURCE_AUDIT.json', source_audit())
    records=[]
    for arm in ('N','D'): records.append(await session(arm, out/arm, find_data()))
    assert records[0]['generation'] == records[1]['generation']
    write(out/'CPU_TEST_RESULTS.json', dict(status='COMPILER_FULL_PASS', records=records,
        GPU_count=0, real_Gemma_requests=0, CPU_MODEL='SCRIPTED_ONLY', new_independent_tasks=0))


if __name__ == '__main__':
    asyncio.run(run(sys.argv[1]))
