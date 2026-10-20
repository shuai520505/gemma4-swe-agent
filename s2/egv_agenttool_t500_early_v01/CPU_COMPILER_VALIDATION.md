# Official Compiler acceptance

CPU02 version1 completed the full135-test acceptance; CPU01's real Test A error is retained separately. See results/cpu02/validation/compiler_gate.json, cpu_gate.json, versions.json and cpu.log. Official packages:swegemma0.2.11,adk-submission0.2.13,ADK1.36.1,google-genai2.11.0,LiteLLM1.82.4,pytest8.4.2; image and wheel hashes are in frozen Notebook metadata/registrations.

The actual official Compiler validates the extracted five-member submission ZIP. Root agent.yaml loads Main and the unchanged AgentTool config_path/child instruction. Main and child instructions equal source text exactly. Main has six organizer tools plus AgentTool schema; child has get_status/read_file/run_command. Same31B model and frozen generation configuration; public EvalConfig parses500.00000000000006seconds,60 charged tools,120-second command timeout.

Empty-State actual ADK Runner pre-processes the complete Main/child instructions and reaches mocked HTTP. Each observed Main/child System Instruction is checked against its complete source. A new Session starts empty; child output_key legitimately adds egv_latest_report after delegation. No instruction-template braces added. The native synthetic repair Patch is captured by the real submit_patch interface, not a mock text claim. No research Python, test, reference repair or Trace is present in submission.zip.

Candidate ZIP SHAd1e815e770abbcc448325ad2a3c8785c62f6d3c63bc7f95700850748c048a487; only prompts/main.md differs from frozen T500. CPU02 rawSHA45e679db5454bf5e62e95baeba56d5d1bbcbc8d4165d905d442aeca00c840355,1585manifest files,CRC and all digests verified. Official CPU compatibility is not real-Gemma inference or a guarantee of private scoring-stage behavior; no new formal submission was made.
