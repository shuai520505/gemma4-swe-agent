"""Validate with official competition packages; never perform model inference."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile
import yaml

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'gemma-4-31b-it-qat-w4a16-ct'
TOOLS = ['get_status', 'run_command', 'read_file', 'edit_file', 'write_file', 'submit_patch']
MEMBERS = ['agent.yaml', 'eval_config.yaml', 'prompts/system.md']


def load(path):
    from adk_submission.yaml_loader import load_yaml
    path = Path(path).resolve()
    data = load_yaml(path, path.parent)
    if not isinstance(data, dict):
        raise ValueError('agent configuration must be a mapping')
    return data


def validate(directory):
    directory = Path(directory)
    for path in directory.rglob('*'):
        if path.is_symlink():
            raise ValueError('symlinks are forbidden in the submission')
        if path.is_file() and path.relative_to(directory).as_posix() not in MEMBERS:
            raise ValueError(f'unexpected submission file: {path.name}')
    config = load(directory / 'agent.yaml')
    prompt = (directory / 'prompts/system.md').read_text(encoding='utf-8')
    allowed = {'agent_class', 'name', 'model', 'description', 'instruction', 'tools'}
    if set(config) - allowed:
        raise ValueError('unexpected configuration fields')
    if config.get('agent_class') != 'LlmAgent' or config.get('model') != MODEL:
        raise ValueError('must use a single LlmAgent with the required Gemma model')
    if config.get('instruction') != prompt or not prompt.strip():
        raise ValueError('instruction must resolve to prompts/system.md')
    if config.get('tools') != TOOLS:
        raise ValueError('V0 requires exactly the reviewed official tool set')
    evaluation = yaml.safe_load((directory / 'eval_config.yaml').read_text())
    expected = dict(timeout_seconds=300, verification_timeout_seconds=300,
                    max_tool_calls=100, max_time_minutes=60.0)
    if evaluation != {'evaluation': expected}:
        raise ValueError('unexpected evaluation defaults')
    return config


def compile_adk(directory):
    from adk_submission import ModelRegistry, compile_submission, validate_directory
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.config import build_submission_limits
    from swegemma.context import SwegemmaContext
    validate(directory)
    # Real organizer tool factories, without executing commands or any model.
    tools = SwegemmaContext().create_tools()
    if not set(TOOLS).issubset(tools):
        raise ValueError('official Harness registry lacks required tools')
    models = ModelRegistry()
    model = LiteLlm(model=f'openai/{MODEL}', api_base='http://127.0.0.1:8000/v1', api_key='EMPTY')
    models.register(MODEL, model)
    limits, constraints = build_submission_limits()
    validate_directory(directory, limits=limits)
    agent = compile_submission(directory, tools, models,
                               limits=limits, generation_constraints=constraints)
    if agent.model.model != f'openai/{MODEL}' or agent.sub_agents:
        raise ValueError('compiled agent model or architecture mismatch')
    if [tool.__name__ for tool in agent.tools] != TOOLS:
        raise ValueError('compiled tool bindings mismatch')
    return agent


def build(directory, output):
    validate(directory)
    directory, output = Path(directory), Path(output)
    if output.resolve().is_relative_to(directory.resolve()):
        raise ValueError('archive output must be outside submission directory')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in MEMBERS:
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (directory / name).read_bytes())
    return hashlib.sha256(output.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'compile', 'build'])
    parser.add_argument('--submission', type=Path, default=ROOT / 'submission')
    parser.add_argument('--output', type=Path, default=ROOT / 'submission.zip')
    args = parser.parse_args()
    config = validate(args.submission)
    if args.action in {'compile', 'build'}:
        compile_adk(args.submission)
    result = {'action': args.action, 'model': config['model'],
              'tool_count': len(config['tools']),
              'official_compiler_verified': args.action in {'compile', 'build'},
              'harness_inference_verified': False}
    if args.action == 'build':
        result['sha256'] = build(args.submission, args.output)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
