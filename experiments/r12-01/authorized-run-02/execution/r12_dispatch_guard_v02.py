"""CPU-safe packaging and authorization guards; importing this module has no side effects."""
import hashlib
import json
from pathlib import Path

RUN_ID = 'R12_AUTHORIZED_GPU_RUN_02'
LIMIT = 1048576

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8388608), b''):
            h.update(block)
    return h.hexdigest()

def require_authorization(receipt):
    # A receipt is only an accident guard. Its creation requires a NEW human instruction.
    if receipt.get('run_id') != RUN_ID or receipt.get('explicit_user_GPU_authorization') is not True:
        raise PermissionError('NEW_RUN_02_HUMAN_AUTHORIZATION_REQUIRED')
    if receipt.get('prior_authorization_consumed') is not True or receipt.get('authorization_source') == 'CONSUMED_RUN_01':
        raise PermissionError('CONSUMED_AUTHORIZATION_FORBIDDEN')
    if receipt.get('maximum_dispatches') != 1 or receipt.get('maximum_node_seconds') != 18000:
        raise ValueError('FROZEN_DISPATCH_BUDGET_MISMATCH')
    if receipt.get('formal_submission_authorized') or receipt.get('retries_authorized'):
        raise PermissionError('SUBMISSION_AND_RETRY_FORBIDDEN')

def require_quota(available_seconds, window_seconds):
    if available_seconds < 73200:
        raise ValueError('QUOTA_BELOW_FROZEN_FLOOR')
    if window_seconds != 18000:
        raise ValueError('FROZEN_FIVE_HOUR_WINDOW_REQUIRED')

def unique(root, name):
    paths = list(Path(root).rglob(name))
    if len(paths) != 1 or not paths[0].is_file():
        raise FileNotFoundError('MISSING_OR_AMBIGUOUS_INPUT: ' + name)
    return paths[0]

def require_hashes(root, hashes):
    root = Path(root).resolve()
    for name, expected in hashes.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or digest(path) != expected:
            raise ValueError('FROZEN_HASH_MISMATCH: ' + name)

def packaging(folder, expected=None):
    folder = Path(folder).resolve()
    metadata = json.loads((folder / 'kernel-metadata.json').read_bytes())
    if metadata.get('code_file') != 'study.ipynb':
        raise ValueError('UNEXPECTED_CLI_SOURCE_FILE')
    path = folder / metadata['code_file']
    raw = path.read_bytes()
    notebook = json.loads(raw.decode('utf-8'))
    sources = [''.join(c['source']) if isinstance(c['source'], list) else c['source']
               for c in notebook['cells'] if c['cell_type'] == 'code']
    code_bytes = sum(len(s.encode('utf-8')) for s in sources)
    # Kaggle 2.2.2 kernels_push reserializes the notebook with json.dumps.
    upload = json.loads(raw.decode('utf-8'))
    for cell in upload['cells']:
        if cell['cell_type'] == 'code' and 'outputs' in cell:cell['outputs'] = []
        if isinstance(cell.get('source'), list):cell['source'] = ''.join(cell['source'])
    cli_source_bytes = len(json.dumps(upload).encode('utf-8'))
    if len(raw) >= LIMIT or code_bytes >= LIMIT or cli_source_bytes >= LIMIT:
        raise ValueError('SOURCE_TOO_LARGE_NO_API_REQUEST')
    if notebook.get('nbformat') != 4 or not sources:
        raise ValueError('INVALID_NOTEBOOK_METADATA')
    for source in sources:
        compile(source, str(path), 'exec')
    required = dict(language='python', kernel_type='notebook', is_private=True,
                    enable_gpu=True, enable_tpu=False, enable_internet=False, machine_shape='NvidiaL4')
    if any(metadata.get(k) != v for k, v in required.items()):
        raise ValueError('INVALID_KAGGLE_METADATA')
    if metadata['id'].split('/')[-1] != metadata['title'].lower().replace(' ', '-'):
        raise ValueError('TITLE_SLUG_MISMATCH')
    if expected is not None:
        if digest(path) != expected['notebook_sha256'] or digest(folder/'kernel-metadata.json') != expected['metadata_sha256']:
            raise ValueError('PACKAGING_HASH_MISMATCH')
    return dict(notebook_bytes=len(raw), code_cell_bytes=code_bytes, CLI_serialized_source_bytes=cli_source_bytes, notebook_sha256=digest(path),
                metadata_sha256=digest(folder/'kernel-metadata.json'), code_file=metadata['code_file'])

def pre_dispatch(folder, build, receipt):
    result = packaging(folder, build)  # ALWAYS before authentication, quota or any Kaggle write.
    require_authorization(receipt)
    if build.get('gate') != 'R12_REDISPATCH_READY':
        raise PermissionError('COMPACT_DEPENDENCY_GATE_NOT_READY')
    return result
