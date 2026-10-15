"""Scripted failure injection only. No model, Agent or real task is evaluated."""
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from harness_v2.evidence import Journal, atomic_json

mode, directory=sys.argv[1:]
p=Path(directory)
if mode in ('launcher','launcher_outer'):
    subprocess.Popen([sys.executable,__file__,'slow_ok' if mode=='launcher' else 'outer',directory])
    raise SystemExit(0)
j=Journal(p)
j.stage('agent')
j.patch('diff --git a/x b/x\n+scripted evidence\n',source='scripted_cpu_test')
with (p/'adk_events.jsonl').open('w',encoding='utf-8') as f:
    f.write('{"scripted_cpu_fixture":true}\n'); f.flush()
if mode=='outer':
    script="import time,pathlib;time.sleep(10);pathlib.Path(__import__('sys').argv[1]).write_text('contamination')"
    subprocess.Popen([sys.executable,'-c',script,str(p/'contamination.txt')])
    time.sleep(30)
elif mode=='agent':
    time.sleep(30)
elif mode=='verifier':
    j.stage('verification'); time.sleep(30)
else:
    if mode=='slow_ok': time.sleep(.5)
    atomic_json(p/'official_result.json',{'resolved':True,'test_exit_code':0})
    j.stage('cleanup')
    if mode=='cleanup': time.sleep(30)
    atomic_json(p/'worker_done.json',{'cleanup_complete':True})
