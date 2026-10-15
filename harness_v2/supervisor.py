"""Separate worker process per task; cancellation never reuses a live sandbox."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time

import psutil

from .evidence import atomic_json
from .outcomes import normalize


def _read(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def _alive(proc):
    try:
        return proc.is_running() and proc.status() not in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD)
    except psutil.NoSuchProcess:
        return False
    except psutil.AccessDenied:
        return True


def _remember(pid, known):
    try:
        root=psutil.Process(pid)
        for p in [root]+root.children(recursive=True):
            known[(p.pid,p.create_time())]=p
    except (psutil.NoSuchProcess,psutil.AccessDenied):
        pass


def _remember_group(pid, known):
    if os.name!='posix':
        return
    for p in psutil.process_iter():
        try:
            if os.getpgid(p.pid)==pid:
                known[(p.pid,p.create_time())]=p
        except (ProcessLookupError,PermissionError,psutil.NoSuchProcess):
            pass


def stop_tree(process, known, grace, job=None):
    _remember(process.pid, known)
    _remember_group(process.pid, known)
    if job is not None:
        job.terminate()
    if os.name=='posix':
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    else:
        # Kill known descendants before their parent can orphan them.
        for p in reversed(list(known.values())):
            try:
                p.terminate()
            except psutil.NoSuchProcess:
                pass
    end=time.monotonic()+grace
    while time.monotonic()<end and any(_alive(p) for p in known.values()):
        time.sleep(.02)
    if os.name=='posix':
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    for p in known.values():
        if _alive(p):
            try:
                p.kill()
            except psutil.NoSuchProcess:
                pass
    try:
        process.wait(timeout=max(grace,1))
    except subprocess.TimeoutExpired:
        pass
    psutil.wait_procs(list(known.values()), timeout=max(grace,1))
    if job is not None:
        until=time.monotonic()+max(grace,1)
        while job.active() and time.monotonic()<until:
            time.sleep(.02)
    _remember_group(process.pid,known)
    return not any(_alive(p) for p in known.values()) and (job is None or job.active()==0)


def supervise(command, directory, *, outer_seconds, stage_caps, poll_seconds=.5,
              terminate_grace=5, cwd=None):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    # Every attempt needs a fresh run directory, even after an incomplete attempt.
    with (directory/'controller_started.json').open('x',encoding='utf-8') as f:
        json.dump(dict(started=True, outer_seconds=outer_seconds),f)
    start=time.monotonic()
    known={}
    failure=None
    controller_stage=None
    progress={}
    totals={}
    last_stage='prepare_agent'
    last_change=start
    options=dict(start_new_session=True) if os.name=='posix' else dict(
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW | 0x00000004)
    job=None
    with (directory/'worker.stdout.log').open('xb') as stdout, (directory/'worker.stderr.log').open('xb') as stderr:
        process=subprocess.Popen(command,stdout=stdout,stderr=stderr,cwd=cwd,**options)
        if os.name=='nt':
            from .windows_job import WindowsJob
            job=WindowsJob(process)
        try:
            while True:
                _remember(process.pid, known)
                now=time.monotonic()
                progress=_read(directory/'progress.json',progress)
                stage=progress.get('stage',last_stage)
                if stage!=last_stage:
                    changed=max(last_change,min(now,progress.get('stage_started_monotonic',now)))
                    totals[last_stage]=totals.get(last_stage,0)+(changed-last_change)
                    last_stage,last_change=stage,changed
                if process.poll() is not None:
                    _remember_group(process.pid,known)
                    descendants_active=job.active()>0 if job is not None else any(_alive(p) for p in known.values())
                    if not descendants_active:
                        break
                if now-start>=outer_seconds:
                    failure='outer_timeout'; controller_stage=stage
                    break
                if stage in stage_caps and totals.get(stage,0)+(now-last_change)>stage_caps[stage]:
                    failure='stage_timeout'; controller_stage=stage
                    break
                time.sleep(poll_seconds)
        except BaseException as exc:
            failure=type(exc).__name__; controller_stage=last_stage
        finally:
            if process.poll() is None or any(_alive(p) for p in known.values()) or (job is not None and job.active()>0):
                stopped=stop_tree(process,known,terminate_grace,job)
            else:
                stopped=job is None or job.active()==0
            if job is not None:
                job.close()
    raw=_read(directory/'official_result.json')
    result=normalize(raw,started=True,stage=controller_stage or progress.get('stage'))
    done=_read(directory/'worker_done.json',{})
    cleanup=done.get('cleanup_complete') is True
    if not stopped:
        failure=failure or 'process_tree_not_stopped'
    elif not failure and process.returncode!=0:
        failure='worker_nonzero_exit'
    elif not failure and not cleanup:
        failure='cleanup_unconfirmed'
    result.update(controller_error=failure,controller_failure_stage=controller_stage,
        process_exit_code=process.returncode,process_tree_stopped=stopped,
        cleanup_complete=cleanup,duration_seconds=time.monotonic()-start,
        allow_next_run=not failure and stopped and cleanup,
        evidence=dict(official_result=raw is not None,
            patch_checkpoint=(directory/'latest.patch').is_file(),
            incremental_adk_events=(directory/'adk_events.jsonl').is_file(),
            native_trace=any(directory.glob('harness/traces/*.json')),
            phase2_output=(directory/'phase2.log').is_file()),
        official_fields_unchanged=True)
    atomic_json(directory/'audit_result.json',result)
    return result
