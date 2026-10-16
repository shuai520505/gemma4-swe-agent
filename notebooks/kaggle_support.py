"""Notebook support code, embedded for Kaggle; no agent tools or model replacement."""
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import shutil
import stat
import time
import traceback
import zipfile

MODEL_NAME = 'gemma-4-31b-it-qat-w4a16-ct'
SUBMISSION_FILES = {'agent.yaml', 'eval_config.yaml', 'prompts/system.md'}


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, default=str) + '\n', encoding='utf-8')
    tmp.replace(path)


def one_path(candidates, label):
    candidates = sorted({Path(p).resolve() for p in candidates})
    if len(candidates) != 1:
        raise RuntimeError(f'{label}: expected one mounted input, found {candidates}. '
                           'Attach the official input; remove duplicate mounts or set an explicit path.')
    return candidates[0]


def discover_inputs(root, overrides=None):
    root = Path(root)
    overrides = overrides or {}
    # File signatures support both old and new Kaggle mount layouts.
    data = Path(overrides['data']) if overrides.get('data') else one_path(
        [p.parent for p in root.rglob('tasks.jsonl') if (p.parent / 'snapshots').is_dir()],
        'Competition data (401 means account authorization; no downloads attempted)')
    wheels = Path(overrides['wheelhouse']) if overrides.get('wheelhouse') else one_path(
        [p.parent for p in root.rglob('swegemma-*.whl')], 'Official wheelhouse')
    model = Path(overrides['model']) if overrides.get('model') else one_path(
        [p.parent for p in root.rglob('config.json')
         if MODEL_NAME in p.parts and any(p.parent.glob('*.safetensors'))], '31B model')
    archive = Path(overrides['zip']) if overrides.get('zip') else one_path(
        [p for name in ('submission.zip', 'submission.bundle') for p in root.rglob(name)
         if not any(p.is_relative_to(excluded) for excluded in (data, wheels, model))], 'V0 submission.zip')
    for path in (data, wheels, model, archive):
        if not path.exists() or not path.resolve().is_relative_to(root.resolve()):
            raise RuntimeError(f'Input is absent or outside Kaggle input root: {path}')
    for name in ('tasks.jsonl', 'snapshots', 'wheels', 'graphs', 'embeddings',
                 'HARNESS_README.md', 'sample_submission/agent.yaml'):
        if not (data / name).exists():
            raise RuntimeError(f'Missing official competition input: {data / name}')
    if MODEL_NAME not in model.parts or not (model / 'config.json').is_file() or not any(model.glob('*.safetensors')):
        raise RuntimeError('Expected mounted official 31B model config and safetensors weights')
    return {'data': data, 'wheelhouse': wheels, 'model': model, 'zip': archive}


def extract_submission(archive_path, destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Use a fresh run directory; never overwrite a previous submission')
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        if len(infos) != len(SUBMISSION_FILES) or {i.filename for i in infos} != SUBMISSION_FILES:
            raise ValueError('V0 ZIP must contain exactly agent.yaml, eval_config.yaml, prompts/system.md')
        if sum(i.file_size for i in infos) > 1024 * 1024:
            raise ValueError('V0 ZIP exceeds the 1 MiB local preflight limit')
        if any(stat.S_ISLNK(i.external_attr >> 16) or i.flag_bits & 1 for i in infos):
            raise ValueError('Symlink or encrypted ZIP entry is unsupported')
        if archive.testzip() is not None:
            raise ValueError('ZIP CRC verification failed')
        archive.extractall(destination)
    return hashlib.sha256(Path(archive_path).read_bytes()).hexdigest()


def budget_profile(mode):
    if mode == 'single':
        return dict(max_time_minutes=60.0, max_tool_calls=100, timeout_seconds=300,
                    verification_timeout_seconds=300, max_tasks=1, task_wall_minutes=75.0)
    if mode == 'batch':
        # 50 * 12 + 45 bootstrap + 15 finalization = 660 minutes < 720.
        return dict(max_time_minutes=8.0, max_tool_calls=60, timeout_seconds=120,
                    verification_timeout_seconds=300, max_tasks=50, task_wall_minutes=12.0)
    raise ValueError('RUN_MODE must be single or batch')


def admission_seconds(session_started, task_wall_minutes, now=None):
    # A 705-minute soft deadline leaves 15 minutes before the 12-hour ceiling.
    now = time.monotonic() if now is None else now
    remaining = 705 * 60 - (now - session_started)
    return task_wall_minutes * 60 if remaining >= task_wall_minutes * 60 else 0.0


def preserve_server_log(server, output):
    path = getattr(server, 'log_path', None)
    if path and Path(path).is_file():
        shutil.copyfile(path, Path(output) / 'vllm.log')


def exception_record(output, stage, exc):
    write_json(Path(output) / 'exception.json', dict(
        stage=stage, exception_type=type(exc).__name__, message=str(exc),
        traceback=''.join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        recorded_at=datetime.now(timezone.utc).isoformat(),
        real_task_completed=False, repair_score=None))


def trace_from_result(result):
    from adk_eval_core.tracing import SessionTrace
    trace = result.trace
    if trace is None and getattr(result, 'trace_path', None):
        path = Path(result.trace_path)
        if path.is_file():
            trace = SessionTrace.from_json(path)
    return trace


def persist_result(result, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    # Preserve even empty patches and outputs: absence is a result, not a pass.
    (directory / 'agent.patch').write_text(result.agent_patch or '', encoding='utf-8')
    (directory / 'phase2.log').write_text(result.test_output or '', encoding='utf-8')
    trace = trace_from_result(result)
    entries = []
    if trace is not None:
        trace.save(directory / 'trace.json')
        trace.save(directory / 'trace_legacy.json', format='legacy')
        entries = trace.to_dict(format='legacy')['entries']
    tool_events = [e for e in entries if e['type'] in ('tool_call', 'tool_response')]
    model_events = [e for e in entries if e['type'] not in ('tool_call', 'tool_response') or e.get('usage')]
    for name, events in [('tool_events.jsonl', tool_events), ('model_events.jsonl', model_events)]:
        (directory / name).write_text(''.join(json.dumps(e) + '\n' for e in events), encoding='utf-8')
    submitted = False
    for event in tool_events:
        if event['type'] == 'tool_response' and event.get('tool') == 'submit_patch':
            try:
                submitted |= json.loads(event.get('result', '{}')).get('status') == 'ok'
            except (ValueError, AttributeError):
                pass
    # verify_task's final test result contains this exact stdout/stderr envelope.
    # Patch/setup errors can also have a nonzero code, so code alone is insufficient.
    phase2_ran = (result.test_exit_code >= 0 and (result.test_output or '').startswith('STDOUT:\n')
                  and '\nSTDERR:\n' in result.test_output)
    has_inference = result.total_llm_calls > 0 and any(e.get('usage') or e['type'] in
                   ('thinking', 'text', 'final', 'tool_call') for e in entries)
    record = dict(instance_id=result.instance_id, repo=result.repo, resolved=result.resolved,
                  error=result.error, test_exit_code=result.test_exit_code,
                  phase2_tests_ran=phase2_ran, total_llm_calls=result.total_llm_calls,
                  tool_calls=result.tool_calls, duration_seconds=result.duration_seconds,
                  patch_chars=len(result.agent_patch or ''), explicit_submit_patch_success=submitted,
                  model_events_present=has_inference,
                  first_task_goal_completed=bool(has_inference and submitted and result.agent_patch
                                                and phase2_ran),
                  # Retain official result; never turn missing evidence into a score.
                  competition_score=None)
    write_json(directory / 'result.json', record)
    return record


async def evaluate_with_deadline(evaluator, task, context, directory, deadline_seconds, server=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    pending = asyncio.create_task(evaluator.evaluate_task(task=task, task_index=1,
                                  total_tasks=1, context=context))
    try:
        while True:
            remaining = deadline_seconds - (time.monotonic() - started)
            write_json(directory / 'live_status.json', dict(
                instance_id=task.instance_id, elapsed_seconds=time.monotonic() - started,
                phase=str(getattr(context, 'current_phase', 'unknown')),
                total_llm_calls=context.llm_calls_used, tool_calls=context.tool_calls_used,
                patch_submitted=context.patch_submitted, completed=False))
            if context.submitted_patch is not None:
                (directory / 'last_submitted.patch').write_text(context.submitted_patch, encoding='utf-8')
            if server is not None:
                preserve_server_log(server, directory.parent)
            if remaining <= 0:
                raise TimeoutError(f'Outer task wall-clock budget exhausted ({deadline_seconds}s)')
            done, _ = await asyncio.wait({pending}, timeout=min(15.0, remaining))
            if done:
                result = pending.result()
                record = persist_result(result, directory)
                write_json(directory / 'live_status.json', dict(
                    instance_id=task.instance_id, completed=True, result=record))
                return record
    except BaseException as exc:
        exception_record(directory, 'evaluate_task', exc)
        if context.submitted_patch is not None:
            (directory / 'last_submitted.patch').write_text(context.submitted_patch, encoding='utf-8')
        if not pending.done():
            pending.cancel()
            # Cancellation of underlying synchronous work may take longer; do not
            # wait indefinitely for cleanup and do not claim a completed Phase 2.
            await asyncio.wait({pending}, timeout=30)
        # Retrieve completed exceptions to avoid "Task exception was never retrieved".
        if pending.done() and not pending.cancelled():
            pending.exception()
        raise


def bundle_run(run_dir):
    run_dir = Path(run_dir)
    return Path(shutil.make_archive(str(run_dir), 'zip', root_dir=run_dir))
