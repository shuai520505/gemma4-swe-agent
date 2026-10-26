"""Read hash-pinned source and execute isolated interface fragments, never a Runner.

The source-fragment tests use explicit test doubles for external dependencies.
They are not full ADK compilation, an Agent implementation or a deployable hook.
Private wheel contents and historical trajectory bodies are not exported.
"""
import ast
import copy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys
import types
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WHEELS = ROOT.parent / 'gemma4-swe-agent/artifacts/harness-v2/official-wheels'
BASE = '31511563da988634825d8148da1d2f0624303f03'
SELECTION = {
    'adk_submission-0.2.13-py3-none-any.whl': [
        'adk_submission/compiler.py', 'adk_submission/schema.py',
        'adk_submission/errors.py', 'adk_submission/paths.py',
        'adk_submission/registry.py', 'adk_submission/context.py', 'adk_submission/limits.py',
        'adk_submission/builders/llm.py', 'adk_submission/builders/workflows.py',
        'adk_submission/builders/sub_agents.py',
        'adk_submission/resolvers/callbacks.py', 'adk_submission/resolvers/tools.py',
        'adk_submission/resolvers/generation.py'],
    'google_adk-1.36.1-py3-none-any.whl': [
        'google/adk/agents/sequential_agent.py', 'google/adk/agents/loop_agent.py',
        'google/adk/agents/parallel_agent.py', 'google/adk/agents/llm_agent.py',
        'google/adk/flows/llm_flows/contents.py',
        'google/adk/flows/llm_flows/instructions.py',
        'google/adk/tools/skill_toolset.py', 'google/adk/apps/app.py'],
    'swegemma-0.2.11-py3-none-any.whl': [
        'swegemma/config.py', 'swegemma/harness/agent_runner.py',
        'swegemma/context.py', 'swegemma/submission.py', 'swegemma/sandbox/base.py'],
    'adk_eval_core-0.1.0-py3-none-any.whl': ['adk_eval_core/sandbox/base.py'],
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@lru_cache(maxsize=1)
def pinned_sources():
    pins = json.loads((ROOT / 'meer/v01/OFFICIAL_SOURCE_PINS.json').read_bytes())
    sources, records = {}, {}
    for filename, members in SELECTION.items():
        raw = (WHEELS / filename).read_bytes()
        if sha(raw) != pins[filename]['sha256']:
            raise ValueError('Pinned official wheel changed: ' + filename)
        with zipfile.ZipFile(WHEELS / filename) as wheel:
            if wheel.testzip() is not None:
                raise ValueError('Wheel CRC failure: ' + filename)
            member_records = {}
            for member in members:
                body = wheel.read(member)
                old = pins[filename].get('members', {}).get(member)
                if old and sha(body) != old['sha256']:
                    raise ValueError('Pinned source member changed: ' + member)
                sources[member] = body
                symbols = {}
                for node in ast.walk(ast.parse(body)):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        symbols.setdefault(node.name, []).append([node.lineno, node.end_lineno])
                member_records[member] = dict(sha256=sha(body), lines=len(body.splitlines()), symbols=symbols)
        records[filename] = dict(sha256=sha(raw), members=member_records)
    return sources, records


def node_at(member, qualified_name):
    node = ast.parse(pinned_sources()[0][member])
    for name in qualified_name.split('.'):
        matches = [n for n in node.body if isinstance(
            n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name]
        if not matches:
            matches = [n for n in ast.walk(node) if isinstance(
                n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name]
        if len(matches) != 1:
            raise ValueError('Ambiguous or missing source symbol: ' + qualified_name)
        node = matches[0]
    return node


def fragment(member, qualified_name, namespace=None):
    """Exact function/method body, in a fresh test namespace; no SDK patching."""
    node = copy.deepcopy(node_at(member, qualified_name))
    node.decorator_list = []  # SDK decorators do not alter the tested body.
    tree = ast.Module(body=[ast.ImportFrom(module='__future__',
        names=[ast.alias(name='annotations')], level=0), node], type_ignores=[])
    ast.fix_missing_locations(tree)
    scope = dict(namespace or {})
    exec(compile(tree, member + ':' + qualified_name, 'exec'), scope)
    return scope[node.name]


@lru_cache(maxsize=1)
def schema_modules():
    """Execute complete pure official schema/registry modules with local Pydantic.

    A private package prefix keeps official ADK/Runner modules untouched. No
    competitor imports, factory injection or patched Google module is installed.
    """
    prefix = '_egrd_v021_schema_test'
    package = types.ModuleType(prefix)
    package.__path__ = []
    sys.modules[prefix] = package
    result = {}
    for name in ('errors', 'paths', 'schema', 'registry', 'limits'):
        member = 'adk_submission/' + name + '.py'
        module = types.ModuleType(prefix + '.' + name)
        module.__package__ = prefix
        module.__file__ = member
        sys.modules[module.__name__] = module
        exec(compile(pinned_sources()[0][member], member, 'exec'), module.__dict__)
        result[name] = module
    return result


def historical_bypass():
    """Recheck original scripted CPU03 records; never rerun its Agent/evaluator."""
    prior = json.loads((ROOT / 'meer/v01/CPU_ACCEPTANCE_CPU03.json').read_bytes())
    path = Path(prior['raw_archive_path'])
    raw = path.read_bytes()
    if sha(raw) != prior['archive_sha256']:
        raise ValueError('Historical CPU03 archive identity mismatch')
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        observed = []
        for arm in ('B', 'B_BYPASS'):
            prefix = 'validation/' + arm + '/'
            events = [json.loads(x) for x in archive.read(prefix + 'agent/adk_events.jsonl').splitlines() if x]
            calls = [p['function_call']['name'] for e in events
                     for p in e.get('event', {}).get('content', {}).get('parts', [])
                     if p.get('function_call')]
            row = next(r for r in prior['records'] if r['arm'] == arm)
            native = archive.read(prefix + 'TaskResult.json')
            junit = archive.read(prefix + 'verifier/phase2.junit.xml')
            assert sha(native) == row['TaskResult_sha256'] and sha(junit) == row['JUnit_sha256']
            assert json.loads(archive.read(prefix + 'agent/cleanup.json'))['complete']
            observed.append(dict(arm=arm,script_calls=calls.count('run_skill_script'),
                explicit_submit_calls=calls.count('submit_patch'),
                native_synthetic_resolved=json.loads(native)['resolved'],
                TaskResult_sha256=sha(native), JUnit_sha256=sha(junit)))
    return dict(Notebook_id=prior['Notebook_id'], version=1, archive_sha256=sha(raw),
        archive_bytes=len(raw), CRC_valid=True, CPU_MODEL='SCRIPTED_ONLY',
        scope='Rechecked existing original records; no new Runner or model execution', observations=observed)


def provenance():
    sources, records = pinned_sources()
    guide = (ROOT.parent / 'official-inputs/HARNESS_README.md').read_bytes()
    pins = json.loads((ROOT / 'meer/v01/OFFICIAL_SOURCE_PINS.json').read_bytes())
    assert sha(guide) == pins['HARNESS_README.md']['sha256']
    candidates = {arm: sha((ROOT / f'meer/v01/submission_{arm}.zip').read_bytes()) for arm in 'ABC'}
    assert candidates == {
        'A': '07263740c5ee22bf6611d7fa31dafbc84d7fb50288d22355b9201cd6954a6840',
        'B': 'd962044f264d8f36aea6263abf4dcdb118d5755e82a91cb9b2bd0bc1f6f7c9cd',
        'C': '8dd48fee0c96424a40ed47512f0d788d9b13518e7d73395bd89d2fb07204eb83'}
    with zipfile.ZipFile(ROOT / 'meer/v01/submission_B.zip') as original:
        assert original.testzip() is None
        original_verifier = original.read('skills/meer-evidence/scripts/verify.py')
    return dict(base_PR34=BASE, wheels=records, source_member_count=len(sources),
        guide_sha256=sha(guide), frozen_ABC_SHA256=candidates,
        existing_MEER_verifier_source_sha256=sha((ROOT / 'meer/v01/verify.py').read_bytes()),
        frozen_B_verifier_member_sha256=sha(original_verifier),
        prior_audit={name: sha((ROOT / 'egrd/v02' / name).read_bytes()) for name in (
            'FINAL_DECISION.md','ARCHITECTURE_DECISION.md','OFFICIAL_INTERFACE_AUDIT.md',
            'CONTEXT_GROWTH_ANALYSIS.md','EVIDENCE_TO_PATCH_FAILURES.md','NEXT_EXPERIMENT_PROTOCOL.md')},
        historical_CPU_bypass=historical_bypass(),
        limits=['Full official ADK/Compiler packages are not installed in the local interpreter; no full SDK compilation claimed',
            'Complete scripts/inference.py loader is not present locally; pinned guide is the available competition-loader evidence',
            'No current private-platform or future Gemma adoption guarantee'],
        operations=dict(new_model_requests=0,new_Agent_sessions=0,GPU=0,Notebook_saves=0,formal_submissions=0))


if __name__ == '__main__':
    output = HERE / 'SOURCE_PROVENANCE.json'
    raw = (json.dumps(provenance(), indent=2, sort_keys=True) + '\n').encode()
    if output.exists() and output.read_bytes() != raw:
        raise ValueError('Provenance differs; preserve and investigate before replacing')
    if not output.exists():
        output.write_bytes(raw)
    print(json.dumps(dict(wheels=4, source_members=len(pinned_sources()[0]), new_Agent_sessions=0)))
