"""One instruction-block replacement; reuse frozen three-member ZIP builder."""
import difflib,json,zipfile,io
from .common import HERE,ROOT,BASE,CONTROL,CONTROL_SHA,sha,write
from u_re.v01.build import archive
def build():
    original=CONTROL.parent/'submission_action_v01.zip';assert sha(original.read_bytes())==CONTROL_SHA
    with zipfile.ZipFile(original) as z:
        assert z.testzip() is None and set(z.namelist())=={'agent.yaml','eval_config.yaml','prompts/system.md'}
        files={n:z.read(n) for n in z.namelist()}
    for n,b in files.items():assert (CONTROL/n).read_bytes()==b
    before=files['prompts/system.md'];old=(CONTROL.parent/'ACTION_FIRST_INSTRUCTION_BLOCK.md').read_bytes();new=(HERE/'EGR_INSTRUCTION_BLOCK.md').read_bytes()
    assert before.count(old)==1 and b'{' not in new and b'}' not in new
    after=before.replace(old,new,1);assert after.replace(new,old,1)==before
    files['prompts/system.md']=after
    for n,b in files.items():write(HERE/'candidate_egr_v04'/n,b)
    raw=archive(files)
    path=HERE/'submission_egr_v04.zip'
    if path.exists():assert path.read_bytes()==raw,'Version a frozen candidate rather than overwrite'
    write(path,raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:assert z.testzip() is None and len(z.namelist())==3
    write(HERE/'PROMPT_EXACT.diff',''.join(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile='Frozen-ActionFirst/prompts/system.md',tofile='EGR-V04/prompts/system.md')).encode())
    lock=dict(experiment_id='U-RE-V04-EVIDENCE-GUIDED-REPAIR-01',source_base=BASE,control_ZIP_sha256=CONTROL_SHA,treatment_ZIP_sha256=sha(raw),old_block_sha256=sha(old),new_block_sha256=sha(new),control_prompt_sha256=sha(before),treatment_prompt_sha256=sha(after),control_prompt_words=len(before.decode().split()),treatment_prompt_words=len(after.decode().split()),old_block_words=len(old.decode().split()),new_block_words=len(new.decode().split()),tokens=None,token_status='NO_VERIFIED_LOCAL_GEMMA_TOKENIZER; not estimated with another tokenizer',single_factor='System instruction: replace Action-First strategy block with Evidence-Guided Repair; all other prompt bytes retained',unchanged_sections=['Opening constraints','Triage and repair','Budget and progress','Closure'],runtime_controller_added=False,evaluator_or_task_specific_content=False)
    write(HERE/'EGR_PROMPT_LOCK.json',lock)
    manifest=dict(**lock,ZIP_bytes=len(raw),members={n:sha(b) for n,b in files.items()},control_members={n:sha((CONTROL/n).read_bytes()) for n in files},changed_members=['prompts/system.md'],agent_count=1,model='gemma-4-31b-it-qat-w4a16-ct',tools=['get_status','run_command','read_file','edit_file','write_file','submit_patch'],generation=dict(max_output_tokens=16384,thinking_budget=4096,seed=17,include_thoughts='omitted',sampling='omitted'),budget=dict(context=32768,safety=1024,input_cap=15360,Agent_seconds=300,charged_tools=60,command_seconds=120),CPU_acceptance='NOT_RUN',GPU_authorized=False,formal_submission=False)
    write(HERE/'CANDIDATE_BUILD_MANIFEST.json',manifest);print(json.dumps(dict(ZIP_sha256=sha(raw),words=len(new.decode().split()),members=manifest['members'])))
    return manifest
if __name__=='__main__':build()
