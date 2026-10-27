"""Compare captured HTTP bodies, never estimate tokens from bytes."""
import copy
import difflib
import json

from egrd.v031.prepare import sha


def compare(raw_a, raw_b, issue, supplement):
    a, b = json.loads(raw_a), json.loads(raw_b)
    fixed = copy.deepcopy(b)
    occurrences = 0
    for message in fixed['messages']:
        if isinstance(message.get('content'), str):
            occurrences += message['content'].count(supplement)
            message['content'] = message['content'].replace(supplement, '')
    text_a = '\n'.join(str(m.get('content', '')) for m in a['messages'])
    text_b = '\n'.join(str(m.get('content', '')) for m in b['messages'])
    marker = '<EGRD_DEVELOPMENT_OBSERVATION>'
    audit = dict(original_issue_exact=issue in text_a and issue in text_b,
        only_B_has_receipt=marker not in text_a and supplement in text_b,
        supplement_occurrences=occurrences,
        instructions_equal=[m for m in a['messages'] if m['role']=='system']==[m for m in b['messages'] if m['role']=='system'],
        tools_equal=a.get('tools')==b.get('tools'),
        parameters_equal={k:v for k,v in a.items() if k not in ('messages','tools')}=={k:v for k,v in b.items() if k not in ('messages','tools')},
        ordering_and_roles_equal=[m['role'] for m in a['messages']]==[m['role'] for m in b['messages']],
        only_supplement_differs=occurrences==1 and fixed==a,
        raw_request_bytes={'A':len(raw_a),'B':len(raw_b)},
        raw_request_sha256={'A':sha(raw_a),'B':sha(raw_b)},
        supplement_bytes=len(supplement.encode()),token_overhead=None,
        token_overhead_status='UNKNOWN_NO_EXACT_TOKENIZER_TEMPLATE',
        context_policy='Unmodified S0 and native Runner; no research Guard/compaction override',
        differing_top_level_fields=[k for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)])
    diff='\n'.join(difflib.unified_diff(json.dumps(a,indent=2,ensure_ascii=False).splitlines(),
         json.dumps(b,indent=2,ensure_ascii=False).splitlines(),fromfile='A',tofile='B'))
    audit['private_full_diff_sha256']=sha(diff.encode())
    return audit, diff
