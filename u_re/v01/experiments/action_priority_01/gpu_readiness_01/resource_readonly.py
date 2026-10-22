"""Reuse raw-duration/status reader scoped to this independent observation."""
from pathlib import Path
import types

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]


def main():
    source_path=ROOT/'u_re/v01/experiments/gemma_smoke_01/recovery_01/resource_readonly.py'
    text=source_path.read_text(encoding='utf-8').replace('planning_threshold=10800','planning_threshold=20600').replace('>=10800','>=20600').replace('window_seconds_requested=5400','window_seconds_requested=10000')
    m=types.ModuleType('action_resource_readonly');m.__file__=str(source_path)
    exec(compile(text,str(source_path),'exec'),m.__dict__)
    m.HERE=HERE/'resource_snapshot';m.main()


if __name__=='__main__':main()
