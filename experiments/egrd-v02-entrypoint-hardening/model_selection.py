"""Bounded diagnostic decision, never permission to dispatch a GPU Notebook."""

def decide(rows,model='12b'):
 if model not in ['12b','31b']:raise ValueError('Unknown model')
 if any(r.get('infrastructure_ok') is not True or r.get('tools_available') is not True for r in rows):return 'STOP_INFRASTRUCTURE'
 if rows and all(r.get('activation') and (r.get('evidence_records') or 0)>0 for r in rows):
  if len(rows)<2 and all(r.get('native_resolved') is False for r in rows):return 'KEEP_12B_REPAIR_FAILURE_NOT_DISQUALIFICATION' if model=='12b' else 'STOP_BOUNDED_31B_NO_MORE_GPU'
  return 'KEEP_12B' if model=='12b' else '31B_WORKFLOW_OBSERVED_NO_MORE_GPU'
 repeated=len(rows)==2 and len({r.get('task_id') for r in rows})==2 and all(r.get('model_failure') in ['MODEL_DID_NOT_CALL','INVALID_TOOL_ARGUMENTS','WORKFLOW_BREAKDOWN_CONFIRMED'] for r in rows)
 if repeated:return 'REQUEST_31B_FALLBACK_CONFIRMATION' if model=='12b' else 'STOP_ENTRYPOINT_OR_ARCHITECTURE'
 return 'INCONCLUSIVE_STOP_AT_BOUNDED_SMOKE'
