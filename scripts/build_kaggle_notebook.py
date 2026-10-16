"""Build the self-contained Kaggle Notebook without executing evaluation."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SETTINGS = '''# Defaults require only the four official/user inputs to be mounted.
# Leave paths unset for automatic discovery; overrides resolve duplicate inputs.
INPUT_ROOT = Path('/kaggle/input')
WORKING_DIR = Path('/kaggle/working')
INPUT_PATHS = {'data': None, 'wheelhouse': None, 'model': None, 'zip': None}
RUN_MODE = 'single'              # First run: one public task. Optional later: 'batch'.
TASK_INSTANCE_ID = None           # None selects the first published task.
SESSION_STARTED = time.monotonic()  # Includes installation and model startup.
profile = budget_profile(RUN_MODE)
RUN_DIR = WORKING_DIR / 'v0_runs' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
RUN_DIR.mkdir(parents=True, exist_ok=False)
server_instance = None
write_json(RUN_DIR / 'run_status.json', {'stage': 'created', 'completed': False,
                                       'real_task_completed': False, 'competition_score': None})
print('Evidence directory:', RUN_DIR)
try:
    inputs = discover_inputs(INPUT_ROOT, INPUT_PATHS)
    AGENT_DIR = RUN_DIR / 'submission'
    zip_sha256 = extract_submission(inputs['zip'], AGENT_DIR)
    DATA_DIR, WHEELHOUSE_DIR, MODEL_PATH = inputs['data'], inputs['wheelhouse'], inputs['model']
    for source, target in [('HARNESS_README.md', 'HARNESS_README.md'),
                           ('sample_submission/agent.yaml', 'official_sample_agent.yaml')]:
        shutil.copyfile(DATA_DIR / source, RUN_DIR / target)
    write_json(RUN_DIR / 'manifest.json', {'model': MODEL_NAME, 'inputs': inputs,
               'submission_sha256': zip_sha256, 'profile': profile,
               'run_mode': RUN_MODE, 'official_notebook_version': 3,
               'started_utc': datetime.now(timezone.utc).isoformat(),
               'competition_score': None})
    print('Mounted inputs:', inputs)
    print('Official README and sample saved; read them and the competition rules before proceeding.')
except BaseException as exc:
    exception_record(RUN_DIR, 'inputs', exc)
    print('Diagnostics ZIP:', bundle_run(RUN_DIR))
    raise
'''

INSTALL = '''import glob
import importlib
import os
import subprocess
import sys

# Same offline routing and dependency installation as official Notebook v3.
for name, value in {
    'TRANSFORMERS_NO_TF': '1', 'TRANSFORMERS_NO_FLAX': '1', 'TRANSFORMERS_OFFLINE': '1',
    'HF_HUB_OFFLINE': '1', 'VLLM_NO_USAGE_STATS': '1', 'VLLM_WORKER_MULTIPROC_METHOD': 'spawn',
    'VLLM_ENGINE_READY_TIMEOUT_S': '1200', 'VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS': '1',
    'NCCL_DEBUG': 'WARN', 'LITELLM_LOCAL_MODEL_COST_MAP': 'True', 'LITELLM_TELEMETRY': 'False',
    'LITELLM_LOG': 'WARNING', 'PYTORCH_CUDA_ALLOC_CONF': 'expandable_segments:True',
    'OTEL_SDK_DISABLED': 'true', 'OTEL_PYTHON_DISABLED': 'true',
}.items():
    os.environ[name] = value
os.environ.setdefault('LOCAL_API_KEY', 'EMPTY')
os.environ.setdefault('OPENAI_API_KEY', 'EMPTY')
try:
    gpu_query = subprocess.run(['nvidia-smi', '--query-gpu=index,name,memory.total',
                               '--format=csv,noheader'], check=True, capture_output=True, text=True, timeout=30)
    (RUN_DIR / 'gpu.txt').write_text(gpu_query.stdout)
    print(gpu_query.stdout)
    # Official Notebook workaround for broken cutlass .pth hooks.
    for pattern in ('/usr/local/lib/python*/dist-packages/*cutlass*.pth',
                    '/usr/local/lib/python*/site-packages/*cutlass*.pth'):
        for path in glob.glob(pattern):
            Path(path).unlink(missing_ok=True)
    tmp_whl = RUN_DIR / 'wheelhouse_links'
    tmp_whl.mkdir()
    for wheel in WHEELHOUSE_DIR.glob('*.whl'):
        if 'cutlass' in wheel.name.lower():
            continue
        name = wheel.name.replace('cu128', '+cu128') if 'cu128' in wheel.name and '+' not in wheel.name else wheel.name
        (tmp_whl / name).symlink_to(wheel)
    wheels = sorted(str(p) for p in tmp_whl.glob('*.whl'))
    if not wheels:
        raise RuntimeError('Mounted official wheelhouse is empty')
    with (RUN_DIR / 'installation.log').open('w') as output:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-index', '--no-deps',
                        '--force-reinstall', *wheels], stdout=output, stderr=subprocess.STDOUT, check=True, timeout=1800)
    importlib.invalidate_caches()
    # Link staging is not an artifact; only original file names are retained.
    shutil.rmtree(tmp_whl)
    from importlib.metadata import version
    packages = {name: version(name) for name in
                ('swegemma', 'adk-submission', 'adk-eval-core', 'google-adk', 'google-genai',
                 'vllm', 'torch', 'transformers', 'litellm')}
    write_json(RUN_DIR / 'packages.json', packages)
    print('Installed official package versions:', packages)
    if any(packages[name] != expected for name, expected in {
        'swegemma': '0.2.11', 'adk-submission': '0.2.13', 'adk-eval-core': '0.1.0',
        'google-adk': '1.36.1', 'google-genai': '2.11.0'}.items()):
        raise RuntimeError('Official Harness version changed; review APIs before running')
except BaseException as exc:
    # Avoid copying wheel symlinks into a large diagnostic ZIP after install failure.
    if 'tmp_whl' in globals() and tmp_whl.exists():
        shutil.rmtree(tmp_whl)
    exception_record(RUN_DIR, 'gpu_or_installation', exc)
    print('Diagnostics ZIP:', bundle_run(RUN_DIR))
    raise
'''

PREFLIGHT = '''import inspect
import torch
from adk_submission import (VllmConfig, VllmServer, compile_submission, discover_adapters,
                            validate_directory)
from adk_submission.discovery import discover_declared_models
from adk_submission.yaml_loader import load_yaml
from swegemma.config import EvalConfig, build_submission_limits
from swegemma.context import SwegemmaContext
from swegemma.evaluate import Evaluator
from swegemma.models import load_tasks
from swegemma.deduplication import resolve_task_snapshot_paths

try:
    assert torch.cuda.is_available() and torch.cuda.device_count() > 0, 'CUDA GPU required; no CPU fallback'
    gpu_count = torch.cuda.device_count()
    tp_size = 4 if gpu_count >= 4 else (2 if gpu_count >= 2 else 1)
    assert discover_declared_models(AGENT_DIR) == {MODEL_NAME}, 'Only the required 31B model is allowed'
    adapters = discover_adapters(str(AGENT_DIR))
    assert not adapters.adapters, 'V0 must not contain LoRA adapters'
    raw_agent = load_yaml(AGENT_DIR / 'agent.yaml', AGENT_DIR)
    allowed_fields = {'agent_class', 'name', 'model', 'description', 'instruction', 'tools'}
    assert set(raw_agent) <= allowed_fields and raw_agent.get('agent_class') == 'LlmAgent'
    required_tools = {'get_status', 'run_command', 'read_file', 'edit_file', 'write_file', 'submit_patch'}
    assert set(raw_agent['tools']) == required_tools and len(raw_agent['tools']) == len(required_tools)
    assert required_tools <= SwegemmaContext().create_tools().keys()
    assert 'context' in inspect.signature(Evaluator.evaluate_task).parameters
    assert 'format' in inspect.signature(__import__('adk_eval_core.tracing', fromlist=['SessionTrace']).SessionTrace.save).parameters
    limits, constraints = build_submission_limits()
    validate_directory(AGENT_DIR, limits=limits)
    TASKS_PATH = DATA_DIR / 'tasks.jsonl'
    tasks = load_tasks(TASKS_PATH)
    assert tasks, 'No published tasks in the official input'
    if TASK_INSTANCE_ID is not None:
        selected = [t for t in tasks if t.instance_id == TASK_INSTANCE_ID]
        assert len(selected) == 1, 'TASK_INSTANCE_ID is not a unique published task'
    else:
        selected = tasks[:profile['max_tasks']]
    for task in selected:
        assert not task.repo.startswith('test/mock_repo'), 'Synthetic task cannot satisfy this run'
        snapshot, _, _ = resolve_task_snapshot_paths(DATA_DIR / 'snapshots', task.instance_id, task.repo)
        assert snapshot.is_file(), f'Missing official snapshot for {task.instance_id}'
    # Do not print gold patches or feed them to the model.
    write_json(RUN_DIR / 'selected_tasks.json', [dict(instance_id=t.instance_id, repo=t.repo,
        base_commit=t.base_commit, public_test_spec_present=bool(t.test_patch or t.FAIL_TO_PASS)) for t in selected])
    print('Selected public tasks:', [t.instance_id for t in selected])
    print('GPU count / tensor parallel:', gpu_count, tp_size)
    print('Profile:', profile)
except BaseException as exc:
    exception_record(RUN_DIR, 'harness_preflight', exc)
    print('Diagnostics ZIP:', bundle_run(RUN_DIR))
    raise
'''

SERVER = '''import urllib.request
from dataclasses import asdict

# Native Harness logs preserve ADK output/tool events while a task is running.
# No HTTP debug logging or credential/environment dumps.
handler = logging.FileHandler(RUN_DIR / 'harness.log', encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s'))
for name in ('swegemma', 'adk_submission'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
try:
    if not admission_seconds(SESSION_STARTED, profile['task_wall_minutes']):
        raise TimeoutError('Insufficient session time for model startup and a complete task slot')
    vllm_cfg = VllmConfig(model=str(MODEL_PATH), host='127.0.0.1', port=8000,
        tool_call_parser='gemma4', reasoning_parser='gemma4', max_model_len=32768,
        dtype='bfloat16' if torch.cuda.is_bf16_supported() else 'auto',
        gpu_memory_utilization=0.90, enable_auto_tool_choice=True, enable_lora=False,
        scheduler_reserve_full_isl=False, tensor_parallel_size=tp_size, startup_timeout=1200)
    write_json(RUN_DIR / 'vllm_config.json', asdict(vllm_cfg))
    server_instance = VllmServer(vllm_cfg, adapter_manifest=adapters)
    server_instance.start()
    preserve_server_log(server_instance, RUN_DIR)
    key = os.environ['LOCAL_API_KEY']
    request = urllib.request.Request(server_instance.base_url + '/models',
                                     headers={'Authorization': 'Bearer ' + key})
    with urllib.request.urlopen(request, timeout=30) as response:
        served = json.load(response)
    write_json(RUN_DIR / 'served_models.json', served)
    assert any(item.get('id') in (str(MODEL_PATH), MODEL_NAME) for item in served.get('data', [])), 'Unexpected served model'
    models = server_instance.create_model_registry(aliases=[MODEL_NAME], model_prefix='openai/', api_key=key)
    compiled = compile_submission(AGENT_DIR, SwegemmaContext().create_tools(), models,
                                 limits=limits, generation_constraints=constraints)
    assert not compiled.sub_agents
    write_json(RUN_DIR / 'run_status.json', {'stage': 'model_ready', 'completed': False,
               'real_task_completed': False, 'competition_score': None})
    print('Official server and compiler ready; no task inference has run yet.')
except BaseException as exc:
    exception_record(RUN_DIR, 'vllm_startup_or_compile', exc)
    # VllmServer.start() deletes its temporary log on failure; output contains its captured log.
    if getattr(exc, 'output', None):
        (RUN_DIR / 'vllm_startup_failure.log').write_text(str(exc.output))
    if server_instance is not None:
        preserve_server_log(server_instance, RUN_DIR)
        server_instance.stop()
    handler.flush()
    print('Diagnostics ZIP:', bundle_run(RUN_DIR))
    raise
'''

EVALUATE = '''from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps._configs import EventsCompactionConfig

records = []
try:
    # Public local profile overrides only; the uploaded submission remains unchanged.
    eval_config = EvalConfig(tasks_path=TASKS_PATH, snapshots_dir=DATA_DIR / 'snapshots',
        results_dir=RUN_DIR / 'harness', submission_dir=AGENT_DIR, models=models,
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
    evaluator = Evaluator(eval_config)
    for index, task in enumerate(selected, 1):
        slot = admission_seconds(SESSION_STARTED, profile['task_wall_minutes'])
        if slot == 0:
            write_json(RUN_DIR / 'budget_stop.json', {'reason': '705-minute admission deadline',
                       'unrun_task_ids': [t.instance_id for t in selected[index - 1:]]})
            break
        task_dir = RUN_DIR / 'tasks' / f'{index:03d}'
        context = SwegemmaContext(docker_manager=evaluator.docker, task=task,
                  graph_dir=eval_config.graph_dir, embeddings_dir=eval_config.embeddings_dir,
                  budget=eval_config.budget, harness=eval_config.harness)
        print(f'[{index}/{len(selected)}] {task.instance_id}: real Gemma Phase 1 + official Phase 2')
        record = await evaluate_with_deadline(evaluator, task, context, task_dir, slot, server_instance)
        records.append(record)
        write_json(RUN_DIR / 'public_results.json', records)
        print(json.dumps(record, indent=2))
        if not record['first_task_goal_completed']:
            # Diagnose this run before expanding to more tasks.
            raise RuntimeError('Task did not produce complete inference/submit/Phase 2 evidence; inspect task artifacts')
    write_json(RUN_DIR / 'run_status.json', {'stage': 'finished', 'completed': True,
        'real_task_completed': any(r['first_task_goal_completed'] for r in records),
        'tasks_finished': len(records), 'competition_score': None})
finally:
    # Copy BEFORE stop(): the official server deletes its temporary log on stop.
    if server_instance is not None:
        preserve_server_log(server_instance, RUN_DIR)
        server_instance.stop()
    handler.flush()
    handler.close()
    for name in ('swegemma', 'adk_submission'):
        logging.getLogger(name).removeHandler(handler)
    print('Download complete evidence ZIP:', bundle_run(RUN_DIR))
'''
# Catch evaluation exceptions as well as timeout/cancellation in the support helper.
EVALUATE = EVALUATE.replace('finally:\n    # Copy', '''except BaseException as exc:
    exception_record(RUN_DIR, 'evaluation', exc)
    write_json(RUN_DIR / 'run_status.json', {'stage': 'failed', 'completed': False,
        'real_task_completed': any(r['first_task_goal_completed'] for r in records),
        'tasks_finished': len(records), 'competition_score': None})
    raise
finally:
    # Copy''')


# Include import errors in stage diagnostics; optional API drift can fail at import.
_prefix, _body = PREFLIGHT.split('try:\n', 1)
PREFLIGHT = 'try:\n' + ''.join('    ' + line + '\n' for line in _prefix.splitlines()) + _body
_prefix, _body = EVALUATE.split('records = []\ntry:\n', 1)
EVALUATE = 'records = []\ntry:\n' + ''.join('    ' + line + '\n' for line in _prefix.splitlines()) + _body


def build():
    helper = (ROOT / 'notebooks/kaggle_support.py').read_text()
    sections = [
        ('# V0：Gemma 4 官方环境单题实测\n\n默认仅跑一道公开任务。挂载比赛数据、官方 wheelhouse、31B 模型和本仓库 submission.zip，逐个运行单元。无需 GitHub 仓库挂载或额外工具。\n\n401 属于账号授权问题：在 Kaggle 登录、接受规则并挂载官方输入；本 Notebook 不调用比赛下载 API。使用支持该模型的 GPU（优先官方 4×L4 环境），Internet 关闭。\n\n来源：官方 Getting Started v3；此文件执行计数为空，表示未在 Kaggle 执行。https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent', None),
        ('## 1. 日志与结果辅助函数（仅运行控制，无 Agent 工具）', helper),
        ('## 2. 自动发现输入并建立独立证据目录\n\n先在 Kaggle 阅读完整规则与 HARNESS_README。可选 TASK_INSTANCE_ID 指定公开任务；默认自动选第一题。', SETTINGS),
        ('## 3. GPU 与官方离线 wheelhouse 安装', INSTALL),
        ('## 4. 官方 API、模型、工具与公开任务快照检查\n\nV0 不调用图工具，不执行图检索演示。图/embedding 输入仅传给官方 Harness。', PREFLIGHT),
        ('## 5. 启动指定 31B vLLM，检查本地模型路由并编译\n\n这一步仅验证服务和配置；不是修复评测。', SERVER),
        ('## 6. 一道真实公开任务：Gemma 推理 → submit_patch → Phase 2\n\n结果按 task 保存；finally 自动复制 vLLM 日志、停止服务并打包证据。中断/超时不能视为通过。', EVALUATE),
        ('## 7. 下载并审查证据\n\n从 Notebook Output 下载 v0_runs 下的运行 ZIP。检查 tasks/001/result.json、agent.patch、phase2.log、trace.json、trace_legacy.json、model_events.jsonl、tool_events.jsonl，以及 harness/logs 和 vllm.log。模型事件是官方 ADK Trace 中的输出/usage；不是逐次 HTTP 原始请求抓包。\n\nfirst_task_goal_completed 只表示有推理、显式提交与 Phase 2 执行证据。是否修复以官方 resolved 与验证日志判断；competition_score 始终为空，不声称排行榜分数。若缺少 Phase 2 测试规格，检查官方授权数据输入，不能补造测试。\n\n首次单题完成后才将 RUN_MODE 改为 batch。默认串行最多50题、Phase 1每题8分钟、工具60次、单命令120秒、验证300秒、每题外层12分钟；50×12+安装启动45+结束15=660分钟。实际开销不是保证值，705分钟后不接纳新题，保留15分钟退出。若底层同步操作不响应取消，需在 Kaggle 停止运行；最终12小时硬上限由平台执行。被跳过/取消的题目没有得分。', None),
    ]
    cells = []
    for heading, code in sections:
        cells.append({'cell_type': 'markdown', 'id': hashlib.sha256(heading.encode()).hexdigest()[:12],
                      'metadata': {}, 'source': heading})
        if code:
            # Top-level await is valid in Kaggle/Jupyter, not a shell Python script.
            compile(code, '<notebook>', 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
            cells.append({'cell_type': 'code', 'id': hashlib.sha256(code.encode()).hexdigest()[:12],
                          'metadata': {}, 'source': code,
                          'execution_count': None, 'outputs': []})
    return dict(cells=cells, metadata={'kernelspec': {'display_name': 'Python 3',
           'language': 'python', 'name': 'python3'}, 'language_info': {'name': 'python'}},
           nbformat=4, nbformat_minor=5)


if __name__ == '__main__':
    (ROOT / 'notebooks/v0_official.ipynb').write_text(json.dumps(build(), indent=1) + '\n')
