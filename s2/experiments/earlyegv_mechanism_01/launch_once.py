"""Exactly one authorized SaveKernel transmission; uncertain response never retried."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import requests

HERE = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat()


def emit(name, value):
    with (HERE / name).open('x', encoding='utf-8') as file:
        file.write(json.dumps(value, indent=2, default=str) + '\n')
        file.flush()
        os.fsync(file.fileno())


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


if __name__ == '__main__':
    frozen = load(HERE / 'EXECUTION_BUILD_MANIFEST.json')
    folder = HERE / 'notebooks/gpu01'
    assert hashlib.sha256((folder / 'study.ipynb').read_bytes()).hexdigest() == frozen['notebook_sha256']
    assert hashlib.sha256((folder / 'kernel-metadata.json').read_bytes()).hexdigest() == frozen['metadata_sha256']
    assert not (HERE / 'SAVE_REQUEST_SENT.json').exists(), 'Request already sent/uncertain; query, never resubmit'
    assert not (HERE / 'SAVE_INTENT.json').exists(), 'Launch invocation already recorded; inspect before any action'
    emit('SAVE_INTENT.json', dict(at_utc=now(), max_save_transmissions=1, timeout_seconds=10000,
         machine='NvidiaL4', experiment_id='S2-T500-EARLYEGV-MECHANISM-01', official_competition_submission=False))
    original = requests.Session.send

    def send(self, request, **kwargs):
        kwargs.setdefault('timeout', 60)
        is_save = request.url.rstrip('/').endswith('/SaveKernel')
        if is_save:
            body = json.loads(request.body)
            assert body['sessionTimeoutSeconds'] == 10000
            assert body['machineShape'] == 'NvidiaL4'
            assert hashlib.sha256(body['text'].encode()).hexdigest() == frozen['notebook_API_text_sha256']
            # Exclusive durable file prevents SDK/HTTP automatic retransmission.
            emit('SAVE_REQUEST_SENT.json', dict(at_utc=now(), method=request.method,
                 endpoint=request.url.split('?')[0], request_body_sha256=hashlib.sha256(request.body if isinstance(request.body, bytes) else request.body.encode()).hexdigest(),
                 requested_timeout_seconds=body['sessionTimeoutSeconds'], requested_machine=body['machineShape'],
                 notebook_text_sha256=hashlib.sha256(body['text'].encode()).hexdigest(),
                 input_sources={k:body.get(k) for k in ('modelDataSources', 'datasetDataSources', 'competitionDataSources')},
                 note='Transmission intent persisted immediately before requests.send; lack of response means UNKNOWN, not safe to resubmit.'))
        response = original(self, request, **kwargs)
        if is_save:
            try:
                content = response.json()
            except ValueError:
                content = response.text
            emit('SAVE_RAW_RESPONSE.json', dict(at_utc=now(), http_status=response.status_code, response=content))
        return response

    requests.Session.send = send
    from kaggle import api
    try:
        result = api.kernels_push(str(folder), timeout='10000', acc='NvidiaL4')
        raw = result.to_dict(ignore_defaults=False)
        emit('SAVE_RESULT.json', dict(at_utc=now(), result=raw))
        print(json.dumps(raw, indent=2))
    except BaseException as exc:
        emit('SAVE_EXCEPTION.json', dict(at_utc=now(), type=type(exc).__name__, message=str(exc),
             state='UNKNOWN_IF_TRANSMITTED; inspect request marker and query existing version; never blindly retry'))
        raise
