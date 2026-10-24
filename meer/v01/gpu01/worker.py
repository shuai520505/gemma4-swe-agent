"""Minimal research compatibility adapter around the proven official worker.

No official tool, Compiler, Runner, Guard or native verification is replaced.
Only the old research six-entry validator and frozen result reader are adapted.
"""
import asyncio
import inspect
import json
from pathlib import Path
import sys
from unittest.mock import patch


def validate_compiled(agent, config):
    from google.adk.tools.skill_toolset import SkillToolset
    from s1 import MODEL, TOOLS
    normal = [t for t in agent.tools if not isinstance(t, SkillToolset)]
    skills = [t for t in agent.tools if isinstance(t, SkillToolset)]
    names = [getattr(t, '__name__', getattr(t, 'name', None)) for t in normal]
    if len(normal) != 6 or set(names) != set(TOOLS) or len(skills) > 1 or agent.sub_agents:
        raise ValueError('Exactly six official tools and at most one official SkillToolset required')
    cfg = agent.generate_content_config
    if (cfg.max_output_tokens != config.output_tokens or
            cfg.thinking_config.thinking_budget != config.thinking_budget or
            cfg.thinking_config.include_thoughts != config.include_thoughts or cfg.seed != config.seed):
        raise ValueError('Compiled generation drift')
    if MODEL not in agent.model.model:
        raise ValueError('Model drift')
    return cfg


def verify_candidate(spec):
    import hashlib
    lock = json.loads((Path(__file__).parents[1] / 'CANDIDATE_MANIFEST.json').read_bytes())
    arm = spec['arm']; directory = Path(spec['agent_dir'])
    expected = lock['arms'][arm]
    files = {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in directory.rglob('*') if p.is_file()}
    if files != expected['members'] or any(p.is_symlink() for p in directory.rglob('*')):
        raise ValueError('Frozen candidate member mismatch')
    return expected


async def evaluate(spec, directory):
    verify_candidate(spec)
    mode = spec.get('execution_mode', 'GPU')
    if mode not in ('GPU', 'CPU_VALIDATION'):
        raise ValueError('Unknown execution mode')
    expected = 'REAL_GEMMA' if mode == 'GPU' else 'CPU_SCRIPTED_ONLY'
    if spec.get('model_transport') != expected:
        raise ValueError('GPU route must reject scripted transport')
    from u_re.v01.experiments.action_priority_01.real_gemma_abba01 import worker as original
    from u_re.v01.experiments.action_priority_01.real_gemma_abba03 import worker as transport
    source = inspect.getsource(original.evaluate)
    replacements = {
        'from s1.config import Config,validate_compiled':
        'from s1.config import Config\n    from meer.v01.gpu01.worker import validate_compiled',
        'from s1.verifier_v3.audit import audit_verifier':
        'from u_re.v02.experiments.env_recovery_admission_01.junit_audit import audit_verifier',
    }
    for before, after in replacements.items():
        if source.count(before) != 1:
            raise ValueError('Accepted worker source anchor drift')
        source = source.replace(before, after)
    namespace = dict(original.__dict__)
    exec(compile(source, '<MEER-research-validator-and-frozen-reader>', 'exec'), namespace)
    # GPU03's passive HTTP fix preserves exclusive Agent directory creation.
    with patch.object(transport, '_evaluate', namespace['evaluate']):
        return await transport.evaluate(spec, directory)


if __name__ == '__main__':
    from harness_v2.evidence import atomic_json
    import traceback
    directory = Path(sys.argv[2]); directory.mkdir(parents=True, exist_ok=True)
    try:
        asyncio.run(evaluate(json.loads(Path(sys.argv[1]).read_bytes()), directory))
    except BaseException as exc:
        atomic_json(directory / 'worker_exception.json', dict(type=type(exc).__name__,
                    error=str(exc), traceback=traceback.format_exc()))
        raise
