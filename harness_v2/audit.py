"""Audit real CPU/GPU evidence ZIPs without mutating their native contents."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

from experiments.prepare import ROOT,write_new
from .integrity import verify_baseline
from .outcomes import normalize


def journal_rows(data):
    """A final interrupted append is evidence of a gap, not a lost whole trace."""
    lines=data.splitlines()
    rows=[]
    for index,line in enumerate(lines):
        try:
            rows.append(json.loads(line))
        except (ValueError,UnicodeDecodeError):
            if index!=len(lines)-1: raise
            return rows,True
    return rows,False


def audit(archive,revision,kind):
    archive=Path(archive)
    registered=json.loads((ROOT/'harness_v2/registrations'/f'{revision}.json').read_text())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None,'ZIP CRC failure'
        names=[i.filename for i in z.infolist() if not i.is_dir()]
        assert len(names)==len(set(names)),'Duplicate evidence member'
        files={n:z.read(n) for n in names}
    actual=json.loads(files['source/infra_plan.json'])
    assert actual==registered,'Actual plan differs from registration'
    for name,digest in registered['source_hashes'].items():
        assert hashlib.sha256(files['source/'+name]).hexdigest()==digest,f'Source changed: {name}'
    if 'evidence_manifest.json' in files:
        manifest=json.loads(files['evidence_manifest.json'])
        for name,entry in manifest.items():
            assert hashlib.sha256(files[name]).hexdigest()==entry['sha256'],f'Manifest mismatch: {name}'
    record=dict(kind=kind,revision=revision,run_id=archive.stem,
        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),archive_bytes=archive.stat().st_size,
        archive_crc_pass=True,registered_sources_verified=len(registered['source_hashes']),
        original_baseline_files_preserved=verify_baseline(),competition_score=None)
    if kind=='cpu':
        record['cpu_gate']=json.loads(files['validation/cpu_gate.json'])
    else:
        record['gpu_probe']=json.loads(files['gpu_probe.json']) if 'gpu_probe.json' in files else None
        rows=json.loads(files.get('runs/audit_records.json',b'[]'))
        # A failed model/bootstrap probe can precede batch creation entirely.
        # Keep the preassigned tasks visible without inventing task verdicts.
        recorded={(r['instance_id'],r['arm']) for r in rows}
        for planned in registered['tasks']:
            if (planned['instance_id'],planned['arm']) not in recorded:
                rows.append(dict(**planned,status='not_run',reason='no_admission_record'))
        record['batch_status']=json.loads(files['runs/batch_status.json']) if 'runs/batch_status.json' in files else None
        record['exception']=json.loads(files['exception.json']) if 'exception.json' in files else None
        checks=[]
        for row in rows:
            if row['status']=='not_run':
                checks.append(dict(instance_id=row['instance_id'],arm=row['arm'],status='not_run',reason=row.get('reason')))
                continue
            prefix='runs/'+Path(row['run_directory']).name+'/'
            raw_name=prefix+'official_result.json'
            raw=json.loads(files[raw_name]) if raw_name in files else None
            expected=normalize(raw,started=True,stage=row.get('failure_stage'))
            assert expected['status']==row['status'],'Normalized result changed'
            admissions=[]
            truncated=False
            if prefix+'events.jsonl' in files:
                events,truncated=journal_rows(files[prefix+'events.jsonl'])
                admissions=[e for e in events if e.get('kind')=='context_admission']
                for event in admissions:
                    if event['decision']=='allow':
                        assert event['input_tokens']+event['output_reserved']+event['safety_tokens']<=event['max_model_len']
            else: events=[]
            check=dict(instance_id=row['instance_id'],arm=row['arm'],status=row['status'],
                failure_stage=row.get('failure_stage'),controller_error=row.get('controller_error'),
                official_result_present=raw is not None,official_result_sha256=hashlib.sha256(files[raw_name]).hexdigest() if raw is not None else None,
                official_resolved=(raw or {}).get('resolved'),test_exit_code=(raw or {}).get('test_exit_code'),
                llm_calls=row.get('total_llm_calls'),tool_calls=row.get('tool_calls'),
                counters_censored=row.get('counters_censored'),duration_seconds=row.get('duration_seconds'),
                process_tree_stopped=row.get('process_tree_stopped'),cleanup_complete=row.get('cleanup_complete'),
                context_admissions=len(admissions),rejected_requests=sum(e['decision']=='reject' for e in admissions),
                counting_errors=sum(e['decision']=='count_error' for e in admissions),
                all_allowed_requests_within_capacity=True if any(e['decision']=='allow' for e in admissions) else None,
                journal_final_append_incomplete=truncated,
                incremental_events=prefix+'adk_events.jsonl' in files,
                native_agent_trace=prefix+'agent_boundary_trace_legacy.json' in files,
                phase2_execution=prefix+'phase2_execution.json' in files)
            for name,data in files.items():
                if name.startswith(prefix+'patches/') and name.endswith('.patch'):
                    assert hashlib.sha256(data).hexdigest()==Path(name).stem,'Patch checkpoint changed'
            trace_name=prefix+'agent_boundary_trace_legacy.json'
            if trace_name in files:
                entries=json.loads(files[trace_name])['entries']
                prompt=files[f"source/candidates/{row['arm']}/submission/prompts/system.md"].decode().replace('\r\n','\n').strip()
                prompts=[e.get('content','').replace('\r\n','\n').strip() for e in entries if e['type']=='system_instruction']
                models=sorted({e['model'] for e in entries if e.get('model')})
                check.update(frozen_prompt_matches=prompt in prompts,observed_models=models,
                    required_model_only=bool(models) and all('gemma-4-31b-it-qat-w4a16-ct' in m and m.endswith('/2') for m in models))
            if raw is not None:
                patch=(raw.get('agent_patch') or '').encode()
                check['official_patch_bytes']=len(patch)
                check['official_patch_checkpoint_present']=prefix+'patches/'+hashlib.sha256(patch).hexdigest()+'.patch' in files
                phase2_starts=[e['recorded_monotonic'] for e in events if e.get('kind')=='sandbox_command_start' and e.get('command_kind')=='pytest']
                patch_writes=[e['recorded_monotonic'] for e in events if e.get('kind')=='patch' and e.get('bytes',0)>0]
                check['nonempty_patch_saved_before_phase2']=bool(phase2_starts and patch_writes and min(patch_writes)<min(phase2_starts))
                check['official_error']=raw.get('error_message') or raw.get('error')
            checks.append(check)
        record['runs']=checks
        record['status_counts']=dict(Counter(r['status'] for r in checks))
        probe=record['gpu_probe'] or {}
        record['development_infrastructure_gate_passed']=bool(
            (record['batch_status'] or {}).get('infrastructure_gate_passed') is True and
            probe.get('input_tokens') is not None and probe.get('input_tokens')==probe.get('tokenizer_input_tokens') and
            probe.get('oversize_rejected_before_generation') is True and
            len(checks)==len(registered['tasks']) and all(
                r['status'] in ('resolved','failed') and r.get('frozen_prompt_matches') is True and
                r.get('required_model_only') is True and r.get('phase2_execution') is True and
                r.get('process_tree_stopped') is True and r.get('cleanup_complete') is True and
                r.get('official_patch_checkpoint_present') is True and r.get('counting_errors')==0
                for r in checks))
        record['formal_resolution_rate']=None
        record['development_only']=True
    target=ROOT/'harness_v2/results'/f'{revision}-{kind}-audit.json'
    write_new(target,(json.dumps(record,indent=2)+'\n').encode())
    return record


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('archive',type=Path)
    p.add_argument('revision'); p.add_argument('kind',choices=['cpu','gpu'])
    a=p.parse_args(); print(json.dumps(audit(a.archive,a.revision,a.kind),indent=2))
