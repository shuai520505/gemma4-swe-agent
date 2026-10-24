# Observable repair timelines

All times below are seconds from the archived Agent start. Tool completion bounds the edit time; it is not an instruction-level clock. Event indices are zero-based ADK JSONL row indices. Full public event hashes are in TRAJECTORY_DATASET.json. Raw commands, patches and test text remain private.

## GPU03/01-fastapi_9425-A

Source `72030f1833ee6a8588087836bf281ae3aafae4c5a327b4f1d5651482aed7bea6` / `results/runs/01-fastapi_9425-A/agent/adk_events.jsonl`; trace SHA `43f51f6df6e0c2a950a292712a71c2f5bc0b037a99ac62795190b936d5e93a31`. Candidate ZIP `2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608`.

Relevant inspection: 42.84116936200007 (e18); first observed file edit: None; first behavioral edit: None (eNone). Checks: [32, 36, 44]. All subsequent edit acknowledgements: [].

Native raw=False, assessed=False (NATIVE_RESULT_OBSERVED); submits=0; post-submit tools=None; stop=CONTEXT_RESERVATION_STOP. Model requests=26; received usage={'prompt_tokens': 170535, 'completion_tokens': 8730, 'total_tokens': 179265}; tools=26; Agent seconds=264.2835607799998.

e30/32 reproduction tests a neighboring annotation case, not the stringified case in the Issue; no production edit before guard.

## GPU03/02-fastapi_9425-B

Source `72030f1833ee6a8588087836bf281ae3aafae4c5a327b4f1d5651482aed7bea6` / `results/runs/02-fastapi_9425-B/agent/adk_events.jsonl`; trace SHA `5ece2d141f2f08f905ca4dbae4afcc8616d74949e03f78e1ddb79aad7e324da8`. Candidate ZIP `70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8`.

Relevant inspection: 34.187445492999814 (e20); first observed file edit: 138.952519509; first behavioral edit: 139.005810784 (e43). Checks: [28, 36, 39, 45, 51, 55, 59]. All subsequent edit acknowledgements: [{'event_index': 43, 'seconds': 139.005810784, 'basis': ['source_boundary_hash_change']}].

Native raw=True, assessed=True (NATIVE_RESULT_OBSERVED); submits=1; post-submit tools=0; stop=None. Model requests=39; received usage={'prompt_tokens': 363210, 'completion_tokens': 6949, 'total_tokens': 370159}; tools=37; Agent seconds=229.72936826.

e26/28 distinguishes annotation representations; e43 edits; e45/e51 check changed behavior; e73 submits. Native passes.

## GPU03/03-fastapi_14786-B

Source `72030f1833ee6a8588087836bf281ae3aafae4c5a327b4f1d5651482aed7bea6` / `results/runs/03-fastapi_14786-B/agent/adk_events.jsonl`; trace SHA `738b0a0965b06540a78a393637a02ff4bfb9792fef3c67bac9ecdec348900e44`. Candidate ZIP `70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8`.

Relevant inspection: 7.3068977059999725 (e2); first observed file edit: 30.34073965599987; first behavioral edit: 30.391664900000023 (e8). Checks: [6, 10, 12, 22, 24]. All subsequent edit acknowledgements: [{'event_index': 8, 'seconds': 30.391664900000023, 'basis': ['source_boundary_hash_change']}].

Native raw=True, assessed=True (NATIVE_RESULT_OBSERVED); submits=1; post-submit tools=0; stop=None. Model requests=17; received usage={'prompt_tokens': 122146, 'completion_tokens': 1922, 'total_tokens': 124068}; tools=16; Agent seconds=79.08459343999994.

e6 fails an assertion, e8 edits, e10 passes the same check. Later unscoped pytest and nonexistent path are unnecessary detours, despite native success.

## GPU03/04-fastapi_14786-A

Source `72030f1833ee6a8588087836bf281ae3aafae4c5a327b4f1d5651482aed7bea6` / `results/runs/04-fastapi_14786-A/agent/adk_events.jsonl`; trace SHA `c7cf90cb5b179947a0e060e829a73e0cf96784f223a26631b9483897e409f24f`. Candidate ZIP `2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608`.

Relevant inspection: 7.5254501310000705 (e2); first observed file edit: 29.647917860999996; first behavioral edit: 29.6987821350001 (e8). Checks: [6, 10, 16, 18, 20, 30, 36]. All subsequent edit acknowledgements: [{'event_index': 8, 'seconds': 29.6987821350001, 'basis': ['source_boundary_hash_change']}].

Native raw=True, assessed=True (NATIVE_RESULT_OBSERVED); submits=2; post-submit tools=4; stop=CONTEXT_RESERVATION_STOP. Model requests=24; received usage={'prompt_tokens': 184372, 'completion_tokens': 3103, 'total_tokens': 187475}; tools=24; Agent seconds=116.11263909799982.

Fail/edit/pass sequence precedes successful submission. e38 submit, e40/e42 reads, e44 repeat submit, e46 status; guard stops a natively correct patch.

## V02B/01-fastapi_5077-A

Source `6ecb9bfceb0b230ea3f4a2281b219d1e94c1ff2e50d4b0960b8701b4e7af2e45` / `results/runs/01-fastapi_5077-A/agent/adk_events.jsonl`; trace SHA `125c36cf397cc6d801779100b32e27dd39bab7551df0f93dde6cf3999c515044`. Candidate ZIP `2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608`.

Relevant inspection: 18.219300843000042 (e6); first observed file edit: None; first behavioral edit: None (eNone). Checks: [10, 18, 22, 40]. All subsequent edit acknowledgements: [].

Native raw=False, assessed=False (NATIVE_RESULT_OBSERVED); submits=0; post-submit tools=None; stop=CONTEXT_RESERVATION_STOP. Model requests=22; received usage={'prompt_tokens': 212774, 'completion_tokens': 6848, 'total_tokens': 219622}; tools=22; Agent seconds=211.79704634100005.

Self-authored reproduction initially fails on assignment to a read-only attribute. Later printed success coexists with unresolved annotation output; no production edit. Whether the model accepted that output is unknown.

## V02B/02-fastapi_5077-B

Source `6ecb9bfceb0b230ea3f4a2281b219d1e94c1ff2e50d4b0960b8701b4e7af2e45` / `results/runs/02-fastapi_5077-B/agent/adk_events.jsonl`; trace SHA `33b5385773661a7533a941f9e4e749f4a941e82ca774db3cff0ff75dbea488a8`. Candidate ZIP `70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8`.

Relevant inspection: 28.080248885000174 (e10); first observed file edit: 153.13347459500005; first behavioral edit: None (eNone). Checks: [14, 18, 26, 30, 34]. All subsequent edit acknowledgements: [{'event_index': 32, 'seconds': 153.18518964400005, 'basis': ['source_boundary_hash_change']}].

Native raw=False, assessed=False (NATIVE_RESULT_OBSERVED); submits=0; post-submit tools=None; stop=CONTEXT_RESERVATION_STOP. Model requests=22; received usage={'prompt_tokens': 235056, 'completion_tokens': 5280, 'total_tokens': 240336}; tools=22; Agent seconds=170.96932643200012.

e24 creates a test body containing pass without a discriminating assertion; e26/e30 green. e32 changes production only to add debug output, not repair behavior.

## V02B/03-fastapi_11355-B

Source `6ecb9bfceb0b230ea3f4a2281b219d1e94c1ff2e50d4b0960b8701b4e7af2e45` / `results/runs/03-fastapi_11355-B/agent/adk_events.jsonl`; trace SHA `7e88aa4c52e77c6a81b5c1900586d3dc59f2a49e1977b14bcd9de2dc8a421433`. Candidate ZIP `70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8`.

Relevant inspection: 118.11517714399997 (e40); first observed file edit: None; first behavioral edit: None (eNone). Checks: [10, 14, 20, 24]. All subsequent edit acknowledgements: [].

Native raw=False, assessed=False (NATIVE_RESULT_OBSERVED); submits=0; post-submit tools=None; stop=CONTEXT_RESERVATION_STOP. Model requests=22; received usage={'prompt_tokens': 167741, 'completion_tokens': 4548, 'total_tokens': 172289}; tools=22; Agent seconds=144.63653178000004.

Multiple self-authored examples and caught errors precede relevant helper inspection; no production edit. Issue lacks a complete executable contract. Exact causal misunderstanding is unobservable.

## V02B/04-fastapi_11355-A

Source `6ecb9bfceb0b230ea3f4a2281b219d1e94c1ff2e50d4b0960b8701b4e7af2e45` / `results/runs/04-fastapi_11355-A/agent/adk_events.jsonl`; trace SHA `da4c5ab062924c0f25100dd48b395a47d9ccb97f7ba820f04ec5477062bb4e67`. Candidate ZIP `2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608`.

Relevant inspection: 57.76839410499997 (e28); first observed file edit: 135.3766634179999; first behavioral edit: 135.4275266479999 (e42). Checks: [32, 36, 40]. All subsequent edit acknowledgements: [{'event_index': 42, 'seconds': 135.4275266479999, 'basis': ['source_boundary_hash_change']}].

Native raw=False, assessed=False (NATIVE_RESULT_OBSERVED); submits=0; post-submit tools=None; stop=CONTEXT_RESERVATION_STOP. Model requests=23; received usage={'prompt_tokens': 198441, 'completion_tokens': 4834, 'total_tokens': 203275}; tools=23; Agent seconds=154.22107146300004.

e40 fails an annotation assertion, e42 changes its handling, e44 reads modified code; guard prevents any later execution. Local hypothesis relevance to the entire Issue remains unproven.

## V03/01-fastapi_5077-A

Source `05bbbe3626123f1c4dbc7ce01382867e2d84affca942314fda733b3692d50580` / `results/runs/01-fastapi_5077-A/agent/adk_events.jsonl`; trace SHA `f87de8368434a8bb9e8007e6c0868033d8d564cb3bebb1c58a2a7ac2d9d35800`. Candidate ZIP `70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8`.

Relevant inspection: 22.210091650000095 (e6); first observed file edit: 149.52988632799998; first behavioral edit: 149.58394697099993 (e36). Checks: [10, 16, 34, 40]. All subsequent edit acknowledgements: [{'event_index': 36, 'seconds': 149.58394697099993, 'basis': ['source_boundary_hash_change']}, {'event_index': 38, 'seconds': 154.6961013749999, 'basis': ['source_boundary_hash_change']}].

Native raw=True, assessed=True (NATIVE_RESULT_OBSERVED); submits=0; post-submit tools=None; stop=CONTEXT_RESERVATION_STOP. Model requests=23; received usage={'prompt_tokens': 204363, 'completion_tokens': 5042, 'total_tokens': 209405}; tools=23; Agent seconds=164.45550196400018.

Cross-module reproducer output changes after e36/e38; native passes. Guard stops the session before explicit submit; official fallback retains a correct patch.

## V03/02-fastapi_5077-B

Source `05bbbe3626123f1c4dbc7ce01382867e2d84affca942314fda733b3692d50580` / `results/runs/02-fastapi_5077-B/agent/adk_events.jsonl`; trace SHA `cdba76a843d4767c4c7d350179d270e8c9b6bf38647e63f4c2caf176e8e45565`. Candidate ZIP `70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8`.

Relevant inspection: 16.225588238 (e6); first observed file edit: 182.51259361400002; first behavioral edit: 182.56596997499992 (e28). Checks: [10, 18, 22, 26, 32, 36, 38, 48, 50]. All subsequent edit acknowledgements: [{'event_index': 28, 'seconds': 182.56596997499992, 'basis': ['source_boundary_hash_change']}, {'event_index': 30, 'seconds': 190.11844005800003, 'basis': ['source_boundary_hash_change']}].

Native raw=True, assessed=True (NATIVE_RESULT_OBSERVED); submits=1; post-submit tools=0; stop=None. Model requests=29; received usage={'prompt_tokens': 344816, 'completion_tokens': 7911, 'total_tokens': 352727}; tools=28; Agent seconds=259.80592150000007.

e28/e30 behavior edits; e32 changed reproduction output. e36 unscoped pytest collects 702 cases/162 errors, e38 invalid path; e48/e50 relevant tests pass and e54 submits.

## V03/03-fastapi_11355-B

Source `05bbbe3626123f1c4dbc7ce01382867e2d84affca942314fda733b3692d50580` / `results/runs/03-fastapi_11355-B/agent/adk_events.jsonl`; trace SHA `99e1589876788db9de93bc44ceea7f41c9b4736dd2c4cd47d0ac964ee893aebd`. Candidate ZIP `70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8`.

Relevant inspection: 65.87111504999984 (e36); first observed file edit: 274.97391656900004; first behavioral edit: 288.1304769569999 (e74). Checks: [48, 56, 60, 64, 68]. All subsequent edit acknowledgements: [{'event_index': 72, 'seconds': 275.02345961599985, 'basis': ['source_boundary_hash_change']}, {'event_index': 74, 'seconds': 288.1304769569999, 'basis': ['source_boundary_hash_change']}, {'event_index': 76, 'seconds': 298.79206737799996, 'basis': ['source_boundary_hash_change']}].

Native raw=False, assessed=False (NATIVE_RESULT_OBSERVED); submits=0; post-submit tools=None; stop=AGENT_TIMEOUT. Model requests=40; received usage={'prompt_tokens': 443394, 'completion_tokens': 9199, 'total_tokens': 452593}; tools=40; Agent seconds=299.9996319329998.

e18 and e70 repeat a negative query; many ordinary examples do not distinguish the intended defect. e72 import-only edit, e74 first behavioral edit near 288s, e76 another edit near 299s; no post-edit execution. F6 is interpretation, not proof all exploration was waste.

## V03/04-fastapi_11355-A

Source `05bbbe3626123f1c4dbc7ce01382867e2d84affca942314fda733b3692d50580` / `results/runs/04-fastapi_11355-A/agent/adk_events.jsonl`; trace SHA `8b2f625c024811de2ea8ac0370813f3c4d04dcf0753c151dd1bca1939b728d49`. Candidate ZIP `70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8`.

Relevant inspection: 77.72288727900013 (e42); first observed file edit: None; first behavioral edit: None (eNone). Checks: [30, 60]. All subsequent edit acknowledgements: [].

Native raw=False, assessed=False (NATIVE_RESULT_OBSERVED); submits=0; post-submit tools=None; stop=CONTEXT_RESERVATION_STOP. Model requests=32; received usage={'prompt_tokens': 251255, 'completion_tokens': 4526, 'total_tokens': 255781}; tools=32; Agent seconds=145.96720866300006.

Relevant implementation was inspected; ordinary examples and searches continue until guard. No production edit; no observable proof of a correct causal explanation.

## CURE01/01-lumen_interface_01-checklist

Source `37c81c3cc89ddca69f8858f28015522f2f48af6e1781e1d44689885619c70639` / `runs/01-lumen_interface_01-checklist/adk_events.jsonl`; trace SHA `64b2a0cc71a34778be9df9b52123bb83b7debbeb99a9729eef19b93aad888fb8`. Candidate ZIP `f002c3c5cba1f629f2cce7608d2d72ac389af8a3ee03760257e1aff011844798`.

Relevant inspection: 12.641967802999943 (e2); first observed file edit: 47.895414315999915; first behavioral edit: 47.895414315999915 (e14). Checks: [12, 20, 22]. All subsequent edit acknowledgements: [{'event_index': 14, 'seconds': 47.895414315999915, 'basis': ['tool_ack_only_hash_unavailable']}, {'event_index': 16, 'seconds': 49.998584851999794, 'basis': ['tool_ack_only_hash_unavailable']}].

Native raw=True, assessed=True (NATIVE_RESULT_OBSERVED); submits=1; post-submit tools=0; stop=None. Model requests=14; received usage={'prompt_tokens': 48353, 'completion_tokens': 2629, 'total_tokens': 50982}; tools=13; Agent seconds=76.00156711699992.

Owned synthetic migration task; reads implementation/caller, adds compatible API/export, checks and submits. Not independent SWE evidence.

## CURE_C1/01-lumen_interface_01-checklist

Source `4108828cc749f81bb631bbfa2eab42138f794112e7def39daaff435300fe6e09` / `runs/01-lumen_interface_01-checklist/adk_events.jsonl`; trace SHA `89c03bce4e3498e237d59a5ad88dbd017b473b5cc4a9e673a5fb04f9b9976c8e`. Candidate ZIP `f002c3c5cba1f629f2cce7608d2d72ac389af8a3ee03760257e1aff011844798`.

Relevant inspection: 13.757593644000053 (e4); first observed file edit: 45.916159044000096; first behavioral edit: 45.916159044000096 (e14). Checks: [10, 20, 22]. All subsequent edit acknowledgements: [{'event_index': 14, 'seconds': 45.916159044000096, 'basis': ['tool_ack_only_hash_unavailable']}, {'event_index': 16, 'seconds': 48.02004971800011, 'basis': ['tool_ack_only_hash_unavailable']}].

Native raw=True, assessed=True (NATIVE_RESULT_OBSERVED); submits=2; post-submit tools=2; stop=None. Model requests=16; received usage={'prompt_tokens': 58616, 'completion_tokens': 2747, 'total_tokens': 61363}; tools=15; Agent seconds=79.56359842200004.

Owned synthetic task; repeat submission follows removal of own scratch file, so post-submit work is not automatically waste.

## CURE_C1/02-lumen_interface_01-cure_v01_c1

Source `4108828cc749f81bb631bbfa2eab42138f794112e7def39daaff435300fe6e09` / `runs/02-lumen_interface_01-cure_v01_c1/adk_events.jsonl`; trace SHA `96b3aa68dafaa28ce8a2b051bc8437eae1af173da4245e3b8b83586f22de93dc`. Candidate ZIP `c1001800838f1465c1a6414685db239fb03f9a69b45bba6ff34c6232a6f2e612`.

Relevant inspection: 17.34478332499998 (e2); first observed file edit: 59.45791856400001; first behavioral edit: 59.45791856400001 (e14). Checks: [8, 18, 20, 22, 24]. All subsequent edit acknowledgements: [{'event_index': 14, 'seconds': 59.45791856400001, 'basis': ['tool_ack_only_hash_unavailable']}, {'event_index': 16, 'seconds': 61.464027922000014, 'basis': ['tool_ack_only_hash_unavailable']}].

Native raw=True, assessed=True (NATIVE_RESULT_OBSERVED); submits=1; post-submit tools=0; stop=None. Model requests=15; received usage={'prompt_tokens': 62838, 'completion_tokens': 3147, 'total_tokens': 65985}; tools=14; Agent seconds=90.87413504999995.

Same owned synthetic repair. Model JSON declarations are advisory; no global state controller was executed.

## S2_EARLY/01-rich_3676-A

Source `d51735ad43a2d6318c1ec7fb10bd607b7ba9906d268b3b87924d547445f08b68` / `runs/01-rich_3676-A/adk_events.jsonl`; trace SHA `0c08dafa6333c2e4e95b47cab2a921cacb4f84f8f36b6c75c2012156e3b28e34`. Candidate ZIP `13968b67844d1041bfb79b9f11fc21ae66fb36aee5b00d3b91c526d5d35da329`.

Relevant inspection: 13.81703496299997 (e4); first observed file edit: 259.6267578679999; first behavioral edit: 259.63080838299993 (e78). Checks: [86, 90, 94]. All subsequent edit acknowledgements: [{'event_index': 78, 'seconds': 259.63080838299993, 'basis': ['nested_tool_file_hash_change']}, {'event_index': 80, 'seconds': 264.83646006000004, 'basis': ['nested_tool_file_hash_change']}, {'event_index': 84, 'seconds': 385.360821492, 'basis': ['nested_tool_file_hash_change']}].

Native raw=True, assessed=True (NATIVE_RESULT_OBSERVED); submits=0; post-submit tools=None; stop=TOOL_BUDGET_EXHAUSTED. Model requests=67; received usage={'prompt_tokens': 375649, 'completion_tokens': 15860, 'total_tokens': 391509}; tools=60; Agent seconds=491.4555337359999.

500s/60-tool experiment; production repair late, original tests pass. Tool cap prevents explicit submission; fallback patch succeeds. No AgentTool delegation.

## S2_EARLY/02-rich_3676-B

Source `d51735ad43a2d6318c1ec7fb10bd607b7ba9906d268b3b87924d547445f08b68` / `runs/02-rich_3676-B/adk_events.jsonl`; trace SHA `d68de5cab30f11d377c02cb8ade075203fb7af2ba7cb0cfa8ff735c30b67f3d3`. Candidate ZIP `d1e815e770abbcc448325ad2a3c8785c62f6d3c63bc7f95700850748c048a487`.

Relevant inspection: 12.362558651999962 (e4); first observed file edit: 164.64151293500004; first behavioral edit: 164.6454776789999 (e46). Checks: [14, 18, 40, 44, 52, 56, 60, 64, 68, 72, 80, 90, 110, 112, 114, 116]. All subsequent edit acknowledgements: [{'event_index': 46, 'seconds': 164.6454776789999, 'basis': ['nested_tool_file_hash_change']}, {'event_index': 48, 'seconds': 188.53062019000004, 'basis': ['nested_tool_file_hash_change']}, {'event_index': 50, 'seconds': 193.75982216700004, 'basis': ['nested_tool_file_hash_change']}].

Native raw=True, assessed=True (NATIVE_RESULT_OBSERVED); submits=1; post-submit tools=0; stop=None. Model requests=68; received usage={'prompt_tokens': 375486, 'completion_tokens': 15202, 'total_tokens': 390688}; tools=61; Agent seconds=473.56862093400014.

500s experiment; earlier behavioral edits and explicit submission. Reproduction/API mistakes occur but native passes. No AgentTool delegation.

## S2_EARLY/03-fastapi_14492-B

Source `d51735ad43a2d6318c1ec7fb10bd607b7ba9906d268b3b87924d547445f08b68` / `runs/03-fastapi_14492-B/adk_events.jsonl`; trace SHA `68f05194fe59a93f3c2014cc509affa372a53626c2ae7efdf8b6d2e4cf622510`. Candidate ZIP `d1e815e770abbcc448325ad2a3c8785c62f6d3c63bc7f95700850748c048a487`.

Relevant inspection: 24.208885925000004 (e8); first observed file edit: 39.63080612199997; first behavioral edit: 39.63708702400004 (e12). Checks: [22]. All subsequent edit acknowledgements: [{'event_index': 12, 'seconds': 39.63708702400004, 'basis': ['nested_tool_file_hash_change']}].

Native raw=True, assessed=True (NATIVE_RESULT_OBSERVED); submits=3; post-submit tools=6; stop=None. Model requests=33; received usage={'prompt_tokens': 180088, 'completion_tokens': 5834, 'total_tokens': 185922}; tools=30; Agent seconds=209.49474139599988.

Task target is executable docs_src example, not fastapi library. Edits that example; native passes. Three successful submits and six post-submit tools. Visible workspace test edit is not a trusted verifier modification.

## S2_EARLY/04-fastapi_14492-A

Source `d51735ad43a2d6318c1ec7fb10bd607b7ba9906d268b3b87924d547445f08b68` / `runs/04-fastapi_14492-A/adk_events.jsonl`; trace SHA `c92cddc99ca2857f0ef1a6705c38e7aadbdd1b63393787097774056e4f300189`. Candidate ZIP `13968b67844d1041bfb79b9f11fc21ae66fb36aee5b00d3b91c526d5d35da329`.

Relevant inspection: 77.99878528599993 (e24); first observed file edit: 108.55703854600006; first behavioral edit: 108.56334260299991 (e38). Checks: []. All subsequent edit acknowledgements: [{'event_index': 38, 'seconds': 108.56334260299991, 'basis': ['nested_tool_file_hash_change']}].

Native raw=True, assessed=True (NATIVE_RESULT_OBSERVED); submits=1; post-submit tools=0; stop=None. Model requests=26; received usage={'prompt_tokens': 143823, 'completion_tokens': 3123, 'total_tokens': 146946}; tools=24; Agent seconds=123.40489106099994.

Reads and edits target docs_src example, submits without running pytest; native passes. Absence of local test does not imply incorrect patch.

## S2_T500/01-rich_3471-B

Source `ee3651b4ca76b8a226a9f48ddb7e614add3bd32d3a77bcf32d37b13dd01425e0` / `runs/01-rich_3471-B/adk_events.jsonl`; trace SHA `f1f134873fbb9aedd952a25f0449311b92024e93a0e7583fd8ea2241e8a25c69`. Candidate ZIP `13968b67844d1041bfb79b9f11fc21ae66fb36aee5b00d3b91c526d5d35da329`.

Relevant inspection: 12.205213116999971 (e6); first observed file edit: 463.6658497970001; first behavioral edit: 463.669908382 (e90). Checks: [36, 52, 92, 96]. All subsequent edit acknowledgements: [{'event_index': 90, 'seconds': 463.669908382, 'basis': ['nested_tool_file_hash_change']}].

Native raw=True, assessed=True (NATIVE_RESULT_OBSERVED); submits=0; post-submit tools=None; stop=AGENT_TIMEOUT. Model requests=56; received usage={'prompt_tokens': 301198, 'completion_tokens': 15796, 'total_tokens': 316994}; tools=50; Agent seconds=500.0158269159999.

Production edit after ~464s; a self-authored check has 3 pass/1 fail based on an unsupported control-character expectation. Native 108 pass. Deadline prevents submission; no AgentTool invocation.

## S1_OUTPUT/01-requests_7328-control

Source `6f7ce7cec7979921e8cfae11e3f80411f6398281f1c5a2e461b42a5a57b03128` / `runs/01-requests_7328-control/adk_events.jsonl`; trace SHA `ecb67727cd76baf6582c33f61448e260b7b7638e6060e7f7e8e84e738b212da6`. Candidate ZIP `8835fd8ab4bdd43f5fcf74423c8ed2c3b9e0e0711686c8eac335b22c1da9da12`.

Relevant inspection: 6.48387571100011 (e2); first observed file edit: 258.496797219; first behavioral edit: 258.496797219 (e36). Checks: [12, 16, 34, 38, 42]. All subsequent edit acknowledgements: [{'event_index': 36, 'seconds': 258.496797219, 'basis': ['tool_ack_only_hash_unavailable']}].

Native raw=False, assessed=None (VERIFIER_ERRORS_ASSESSMENT_CONFOUNDED); submits=0; post-submit tools=None; stop=AGENT_TIMEOUT. Model requests=25; received usage={'prompt_tokens': 123109, 'completion_tokens': 9662, 'total_tokens': 132771}; tools=23; Agent seconds=299.99773174200004.

Post-edit reproduction still reports the investigated symptom; replacement mock yields a vacuous-looking history result. Native has 194 fixture errors, so repair outcome is unknown, not an algorithm failure.

## S1_LOCATE/01-rich_3278-control

Source `9279f95aadab5b4802c12bd4546ed78db44374173a451eb80bb9b66ce39c0159` / `runs/01-rich_3278-control/adk_events.jsonl`; trace SHA `1ed8cc0f61026bb5fc44bc779bc44b6c1b945f61068cacff115b25296a44df6d`. Candidate ZIP `8835fd8ab4bdd43f5fcf74423c8ed2c3b9e0e0711686c8eac335b22c1da9da12`.

Relevant inspection: 10.188523983000096 (e2); first observed file edit: 72.83948971500013; first behavioral edit: 72.83948971500013 (e8). Checks: [6, 10, 14, 18, 29]. All subsequent edit acknowledgements: [{'event_index': 8, 'seconds': 72.83948971500013, 'basis': ['tool_ack_only_hash_unavailable']}].

Native raw=False, assessed=False (NATIVE_RESULT_OBSERVED); submits=0; post-submit tools=None; stop=AGENT_TIMEOUT. Model requests=20; received usage={'prompt_tokens': 101572, 'completion_tokens': 8966, 'total_tokens': 110538}; tools=17; Agent seconds=300.04294081399996.

Final native summary is 4 failed/19 passed, zero errors. Historical observer confused a test data string saying 4 errors with an environment failure; its suppression of the next arm is infrastructure error, not this task classification.

## S1_STRUCTURED/01-rich_3130-control

Source `a5e062da220fb9c0b0912006c5c1a82e3a7fd98eb75048614379cd0dfe07a2d5` / `runs/01-rich_3130-control/adk_events.jsonl`; trace SHA `84bda9533ec5ae02cd54cd45859c9c2a4fd4f6da2e06aa208c4f930d312ad924`. Candidate ZIP `8835fd8ab4bdd43f5fcf74423c8ed2c3b9e0e0711686c8eac335b22c1da9da12`.

Relevant inspection: 9.635340387999804 (e2); first observed file edit: 165.70051438199994; first behavioral edit: 165.70051438199994 (e44). Checks: [22, 46, 48, 52, 54, 56, 60]. All subsequent edit acknowledgements: [{'event_index': 44, 'seconds': 165.70051438199994, 'basis': ['tool_ack_only_hash_unavailable']}].

Native raw=False, assessed=False (NATIVE_RESULT_OBSERVED); submits=0; post-submit tools=None; stop=AGENT_TIMEOUT. Model requests=48; received usage={'prompt_tokens': 237790, 'completion_tokens': 9296, 'total_tokens': 247086}; tools=44; Agent seconds=300.01000096300004.

e22 reproduction calls nonexistent API; e44 behavioral edit; e52/e54/e56 repeat the same failing targeted pytest with no intervening edit, then no revision. This supports failure to use feedback, not an inferred internal belief.

## S1_STRUCTURED/02-rich_3130-e3_locate

Source `a5e062da220fb9c0b0912006c5c1a82e3a7fd98eb75048614379cd0dfe07a2d5` / `runs/02-rich_3130-e3_locate/adk_events.jsonl`; trace SHA `f6fe6f261b3c010c5505b53e94e3718ba69257c5cb27d1ecec4ce755aadfba74`. Candidate ZIP `ae5e6157d2e96b20ffb4c9dd54902313cffeb9d1f9bdd231c38ef4eafbca7461`.

Relevant inspection: 10.093688246000056 (e4); first observed file edit: 78.64269636000017; first behavioral edit: 178.43363251000005 (e54). Checks: [16, 20, 24, 28, 58, 62, 80, 84, 86]. All subsequent edit acknowledgements: [{'event_index': 22, 'seconds': 78.64269636000017, 'basis': ['tool_ack_only_hash_unavailable']}, {'event_index': 54, 'seconds': 178.43363251000005, 'basis': ['tool_ack_only_hash_unavailable']}, {'event_index': 56, 'seconds': 191.19947407900008, 'basis': ['tool_ack_only_hash_unavailable']}, {'event_index': 60, 'seconds': 199.168731771, 'basis': ['tool_ack_only_hash_unavailable']}].

Native raw=False, assessed=False (NATIVE_RESULT_OBSERVED); submits=0; post-submit tools=None; stop=AGENT_TIMEOUT. Model requests=48; received usage={'prompt_tokens': 252778, 'completion_tokens': 10054, 'total_tokens': 262832}; tools=44; Agent seconds=299.999052915.

Initial ~79s edit is debug only. e54/e56 behavioral edits introduce an AttributeError observed at e58; e60 fixes it, e62 runs. Later inclusion-only assertions pass but native fails. This is actual revision, not F4 failure.

## S1_EGV/01-fastapi_15800-egv

Source `fdb36179f46921b4d61362c2ecb406afb8167e8decfdfa6b44b60930347a73c5` / `runs/01-fastapi_15800-egv/adk_events.jsonl`; trace SHA `f4836663c9e1b0f62f3d43f84aa7b8928585cdd54513373b84636d5958a51ae4`. Candidate ZIP `cefadd019ec64d9d06cbde72e0d0507796e8af9a370dd2358059e211845135e9`.

Relevant inspection: 12.504938804000062 (e2); first observed file edit: 160.08501475699995; first behavioral edit: 160.08501475699995 (e38). Checks: [36, 42, 48, 52]. All subsequent edit acknowledgements: [{'event_index': 38, 'seconds': 160.08501475699995, 'basis': ['tool_ack_only_hash_unavailable']}, {'event_index': 40, 'seconds': 196.08649380200006, 'basis': ['tool_ack_only_hash_unavailable']}, {'event_index': 44, 'seconds': 228.21035446200005, 'basis': ['tool_ack_only_hash_unavailable']}, {'event_index': 46, 'seconds': 234.755148707, 'basis': ['tool_ack_only_hash_unavailable']}].

Native raw=False, assessed=False (NATIVE_RESULT_OBSERVED); submits=0; post-submit tools=None; stop=AGENT_TIMEOUT. Model requests=30; received usage={'prompt_tokens': 167878, 'completion_tokens': 9263, 'total_tokens': 177141}; tools=27; Agent seconds=300.0111992609999.

e42 targeted HTTP assertions fail; e44/e46 revise; e48 three checks pass; e52 repeats unchanged checks. Native 18 pass/42 fail: feedback-driven local correction is insufficient for complete repair.

## S1_EGV/02-fastapi_15800-control

Source `fdb36179f46921b4d61362c2ecb406afb8167e8decfdfa6b44b60930347a73c5` / `runs/02-fastapi_15800-control/adk_events.jsonl`; trace SHA `5be6a34446e565239655719969d581981955b03a51f9b2e39b769650831d207d`. Candidate ZIP `8835fd8ab4bdd43f5fcf74423c8ed2c3b9e0e0711686c8eac335b22c1da9da12`.

Relevant inspection: 15.961961792000011 (e4); first observed file edit: 268.3158810489999; first behavioral edit: 268.3158810489999 (e84). Checks: [60, 70]. All subsequent edit acknowledgements: [{'event_index': 84, 'seconds': 268.3158810489999, 'basis': ['tool_ack_only_hash_unavailable']}, {'event_index': 92, 'seconds': 284.843141222, 'basis': ['tool_ack_only_hash_unavailable']}].

Native raw=False, assessed=False (NATIVE_AGENT_REGRESSION_OBSERVED); submits=0; post-submit tools=None; stop=AGENT_TIMEOUT. Model requests=51; received usage={'prompt_tokens': 272184, 'completion_tokens': 9510, 'total_tokens': 281694}; tools=47; Agent seconds=300.01403737300006.

Late production edits introduce literal escaped docstring quotes. No execution after edits. Original native JUnit reports SyntaxError at the changed applications.py location; algorithm-generated regression, not missing dependency.
