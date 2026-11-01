"""Freeze a text-replacement design; never emit an Agent or candidate archive."""
import difflib
import hashlib
import json
from pathlib import Path
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
DESIGN = OUT / "candidate-a-design"
sha = lambda b: hashlib.sha256(b).hexdigest()
CONTROL = ROOT / "work/gemma-r12-01/candidates/R2.zip"
EXPECTED = "af918c1a65aeb211298f13a69b5b789ae6b086974922c80469df87d902eb98d5"
OLD = "- Calls 1-8: locate and read. Calls 9-12: edit. You MUST have edited a source file by call 12. If you are unsure, make your best-guess edit in the most likely place now. A wrong edit can still be corrected. Pure reading cannot score."
NEW = "- Base the first edit on evidence rather than a call number. Once you have identified the implicated production path, a concrete causal hypothesis, and one bounded discriminating counterexample or comparison supporting that hypothesis, make the smallest reversible production change as the next repair action. If the evidence is insufficient, use the next action for focused disambiguation rather than a blind edit. Then preserve the necessary focused target and regression checks."

def main():
    assert sha(CONTROL.read_bytes()) == EXPECTED
    with zipfile.ZipFile(CONTROL) as z:
        original = {n: z.read(n) for n in z.namelist()}
    prompt = original["prompts/system.md"].decode("utf8")
    assert prompt.count(OLD) == 1 and OLD in prompt.split("# CALL PLAN\n")[1].split("# PROCEDURE")[0]
    virtual = prompt.replace(OLD, NEW, 1)
    before_suffix = prompt.split("# DEADLINE-AWARE FINALIZATION", 1)[1]
    after_suffix = virtual.split("# DEADLINE-AWARE FINALIZATION", 1)[1]
    assert before_suffix == after_suffix
    assert virtual.replace(NEW, OLD, 1) == prompt
    diff = "".join(difflib.unified_diff(prompt.splitlines(True), virtual.splitlines(True), fromfile="frozen-R2/prompts/system.md", tofile="DESIGN-ONLY-Candidate-A/prompts/system.md", n=3))
    assert sum(l.startswith("-") and not l.startswith("---") for l in diff.splitlines()) == 1
    assert sum(l.startswith("+") and not l.startswith("+++") for l in diff.splitlines()) == 1
    spec = {
        "status": "DESIGN_FROZEN_NOT_DISPATCH_READY",
        "name": "R2-Early-Decision", "version": 1,
        "reference_commit": "cf411e41bb58957846c8d73c4d9c96c6dcbe531f",
        "control_zip_sha256": EXPECTED,
        "control_prompt_sha256": sha(original["prompts/system.md"]),
        "target": "prompts/system.md: first CALL PLAN bullet",
        "replacement_count": 1, "old_exact": OLD, "new_exact": NEW,
        "virtual_prompt_sha256": sha(virtual.encode("utf8")),
        "unchanged_R2_suffix_sha256": sha(before_suffix.encode("utf8")),
        "unchanged_nonprompt_members": {n: sha(b) for n,b in original.items() if n != "prompts/system.md"},
        "diff_sha256": sha(diff.encode("utf8")),
        "model": "gemma-4-31b-it-qat-w4a16-ct",
        "agent_seconds": 480, "charged_tools": 28, "max_turns": 80,
        "command_timeout_seconds": 240,
        "all_other_prompt_and_model_tool_sampling_runtime_settings": "EXACT_CONTROL_UNCHANGED",
        "candidate_zip_created": False, "agent_yaml_created": False,
        "candidate_B_included": False, "R3_created": False,
        "compile_status": "NOT_RUN_NO_AGENT_PACKAGE_CREATED",
        "prospective_tasks": None, "ordering_seed": None,
        "native_endpoint_ready": None,
        "known_inherited_conflicts": [
            "Search returned nothing: try one different specific string, then edit your best candidate anyway.",
            "Other CALL PLAN ranges, ambiguous-issue and nonempty-patch rules remain unchanged; they may compete with evidence gating."
        ],
        "conflict_policy": "Disclose and measure nonadherence; no second prompt edit or post-hoc repair of this version. Any later change needs a new preregistration before observations.",
        "benefit_seconds": None, "benefit_tokens": None,
        "benefit_status": "UNTESTED_HYPOTHESIS"
    }
    DESIGN.mkdir(exist_ok=True)
    (DESIGN / "CANDIDATE_A_POLICY_SPEC.json").write_text(json.dumps(spec,indent=2)+"\n",encoding="utf8")
    (DESIGN / "CANDIDATE_A_PROMPT_REPLACEMENT.diff").write_text(diff,encoding="utf8")
    checks = {
        "status": "PASS_DESIGN_IDENTITY_ONLY", "control_archive_unchanged": sha(CONTROL.read_bytes()) == EXPECTED,
        "one_removed_one_added_bullet": True, "all_other_prompt_bytes_preserved": True,
        "six_R2_rules_preserved": before_suffix == after_suffix,
        "original_members": {n: sha(b) for n,b in original.items()},
        "spec_sha256": sha((DESIGN / "CANDIDATE_A_POLICY_SPEC.json").read_bytes()),
        "compiler": "NOT_RUN", "native_evaluation": "NOT_RUN", "model_benefit": "UNKNOWN",
        "candidate_archive_written": False, "GPU_requests": 0,
        "scope": "Text replacement applied in CPU memory only; not an executable Agent, compiler pass or model experiment."
    }
    (DESIGN / "CPU_DESIGN_IDENTITY_CHECK.json").write_text(json.dumps(checks,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"status": checks["status"], "spec_sha256": checks["spec_sha256"], "virtual_prompt_sha256": spec["virtual_prompt_sha256"]}))

if __name__ == "__main__":
    main()
