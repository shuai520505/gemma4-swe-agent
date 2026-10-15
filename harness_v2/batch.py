"""Serial versioned development runs and pair-preserving formal batch helpers."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time

from .budgets import Budgets
from .evidence import atomic_json,read_events
from .outcomes import summarize
from .supervisor import supervise

CRITICAL=('__init__.py','budgets.py','context_budget.py','evidence.py','official.py',
          'outcomes.py','supervisor.py','windows_job.py','worker.py','batch.py')


def split_pairs(schedule):
    if len(schedule)%2: raise ValueError('A task pair is incomplete')
    pairs=[]
    for i in range(0,len(schedule),2):
        pair=schedule[i:i+2]
        if pair[0]['instance_id']!=pair[1]['instance_id'] or {r['arm'] for r in pair}!={'v0','v1'}:
            raise ValueError('Schedule must contain adjacent complete V0/V1 task pairs')
        pairs.append(pair)
    return [[r for pair in pairs[i:i+2] for r in pair] for i in range(0,len(pairs),2)]


def require_cpu_gate(gate_path,cpu_plan,source_root):
    gate=json.loads(Path(gate_path).read_text(encoding='utf-8'))
    if (gate.get('passed') is not True or gate.get('failures')!=0 or gate.get('errors')!=0 or
            gate.get('skipped')!=0 or gate.get('official_api_tests_executed') is not True):
        raise ValueError('Official CPU gate not passed; GPU is forbidden')
    expected={'swegemma':'0.2.11','adk-submission':'0.2.13','adk-eval-core':'0.1.0',
              'google-adk':'1.36.1','google-genai':'2.11.0','litellm':'1.82.4'}
    if any(gate.get('versions',{}).get(k)!=v for k,v in expected.items()):
        raise ValueError('CPU runtime versions differ from the registered official stack')
    for name in CRITICAL:
        key='harness_v2/'+name
        if cpu_plan.get('source_hashes',{}).get(key)!=hashlib.sha256((Path(source_root)/key).read_bytes()).hexdigest():
            raise ValueError(f'CPU-tested runtime changed: {key}')
    return gate


def run_batch(plan,source_root,output,paths,model,*,session_started,session_seconds=10800):
    source_root,output=Path(source_root),Path(output)
    output.mkdir(parents=True,exist_ok=False)
    budget=Budgets()
    if plan['budget']!=budget.as_dict(): raise ValueError('Common budget differs from preregistration')
    records=[]
    stop=None
    for row in plan['tasks']:
        if stop is None and session_seconds-(time.monotonic()-session_started)<budget.outer_seconds+900:
            stop='insufficient_complete_slot_and_finalization_budget'
        if stop is not None:
            record=dict(**row,status='not_run',reason=stop,official_result_present=False)
        else:
            directory=output/f"{row['index']:02d}_{row['arm']}_{row['instance_id']}"
            agent_dir=source_root/'candidates'/row['arm']/'submission'
            hashes={n:plan['source_hashes'][f"candidates/{row['arm']}/submission/{n}"]
                    for n in ('agent.yaml','eval_config.yaml','prompts/system.md')}
            spec=dict(**row,**paths,**model,agent_dir=str(agent_dir),candidate_hashes=hashes)
            spec_path=output/f"spec_{row['index']:02d}.json"
            atomic_json(spec_path,spec)
            print('START',json.dumps(row),flush=True)
            result=supervise([sys.executable,'-m','harness_v2.worker',str(spec_path),str(directory)],
                directory,outer_seconds=budget.outer_seconds,stage_caps=budget.stage_caps,cwd=source_root)
            raw_path=directory/'official_result.json'
            raw=json.loads(raw_path.read_text()) if raw_path.exists() else None
            counters=[e for e in read_events(directory/'events.jsonl') if e.get('kind')=='counters']
            latest=counters[-1] if counters else {}
            phase2=(raw or {}).get('test_output') or ''
            record=dict(**row,**result,run_directory=str(directory),official_result_present=raw is not None,
                total_llm_calls=raw.get('total_llm_calls') if raw is not None else latest.get('llm_calls'),
                tool_calls=raw.get('tool_calls') if raw is not None else latest.get('tool_calls'),
                counters_censored=raw is None,
                official_resolved=(raw or {}).get('resolved'),test_exit_code=(raw or {}).get('test_exit_code'),
                phase2_command_completed=(directory/'phase2_execution.json').exists(),
                patch_application_confirmed=bool(raw and raw.get('agent_patch') and phase2.startswith('STDOUT:\n')))
            if not result['allow_next_run'] or record['status']=='unknown':
                stop='previous_run_requires_infrastructure_audit'
            print('RESULT',json.dumps(record),flush=True)
        records.append(record)
        atomic_json(output/'audit_records.json',records)
    counts=Counter(r['arm'] for r in plan['tasks'])
    metrics=summarize(records,planned_per_arm=dict(counts))
    # Development tasks are not a prompt comparison, regardless of outcomes.
    for arm in metrics.values(): arm['resolution_rate']=None
    passed=all(r['status'] in ('resolved','failed') and r.get('allow_next_run') is True and
        r.get('phase2_command_completed') is True for r in records)
    atomic_json(output/'audit_summary.json',dict(purpose='infrastructure_development_only',arms=metrics))
    atomic_json(output/'batch_status.json',dict(harness_version='2.0.0',
        experiment_id=plan['experiment_id'],all_runs_admitted=all(r['status']!='not_run' for r in records),
        infrastructure_gate_passed=passed,stop_reason=stop,competition_score=None))
    return records
