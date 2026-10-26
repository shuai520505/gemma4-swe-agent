"""Official CLI adapter: private raw capture, bounded reads, once-only CPU push."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRIVATE = ROOT.parent / 'private-evidence/egrd_v023'
REQUESTED_REF = 'wudangdexiaodoashi/egrd-v023-compiler-cpu'
# The v1 CLI reply returned the title-derived canonical slug. Do not resubmit
# the intended slug; follow only the confirmed created Notebook identity.
REF = 'wudangdexiaodoashi/egrd-v023-compiler-cpu-recovery'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(args, label, timeout=240):
    """No credentials/config dumps; output stays private even on failure."""
    directory = PRIVATE / 'cli' / label
    directory.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, HTTPS_PROXY='http://127.0.0.1:7890',
               PYTHONIOENCODING='utf-8')
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        result = subprocess.run(['kaggle', *args], env=env, capture_output=True,
                                timeout=timeout)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = None, exc.stdout or b'', exc.stderr or b''
    (directory / 'stdout.txt').write_bytes(stdout)
    (directory / 'stderr.txt').write_bytes(stderr)
    safe_args = list(args)
    if '--page-token' in safe_args:
        safe_args[safe_args.index('--page-token') + 1] = '[PAGINATION_TOKEN_REDACTED]'
    record = dict(args=safe_args, started=started, returncode=code,
                  stdout_sha256=sha(stdout), stderr_sha256=sha(stderr))
    (directory / 'record.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf8')
    print(json.dumps(dict(label=label, returncode=code, stdout_bytes=len(stdout),
                         stderr_bytes=len(stderr))), flush=True)
    return code, stdout.decode('utf8', errors='replace'), stderr.decode('utf8', errors='replace')


def push(version):
    assert version in (1, 2)
    notebook = HERE / f'cpu-v{version}'
    meta = json.loads((notebook / 'kernel-metadata.json').read_bytes())
    assert meta['id'] == REF and meta['is_private'] is True
    assert meta['enable_gpu'] is False and meta['enable_tpu'] is False
    assert meta['machine_shape'] == '' and not meta['model_sources']
    raw = (notebook / meta['code_file']).read_bytes()
    assert not meta['enable_internet']
    dispatch = PRIVATE / f'dispatch-v{version}.json'
    if version == 2:
        assert (PRIVATE / 'v1-confirmed-infrastructure-failure.json').is_file()
    # Persist before the CLI can cause a remote mutation. Unknown is never retried.
    PRIVATE.mkdir(parents=True, exist_ok=True)
    with dispatch.open('x', encoding='utf8') as file:
        json.dump(dict(ref=REF, intended_version=version, status='DISPATCH_ATTEMPT_RECORDED',
                       notebook_sha256=sha(raw), metadata_sha256=sha(
                           (notebook/'kernel-metadata.json').read_bytes()), CPU_only=True), file, indent=2)
    return run(['kernels', 'push', '-p', str(notebook), '-t', '3600'],
               f'push-v{version}', timeout=300)


if __name__ == '__main__':
    if sys.argv[1] == 'push':
        code, out, err = push(int(sys.argv[2]))
        # Push replies may include account details: inspect private output separately.
        print('Push returned', code, '; recover status read-only before any subsequent action.')
    else:
        run(sys.argv[2:], sys.argv[1])
