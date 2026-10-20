"""Bounded read-only saved-version log stream; retain partial bytes on timeout."""
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import requests

HERE = Path(__file__).resolve().parent
original = requests.Session.send


def send(self, request, **kwargs):
    kwargs.setdefault('timeout', (10, 10))
    return original(self, request, **kwargs)


requests.Session.send = send
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelSessionLogsStreamRequest


if __name__ == '__main__':
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder = HERE / 'observations' / stamp
    folder.mkdir(parents=True, exist_ok=False)
    query = ApiGetKernelSessionLogsStreamRequest()
    query.user_name = 'wudangdexiaodoashi'
    query.kernel_slug = 'gemma4-s2-earlyegv-mechanism-01'
    query.wait_for_logs_url_seconds = 2
    details = dict(queried_at_utc=stamp, read_only=True, requested_wait_for_URL_seconds=2)
    response = None
    lines = []
    try:
        with api.build_kaggle_client() as k:
            response = k.kernels.kernels_api_client.get_kernel_session_logs_stream(query)
            details['http_status'] = response.status_code
            started = time.monotonic()
            for line in response.iter_lines(chunk_size=256):
                if line:
                    lines.append(line)
                if len(lines) >= 10000 or time.monotonic() - started >= 15:
                    break
    except Exception as exc:
        details.update(exception_type=type(exc).__name__, error=str(exc))
    finally:
        if response is not None:
            response.close()
        raw = b'\n'.join(lines)
        (folder / 'live.log').write_bytes(raw)
        details['bytes_observed'] = len(raw)
        (folder / 'live_status.json').write_text(json.dumps(details, indent=2), encoding='utf-8')
        print(json.dumps(details))
        visible = []
        for line in lines:
            if not line.startswith(b'data: '):
                continue
            try:
                event = json.loads(line[6:])
            except ValueError:
                continue
            text = event.get('data', '')
            if text.strip() and (event.get('stream_name') == 'stdout' or 'Traceback' in text or 'Error:' in text):
                visible.append(dict(time=event.get('time'), text=text))
        print(json.dumps(visible[-10:], ensure_ascii=False))
