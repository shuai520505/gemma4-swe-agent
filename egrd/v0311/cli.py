"""Single owner-authorized CPU push; all further operations are read-only."""
import datetime
import json
import os
import subprocess

from .prepare import HERE, PRIVATE, REF, sha, write


def run(args, label, timeout=300):
    directory = PRIVATE / 'cli' / label
    directory.mkdir(parents=True, exist_ok=False)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        result = subprocess.run(['kaggle', *args], capture_output=True, timeout=timeout,
            env=dict(os.environ, HTTPS_PROXY='http://127.0.0.1:7890', PYTHONIOENCODING='utf-8'))
        code, out, err = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        code, out, err = None, exc.stdout or b'', exc.stderr or b''
    (directory / 'stdout.txt').write_bytes(out)
    (directory / 'stderr.txt').write_bytes(err)
    write(directory / 'record.json', dict(args=args, started=started, returncode=code,
          stdout_sha256=sha(out), stderr_sha256=sha(err)))
    print(json.dumps(dict(label=label, returncode=code, stdout_bytes=len(out), stderr_bytes=len(err))))
    return code


def push():
    folder = PRIVATE / 'notebook-v1'
    meta = json.loads((folder / 'kernel-metadata.json').read_bytes())
    build = json.loads((HERE / 'CPU_BUILD.json').read_bytes())
    assert meta['id'] == REF and meta['is_private'] is True
    assert not any(meta[k] for k in ('enable_gpu','enable_tpu','enable_internet','machine_shape','model_sources','competition_sources','kernel_sources'))
    assert sha((folder/'study.ipynb').read_bytes()) == build['Notebook_sha256']
    assert sha((folder/'kernel-metadata.json').read_bytes()) == build['metadata_sha256']
    assert sha((folder/'payload.zip').read_bytes()) == build['payload_sha256']
    with (PRIVATE / 'CPU_DISPATCH.json').open('x', encoding='utf8') as f:
        json.dump(dict(ref=REF, CPU_only=True, max_dispatches=1,
            grant='Owner EGRD V0.3.1.1 instruction; exactly one additional CPU execution',
            status='ATTEMPT_RECORDED_DO_NOT_REDISPATCH', Notebook_sha256=build['Notebook_sha256']), f, indent=2)
        f.flush(); os.fsync(f.fileno())
    return run(['kernels','push','-p',str(folder),'-t','3600'], 'dispatch', 900)


if __name__ == '__main__':
    import sys
    if sys.argv[1] == 'push':
        push()
    else:
        run(sys.argv[2:], sys.argv[1])
