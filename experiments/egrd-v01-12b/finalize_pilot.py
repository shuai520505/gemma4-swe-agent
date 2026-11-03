"""Join mechanical extraction with explicit unblinded human review input."""
import collections,hashlib,json,zipfile
from pathlib import Path
import analyze
D=Path(__file__).resolve().parent

def main():
 analyze.main();p=D/'PILOT_METRICS.json';m=json.loads(p.read_bytes())
 reviews={r['index']:r for r in json.loads((D/'INDEPENDENT_SEMANTIC_REVIEW.json').read_bytes())['rows']}
 for s in m['sessions']:
  assert s['result']['model_transport']=='REAL_GEMMA'
  review=reviews[s['index']];assert review['evidence']['patch_sha256'] in [p['sha256'] for p in s['patches']]
  s['first_relevant_production_edit_seconds']=review['first_relevant_production_edit_seconds']
  s['first_relevant_production_edit_status']=review['first_relevant_production_edit_status']
  s['patch_correct']=review['classification']=='VALIDATED_REPAIR'
  s['issue_alignment_semantic']='FINAL_PATCH_DOES_NOT_REPAIR_ORIGINAL_PRODUCTION_BEHAVIOR' if not s['patch_correct'] else 'REVIEWED_WITH_LIMITATIONS'
 totals=collections.Counter();usage_observed=False
 for s in m['sessions']:
  u=s['result']['http_audit'].get('observed_response_usage')
  if u:totals.update(u);usage_observed=True
 before=json.loads((D/'gpu-notebook/QUOTA_IMMEDIATELY_BEFORE_DISPATCH.json').read_bytes());after=json.loads((D/'gpu-output/QUOTA_AFTER.json').read_bytes())
 with zipfile.ZipFile(D/'gpu-output/egrd-v01-12b-pilot01.zip') as z:final=json.loads(z.read('NOTEBOOK_FINAL_STATUS.json'))
 arms={}
 for arm in 'ABCD':
  rs=[s['result'] for s in m['sessions'] if s['candidate']==arm]
  arms[arm]=dict(attempted=len(rs),resolved=sum(r['native_resolved'] is True for r in rs) if rs else None)
 missing=sum(sum(r.get('usage') is None for r in s['result']['http_audit']['rows']) for s in m['sessions'])
 m['aggregate']=dict(attempted=len(m['sessions']),not_run=len(m['pilot']['not_run']),raw_SDK_resolved=arms,validated_repairs=sum(r['classification']=='VALIDATED_REPAIR' for r in reviews.values()),explicit_submits=sum(s['result']['patch_submitted'] for s in m['sessions']),EGRD_skill_calls=sum(s['ADK_tool_calls'].get('run_skill_script',0) for s in m['sessions']),EGRD_states=sum(s['EGRD'] is not None for s in m['sessions']),agent_seconds=sum(s['result']['agent_seconds'] for s in m['sessions']),charged_tools=sum(s['result']['charged_tools'] for s in m['sessions']),ADK_tool_calls=sum(s['ADK_total_tool_calls'] for s in m['sessions']),SDK_llm_counter=sum(s['result']['llm_calls'] for s in m['sessions']),HTTP_requests=sum(s['result']['http_audit']['requests'] for s in m['sessions']),HTTP_responses=sum(s['result']['http_audit']['responses'] for s in m['sessions']),observed_usage=dict(totals) if usage_observed else None,usage_complete=all(s['result']['http_audit']['usage_complete'] for s in m['sessions']),requests_unknown_usage=missing,notebook_seconds=final['elapsed_seconds'],quota_delta_seconds=after['used_seconds']-before['used_seconds'],quota_delta_hours=(after['used_seconds']-before['used_seconds'])/3600,quota_delta_scope='Observed account delta; not isolated billing attribution',model12_load_seconds=m['models']['12b'].get('MODEL_LOAD',{}).get('seconds'),model31_load_seconds=m['models']['31b'].get('MODEL_LOAD',{}).get('seconds'),model_size_latency_effect=None,EGRD_effect=None,frozen_S0_superiority=None)
 m['semantic_review']='COMPLETED_SEPARATELY_UNBLINDED';m['status']=['EGRD_PARTIALLY_IMPLEMENTED','PILOT_FAILED']
 p.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 print(json.dumps(m['aggregate'],indent=2))
if __name__=='__main__':main()
