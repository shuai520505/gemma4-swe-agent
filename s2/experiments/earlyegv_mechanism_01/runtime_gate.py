"""Execution admission only; never chooses repair actions or changes candidates."""
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import time


def admit(source, output, session_started, authorization):
    from harness_v2.evidence import atomic_json
    from s1.window import SessionWindow
    # Inspect assigned hardware before importing a framework that may allocate it.
    hardware = subprocess.run(['nvidia-smi', '--query-gpu=index,name,uuid,memory.total,driver_version',
                               '--format=csv,noheader'], capture_output=True, text=True, check=True, timeout=30)
    (output / 'nvidia_smi_devices.txt').write_text(hardware.stdout + hardware.stderr)
    processes = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,process_name', '--format=csv,noheader'],
                              capture_output=True, text=True, check=True, timeout=30)
    (output / 'nvidia_smi_before_framework.txt').write_text(processes.stdout + processes.stderr)
    assert not processes.stdout.strip(), 'Pre-existing GPU compute processes; do not start model'
    names = [line.split(',')[1].strip() for line in hardware.stdout.splitlines() if line.strip()]
    assert len(names) == 4 and all(name == 'NVIDIA L4' for name in names), names
    import torch
    assert torch.cuda.device_count() == 4
    assert all(torch.cuda.get_device_name(i) == 'NVIDIA L4' for i in range(4))
    versions = {name: importlib.metadata.version(name) for name in
                ('swegemma', 'adk-submission', 'google-adk', 'google-genai', 'litellm', 'pytest', 'vllm')}
    expected = {'swegemma': '0.2.11', 'adk-submission': '0.2.13', 'google-adk': '1.36.1',
                'google-genai': '2.11.0', 'litellm': '1.82.4', 'pytest': '8.4.2'}
    assert all(versions[name] == value for name, value in expected.items()), versions
    assert authorization['requested_notebook_window_seconds'] == 10000
    assert authorization['requested_machine_shape'] == 'NvidiaL4'
    # The successful SaveKernel request is the platform's acceptance of this
    # explicit timeout contract. Read-only status responses do not echo it.
    # Additionally reject a smaller numeric timeout if the runtime exposes one.
    exposed = {}
    for key in ('KAGGLE_KERNEL_TIMEOUT_SECONDS', 'KAGGLE_SESSION_TIMEOUT_SECONDS'):
        value = os.environ.get(key)
        if value is not None:
            assert value.isdigit() and int(value) >= 10000, (key, value)
            exposed[key] = value
    assert authorization['prelaunch_resource_admission']['quota_passed']
    assert float(authorization['prelaunch_resource_admission']['remaining_reported_seconds']) >= 20600
    window = SessionWindow(session_started, limit_seconds=10000, finalization_seconds=900)
    # Still reserve both 300s clean baseline checks before the frozen coordinator
    # reserves startup + all four worker slots after hashing.
    full = window.admission(600 + 1200 + 4 * (1550 + 60))
    evidence = dict(passed=full['allow'], hardware_names=names, actual_devices=4, TP=4,
                    torch_cuda=torch.version.cuda, torch=torch.__version__, versions=versions,
                    window=full, requested_window_seconds=10000,
                    timeout_basis='Explicit SaveKernel session_timeout_seconds=10000 accepted by running saved version; API does not independently echo an approved timeout.',
                    exposed_timeout_fields=exposed,
                    account_conflict_basis='Assigned isolated GPU devices have no existing compute processes; recent saved sessions terminal, reservation zero before save.',
                    model_inference_started=False, monotonic=time.monotonic())
    atomic_json(output / 'gpu_runtime_admission.json', evidence)
    assert full['allow'], 'Insufficient remaining full four-run window before baselines'
    result = dict(authorization)
    result['fresh_quota_and_machine_admission_verified'] = True
    atomic_json(output / 'effective_execution_authorization.json', result)
    return result
