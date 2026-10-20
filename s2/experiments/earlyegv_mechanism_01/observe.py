"""One bounded status/log observation, optional terminal output download; no launch."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import requests

HERE = Path(__file__).resolve().parent
SLUG = 'wudangdexiaodoashi/gemma4-s2-earlyegv-mechanism-01'
original = requests.Session.send


def send(self, request, **kwargs):
    kwargs.setdefault('timeout', 30)
    return original(self, request, **kwargs)


requests.Session.send = send
from kaggle import api


if __name__ == '__main__':
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder = HERE / 'observations' / stamp
    folder.mkdir(parents=True, exist_ok=False)
    status = api.kernels_status(SLUG).to_dict(ignore_defaults=False)
    with (folder / 'status.json').open('x', encoding='utf-8') as f:
        json.dump(dict(queried_at_utc=stamp, notebook=SLUG, saved_version=1, status=status), f, indent=2)
    print(json.dumps(status))
    try:
        logs = api.kernels_logs(SLUG)
        (folder / 'kernel.log').write_text(logs, encoding='utf-8')
        try:
            rows = json.loads(logs)
            visible = ''.join(r.get('data', '') for r in rows if isinstance(r, dict))
        except (ValueError, TypeError):
            visible = logs
        print(visible[-5500:])
    except Exception as exc:
        (folder / 'log_exception.json').write_text(json.dumps(dict(type=type(exc).__name__, message=str(exc)), indent=2), encoding='utf-8')
        print('Log unavailable:', type(exc).__name__)
    if '--outputs' in sys.argv:
        assert status['status'] in ('COMPLETE', 'ERROR', 'CANCEL_ACKNOWLEDGED'), 'No terminal evidence download yet'
        target = HERE / 'download'
        files, token = api.kernels_output(SLUG, str(target), file_pattern=r'(?:^|/)\d{8}T\d{6}_\d{6}Z\.zip$', page_size=100)
        (folder / 'download.json').write_text(json.dumps(dict(files=files, next_page_token=token), indent=2), encoding='utf-8')
        print('Downloaded', files, 'next', token)
