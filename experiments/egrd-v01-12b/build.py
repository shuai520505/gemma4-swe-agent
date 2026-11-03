"""Matched official Skill packages, one LlmAgent, immutable S0 provenance."""
import hashlib,io,json,zipfile
from pathlib import Path
D=Path(__file__).resolve().parent
BASE_PROMPT=D/'inputs/s0/system.md'
TOOLS=['get_status','run_command','read_file','edit_file','write_file','submit_patch']
MODELS={'12b':dict(alias='gemma-4-12b-it-qat-w4a16-ct',mount='google/gemma-4/Other/gemma-4-12b-it-qat-w4a16-ct/2',extra_args=['--hf-overrides','{"architectures": ["Gemma4ForCausalLM"], "model_type": "gemma4"}']),
 '31b':dict(alias='gemma-4-31b-it-qat-w4a16-ct',mount='google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2',extra_args=[])}
SKILL='''---
name: egrd-repair
description: Source-bound local repair evidence and bounded decisions; not an evaluator or global gate.
---

Use run_skill_script(skill_name="egrd-repair", file_path="scripts/egrd.py",
args={"request": "JSON request string"}). State is /tmp/egrd-v01/state.json.
The same interface may return advisory UNKNOWN in a control experiment.
No result means Native Resolved or semantic proof. Official submit_patch is separate.

Initialize once with op=init, issue_id, original (exact supplied Issue), model_id,
requirements=[{id:R1,text:exact quote,status:OBSERVED}], and expected_behavior,
actual_behavior, inputs_outputs, boundaries, acceptance_criteria, unresolved_questions
(each a list of text/status claims). Implicit assumptions are INFERRED or UNVERIFIED.
After compaction consult this state rather than replacing the original Issue.

Operations (flat JSON fields):
- source: name,start,end,requirements. Reads bounded actual workspace source.
- hypothesis: location,mechanism,support (evidence IDs),contradictions,prediction,
  confidence,next_experiment,requirements. Semantic claims remain UNVERIFIED.
- intent: files,regions,behavior,requirements,support,regressions,preserve,
  discriminating_test. Then use the normal official edit_file, not this Skill, to edit.
- record_patch: observe actual differences and flag files outside the intent.
- check: path (assertion script under /tmp),requirements,purpose TARGET or REGRESSION,
  seconds (at most15). Obtain fresh executed assertions after production edits.
- review: inspect actual diff. accept: local evidence gate, never the official scorer.
- revise: bounded revision count. rollback: explicit restoration of only intent files.
- action: kind,signature,justification (optional),duration (optional observed duration).
- next: advisory next action; bypass remains possible through official tools.

Avoid bureaucracy: one concise hypothesis/intent, one discriminating target and
necessary regression checks. When the interface is unavailable, report UNKNOWN
and use the normal tools. Do not spend the submission reserve filling in records.
'''
COMMON='''\n\nEGRD research interface: the official egrd-repair Skill is available. Initialize
it once with the exact supplied Issue and quoted requirements; use it for a concise
source-grounded hypothesis and intent, then actual official edits and targeted checks.
Consult get_status at strategy changes. The Skill clock starts late and is not the
official session clock. Keep25 seconds for diff review and submit_patch. Treat every
semantic link as a hypothesis; reject unrelated changes and contradictory checks.
The matched control may return UNKNOWN/advisory evidence; never invent observations.
Do not add another model/Agent, use graph tools or hidden evaluator information.
'''
CONTROL='''import argparse,json
p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--state');p.add_argument('--workspace');a=p.parse_args();r=json.loads(a.request)
print(json.dumps(dict(schema='EGRD_V01',status='ADVISORY_CONTROL',result=dict(id='UNVERIFIED',verification='UNKNOWN',op=r.get('op')),global_tool_gate=False,global_submit_gate=False,native_resolved=None,guidance='Use the original Issue and normal official tools; no execution or evidence attestation was performed.')))
'''
def digest(b):return hashlib.sha256(b).hexdigest()
def script():
    meer=(D/'meer_verifier.py').read_text(encoding='utf8').split("if __name__ == '__main__':")[0].replace('def main():','def meer_main():')
    core=(D/'core.py').read_text(encoding='utf8').replace('from meer_verifier import tree_identity,verify','')
    cli=(D/'skill_cli.py').read_text(encoding='utf8').replace('from core import RepairState','')
    result=meer+'\n'+core+'\n'+cli;compile(result,'egrd-bundle','exec');return result
def build():
    assert digest(BASE_PROMPT.read_bytes())=='5f43c3a546c4c21765aff5e09a92126b1bb104b6e8423b269364a0b8f286a7ce','Frozen S0 prompt identity mismatch'
    rows={};(D/'configs').mkdir(exist_ok=True)
    for model,config in MODELS.items():(D/'configs'/f'{model}.json').write_text(json.dumps(dict(config,context_limit=32768,max_output_tokens=8192,thinking_budget=4096,temperature=.2,top_p=.95,session_seconds=300,command_seconds=120,tool_calls=60,turns=80),indent=2)+'\n')
    for arm,model,active in [('A','12b',False),('B','12b',True),('C','31b',False),('D','31b',True)]:
        config=MODELS[model]
        agent='agent_class: LlmAgent\nname: egrd_main\nmodel: '+config['alias']+'\ninstruction: !include prompts/system.md\ntools:\n'+''.join('  - '+t+'\n' for t in TOOLS)+'skills:\n  - skills/egrd-repair\ngenerate_content_config:\n  max_output_tokens: 8192\n  temperature: 0.2\n  top_p: 0.95\n  thinking_config:\n    thinking_budget: 4096\n    include_thoughts: true\n'
        prompt=BASE_PROMPT.read_bytes().replace(b'gemma-4-31b-it-qat-w4a16-ct',b'the declared Gemma model')+COMMON.encode()
        files={'agent.yaml':agent.encode(),'prompts/system.md':prompt,'eval_config.yaml':b'evaluation:\n  timeout_seconds: 120\n  max_tool_calls: 60\n  max_time_minutes: 5.0\n  max_turns: 80\n','skills/egrd-repair/SKILL.md':SKILL.encode(),'skills/egrd-repair/scripts/egrd.py':(script() if active else CONTROL).encode()}
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
            for n,b in sorted(files.items()):
                info=zipfile.ZipInfo(n,(2026,11,3,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,b)
                p=D/'packages'/arm/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        raw=output.getvalue();(D/'packages'/f'{arm}.zip').write_bytes(raw)
        rows[arm]=dict(model=config['alias'],active=active,sha256=digest(raw),members={n:digest(b) for n,b in files.items()})
    for x,y in [('A','B'),('C','D')]:assert {k:v for k,v in rows[x]['members'].items() if not k.endswith('/egrd.py')}=={k:v for k,v in rows[y]['members'].items() if not k.endswith('/egrd.py')}
    (D/'PACKAGE_MANIFEST.json').write_text(json.dumps(dict(arms=rows,frozen_S0_unchanged=True,baseline_definition='S0-derived matched-interface control; common prompt/interface and shared explicit generation are deviations from exact frozen S0. Separate frozen-S0 anchor remains required.',base_tools=TOOLS,official_skill_accessors=['list_skills','load_skill','load_skill_resource','run_skill_script'],extra_custom_tools=[],global_control=False),indent=2)+'\n')
    print('BUILT_MATCHED_PACKAGES')
if __name__=='__main__':build()
