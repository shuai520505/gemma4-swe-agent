"""Reuse the frozen CPU-only one-save/status guard with a NEW artifact root.

Changing the module's host-side output root does not change any frozen file,
official verifier behavior, candidate or Notebook accelerator setting.
"""
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    mode=sys.argv[1]
    if mode=='launch':
        from u_re.v01 import launch_cpu as host
        host.HERE=HERE
        host.launch('cpu01')
    elif mode=='observe':
        from u_re.v01 import observe_cpu as host
        host.HERE=HERE
        host.observe('cpu01',len(sys.argv)>2 and sys.argv[2]=='collect')
    else:raise ValueError(mode)


if __name__=='__main__':main()
