"""Mask candidate identities/outcomes before first-pass tool-action review.

Offline audit only. Not included in Agent ZIP or execution payload. The same
reviewer knows the study protocol: this is label-masked, not independently blind.
"""
import json
from pathlib import Path
import secrets
from experiments.prepare import write_new
from s1.util import save, sha_file

HERE=Path(__file__).resolve().parent


def main():
    root=HERE.parent/'_local/gpu-extract/runs'
    folders=[p for p in root.iterdir() if p.is_dir() and (p/'adk_events.jsonl').is_file()]
    assert len(folders)==2,'Require two actual traces; do not fabricate unlaunched actions'
    secrets.SystemRandom().shuffle(folders)
    mapping={}
    for label,folder in zip(('X','Y'),folders):
        pending={};rows=[]
        for line_no,line in enumerate((folder/'adk_events.jsonl').read_text().splitlines(),1):
            item=json.loads(line);event=item['event']
            for part in event.get('content',{}).get('parts',[]):
                if 'function_call' in part:
                    call=part['function_call'];key=call.get('id')
                    row=dict(index=len(rows)+1,tool=call['name'],args=call.get('args'),
                        call_time=item['recorded_monotonic'],call_line=line_no)
                    rows.append(row);pending[key]=row
                if 'function_response' in part:
                    response=part['function_response'];row=pending.get(response.get('id'))
                    assert row is not None,'Unmatched native response'
                    row.update(response=response.get('response'),response_time=item['recorded_monotonic'],response_line=line_no)
        # Remove researcher run-directory names without altering input/code/results.
        raw=json.dumps(dict(case=label,actions=rows),indent=2)
        raw=raw.replace(str(folder),'<research_run>').replace(folder.name,'<research_run>')
        write_new(HERE/'masked'/(label+'.json'),(raw+'\n').encode())
        mapping[label]=dict(run=folder.name,ADK_sha256=sha_file(folder/'adk_events.jsonl'))
    save(HERE.parent/'_local/blind_mapping.json',mapping)
    save(HERE/'masked/registration.json',dict(
        outcome_hidden=True,labels_hidden=True,model_reasoning_hidden=True,
        independent_reviewer=False,limitation='Reviewer has read protocol; identity may be inferable from timing/code. Do not claim independent double blinding.',
        files={p.name:sha_file(p) for p in (HERE/'masked').glob('*.json')}))
    print('Masked X/Y tools ready. Mapping and final native outcomes not printed.')


if __name__=='__main__': main()
