"""Real official Compiler/ADK/six-tool acceptance, synthetic HTTP only."""
import asyncio
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch


async def run(output):
    from adk_submission import ModelRegistry, compile_submission
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.context import SwegemmaContext
    from swegemma.config import EvalConfig, build_submission_limits
    from harness_v2.evidence import atomic_json, read_events
    from s1.config import Config, validate_compiled
    from u_re.v01 import runner_cases as cases
    from .build import HERE, BASE, frozen, sha
    import torch
    assert sys.platform == 'linux' and torch.cuda.device_count() == 0
    originals = frozen()
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    block = (HERE/'ACTION_FIRST_INSTRUCTION_BLOCK.md').read_text(encoding='utf-8').strip()
    expected = json.loads((HERE/'CANDIDATE_AUDIT.json').read_text(encoding='utf-8'))
    assert sha((HERE/'submission_action_v01.zip').read_bytes()) == expected['zip_sha256']
    compiled = {}; runs = []
    models = ModelRegistry()
    models.register('gemma-4-31b-it-qat-w4a16-ct', LiteLlm(
        model='openai/gemma-4-31b-it-qat-w4a16-ct', api_base='http://127.0.0.1:8000/v1', api_key='EMPTY'))
    limits, constraints = build_submission_limits()
    paths = {'noegv': BASE/'candidate_noegv', 'action_v01': HERE/'candidate_action_v01'}
    for arm, directory in paths.items():
        agent = compile_submission(directory, SwegemmaContext().create_tools(), models,
            limits=limits, generation_constraints=constraints)
        validate_compiled(agent, Config())
        assert agent.instruction == (directory/'prompts/system.md').read_text(encoding='utf-8')
        cfg = EvalConfig(tasks_path=output/'unused', snapshots_dir=output, results_dir=output/'unused-results',
            submission_dir=directory, models=models, max_time_minutes=5.0, max_tool_calls=60, timeout_seconds=120)
        assert (cfg.budget.time_minutes*60, cfg.budget.tool_calls, cfg.harness.command_timeout_seconds) == (300,60,120)
        compiled[arm] = dict(real_official_Compiler=True, real_ADK_agent=True, tool_count=len(agent.tools),
            agent_count=1, instruction_sha256=sha(agent.instruction.encode()), budget=[300,60,120])
    original_plan = cases.plan
    def six_tools(case):
        actions = original_plan('basic')
        actions.insert(2, cases.call('write_file', filepath='owned-scratch.txt', content='Owned CPU fixture'))
        actions.insert(-3, cases.call('run_command', command='rm owned-scratch.txt && git diff --check'))
        return actions
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for arm, source in paths.items(): shutil.copytree(source, root/('candidate_'+arm))
        with patch.object(cases, 'HERE', root), patch.object(cases, 'plan', six_tools):
            for arm in paths:
                directory = output/arm
                result = await cases.exercise(arm, 'basic', directory)
                assert result['successful_edits'] == result['successful_submits'] == 1
                assert result['HTTP_audit']['passed'] and not result['tools_after_first_successful_submit']
                assert json.loads((directory/'cleanup.json').read_text())['complete']
                snapshots = read_events(directory/'request_snapshots.jsonl')
                systems = ['\n'.join(m['content'] for m in r['body']['messages'] if m['role']=='system') for r in snapshots]
                prompt = (paths[arm]/'prompts/system.md').read_text(encoding='utf-8').strip()
                assert systems and all(prompt in s for s in systems)
                assert all((block in s) == (arm=='action_v01') for s in systems)
                events = read_events(directory/'adk_events.jsonl')
                actual = {p['function_response']['name'] for r in events for p in
                    r.get('event',{}).get('content',{}).get('parts',[]) if p.get('function_response')}
                assert actual == {'get_status','run_command','read_file','edit_file','write_file','submit_patch'}
                for wire in result['wire_configuration']:
                    assert (wire['output'],wire['thinking'],wire['seed'],wire['sampling']) == (16384,4096,17,{})
                assert b'owned-scratch.txt' not in (directory/'returned.patch').read_bytes()
                runs.append(dict(arm=arm,passed=True,real_tools=sorted(actual),new_block_visible=arm=='action_v01',
                    tools_after_submit=0,successful_submits=1,cleanup=True))
    import importlib.metadata
    atomic_json(output/'CPU_GATE.json', dict(passed=True,compiled=compiled,cases=runs,
        versions={n:importlib.metadata.version(n) for n in ('swegemma','adk-submission','google-adk','litellm')},
        real_official_Runner=True,scripted_HTTP_model=True,Gemma_inference=False,GPU=False,
        actual300_second_boundary_rerun=False,algorithm_validated=False))
    print('ACTION_FIRST_OFFICIAL_CPU_PASS',flush=True)


if __name__ == '__main__': asyncio.run(run(sys.argv[1]))
