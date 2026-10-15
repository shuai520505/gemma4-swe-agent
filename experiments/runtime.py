"""Embedded comparison controller. Not an Agent tool or a solution provider."""
import re
import hashlib
import json
import stat
import zipfile


def unpack_experiment(archive, destination):
    expected = {'experiment.json'} | {f'{a}/{n}' for a in ('v0', 'v1')
        for n in ('agent.yaml', 'eval_config.yaml', 'prompts/system.md')}
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        if {i.filename for i in infos} != expected or len(infos) != len(expected):
            raise ValueError('Experiment payload must contain only the two agents and frozen plan')
        if sum(i.file_size for i in infos) > 1024 * 1024:
            raise ValueError('Experiment payload too large')
        if any(stat.S_ISLNK(i.external_attr >> 16) or i.flag_bits & 1 for i in infos):
            raise ValueError('Symlink/encrypted payload rejected')
        if z.testzip() is not None:
            raise ValueError('Payload CRC failed')
        if destination.exists():
            raise FileExistsError('Use a fresh evidence directory')
        z.extractall(destination)
    plan = json.loads((destination / 'experiment.json').read_text())
    if plan['historical_task_excluded'] != 'fastapi_15661' or any(
            r['instance_id'] == plan['historical_task_excluded'] for r in plan['schedule']):
        raise ValueError('Audited task cannot enter generalization pilot')
    for name, digest in plan['source_hashes'].items():
        # Do not trust plan paths, even though archive entry names were checked.
        if name not in expected - {'experiment.json'}:
            raise ValueError('Invalid source hash path')
        if hashlib.sha256((destination / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Frozen source mismatch: {name}')
    if set(plan['source_hashes']) != expected - {'experiment.json'}:
        raise ValueError('Missing source hash')
    return plan


async def run_comparison():
    from google.adk.agents.context_cache_config import ContextCacheConfig
    from google.adk.apps._configs import EventsCompactionConfig
    records = []
    failure = None
    try:
        task_map = {t.instance_id: t for t in selected}
        for row in PLAN['schedule']:
            task = task_map[row['instance_id']]
            directory = RUN_DIR / 'runs' / f"{row['index']:02d}_{row['arm']}_{task.instance_id}"
            directory.mkdir(parents=True, exist_ok=False)
            arm_dir = ARMS_DIR / row['arm']
            cfg = EvalConfig(tasks_path=TASKS_PATH, snapshots_dir=DATA_DIR / 'snapshots',
                results_dir=directory / 'harness', submission_dir=arm_dir, models=models,
                sandbox='subprocess', wheels_dir=DATA_DIR / 'wheels',
                graph_dir=str(DATA_DIR / 'graphs'), embeddings_dir=str(DATA_DIR / 'embeddings'),
                timeout_seconds=profile['timeout_seconds'],
                verification_timeout_seconds=profile['verification_timeout_seconds'],
                max_time_minutes=profile['max_time_minutes'], max_tool_calls=profile['max_tool_calls'],
                limits=limits, generation_constraints=constraints, adapter_manifest=adapters,
                concurrency=1, enable_sandbox_testing=True,
                context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=1800, cache_intervals=10),
                events_compaction_config=EventsCompactionConfig(compaction_interval=15, overlap_size=2,
                    token_threshold=14336, event_retention_size=5), verbose=False)
            compile_submission(arm_dir, SwegemmaContext().create_tools(), models,
                               limits=limits, generation_constraints=constraints)
            evaluator = Evaluator(cfg)
            context = SwegemmaContext(docker_manager=evaluator.docker, task=task,
                graph_dir=cfg.graph_dir, embeddings_dir=cfg.embeddings_dir,
                budget=cfg.budget, harness=cfg.harness)
            print('START', json.dumps(row), flush=True)
            start = time.monotonic()
            try:
                record = await evaluate_with_deadline(evaluator, task, context, directory,
                    profile['task_wall_minutes'] * 60, server_instance)
                raw = json.loads((directory / 'result.json').read_text())
                output = (directory / 'phase2.log').read_text()
                patch = (directory / 'agent.patch').read_text()
                record.update(classify(raw, output, patch))
                record.update(outer_timeout=False, execution_error=None,
                    agent_timeout=bool(re.search(r'time.?out|time budget', str(raw.get('error') or ''), re.I)))
            except Exception as exc:
                record = dict(instance_id=task.instance_id, resolved=False,
                    total_llm_calls=context.llm_calls_used, tool_calls=context.tool_calls_used,
                    duration_seconds=time.monotonic() - start, patch_application_valid=False,
                    phase2_invoked=False, collection_failed=False, outer_timeout=isinstance(exc, TimeoutError),
                    execution_error=type(exc).__name__ + ': ' + str(exc))
                exception_record(directory, 'comparison_task', exc)
                if isinstance(exc, TimeoutError):
                    # Synchronous cleanup can outlive cancellation. Stop rather than overlap runs.
                    failure = 'Outer timeout; remaining runs withheld to prevent cross-run interference'
            record.update(arm=row['arm'], category=row['category'], order=row['index'],
                          base_commit=task.base_commit, run_directory=str(directory))
            trace_path = directory / 'trace_legacy.json'
            if trace_path.exists():
                entries = json.loads(trace_path.read_text())['entries']
                record['trace_tool_calls'] = sum(e['type'] == 'tool_call' for e in entries)
                record['prompt_tokens'] = sum(e.get('usage', {}).get('prompt_tokens', 0) for e in entries)
                record['completion_tokens'] = sum(e.get('usage', {}).get('completion_tokens', 0) for e in entries)
            records.append(record)
            write_json(directory / 'comparison_record.json', record)
            write_json(RUN_DIR / 'comparison_records.json', records)
            write_json(RUN_DIR / 'comparison_summary.json', summarize(records, PLAN['schedule']))
            print('RESULT', json.dumps(record), flush=True)
            if failure:
                break
    except BaseException as exc:
        failure = type(exc).__name__ + ': ' + str(exc)
        exception_record(RUN_DIR, 'comparison', exc)
        raise
    finally:
        write_json(RUN_DIR / 'comparison_summary.json', summarize(records, PLAN['schedule']))
        write_json(RUN_DIR / 'comparison_status.json', dict(
            completed=len(records) == len(PLAN['schedule']), execution_failure=failure,
            observed_runs=len(records), planned_runs=len(PLAN['schedule']),
            unrun=[r for r in PLAN['schedule'] if r['index'] not in {x['order'] for x in records}],
            competition_score=None))
        preserve_server_log(server_instance, RUN_DIR)
        server_instance.stop()
        handler.flush()
        handler.close()
        print('EVIDENCE ZIP', bundle_run(RUN_DIR), flush=True)
