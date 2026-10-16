"""Collect terminal Notebook evidence once into a new directory, without overwrite."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import time


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('kernel'); p.add_argument('output',type=Path)
    p.add_argument('--seconds',type=int,default=10800)
    p.add_argument('--file-pattern',default=r'(\.zip$|installation\.log$|cpu_gate\.json$|cpu_tests\.log$|runner\.(stdout|stderr)\.log$)')
    args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    import requests
    send=requests.Session.send
    def bounded(self,request,**kwargs):
        kwargs.setdefault('timeout',30)
        return send(self,request,**kwargs)
    requests.Session.send=bounded
    import kaggle
    start=time.monotonic()
    while time.monotonic()-start<args.seconds:
        try:
            status=kaggle.api.kernels_status(args.kernel)
            row=dict(status=str(status.status),failure_message=status.failure_message,
                observed_utc=datetime.now(timezone.utc).isoformat())
            with (args.output/'status.jsonl').open('a',encoding='utf-8') as f:
                f.write(json.dumps(row)+'\n'); f.flush()
            print(json.dumps(row),flush=True)
            if any(row['status'].endswith('.'+s) for s in ('COMPLETE','ERROR','CANCEL_ACKNOWLEDGED')):
                log=kaggle.api.kernels_logs(args.kernel)
                with (args.output/'native-kernel.log').open('x',encoding='utf-8') as f: f.write(log or '')
                kaggle.api.kernels_output(args.kernel,path=str(args.output/'files'),force=False,quiet=True,
                    file_pattern=args.file_pattern,page_size=200)
                print('Terminal evidence downloaded',flush=True)
                return
        except requests.RequestException as exc:
            print('Transport retry:',type(exc).__name__,flush=True)
        time.sleep(30)
    print('Watch limit reached; Notebook outcome remains unconfirmed',flush=True)


if __name__=='__main__': main()
