import argparse,json
p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--state');p.add_argument('--workspace');a=p.parse_args();r=json.loads(a.request)
print(json.dumps(dict(schema='EGRD_V01',status='ADVISORY_CONTROL',result=dict(id='UNVERIFIED',verification='UNKNOWN',op=r.get('op')),global_tool_gate=False,global_submit_gate=False,native_resolved=None,guidance='Use the original Issue and normal official tools; no execution or evidence attestation was performed.')))
