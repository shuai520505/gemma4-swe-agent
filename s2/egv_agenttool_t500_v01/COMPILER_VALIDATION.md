# Official compiler and public API validation

Installed official Linux versions are exported per preparation: swegemma0.2.11,adk-submission0.2.13,google-adk1.36.1,google-genai2.11.0,litellm1.82.4. Actual exported source bytes and indexes are in results/*/validation/official_source. The pinned model/task wheel manifests remain checked during Notebook setup; any drift aborts.

CPU03 successfully compiles the actual five-member ZIP, resolves child config_path/include, loads both complete unchanged Prompts, observes seven Main schemas/six official tools plus AgentTool and three child tools, verifies common31B/output16384/thinking4096/seed17 with sampling/include_thoughts omitted, and executes empty-State/native Runner requests with real LiteLLM mocked HTTP. The candidate ZIP contains YAML/Markdown only.

The additional public EvalConfig test in CPU03 failed because the test omitted required submission_dir/models constructor arguments. This is a real failed test retained in the raw archive. CPU04 fixes those test arguments, compiles both S2-T500 and the single S1-EGV-T500 research control, parses each actual YAML through PyYAML and official public EvalConfig, and verifies500s/60/120. Its actual final result is separately required for acceptance; no prior300s proof substitutes for this test.

The private Stage1 scripts/inference.py is referenced in official HARNESS_README but not distributed in any of524 public competition files or core official wheels; attempted direct download returned404. We did not execute or inspect it. Official public API and actual native timer compatibility are established by tests; private scoring integration remains subject to the actual official submission and any returned error. No private source/upper-bound claim is invented.


## Final accepted evidence

CPU04 corrected configuration test passed and all115 original regressions actually reran and passed. CPU03 eight core methods passed with real500.093s evidence;its overall error remains retained. CPU_FEASIBILITY.json is explicitly COMPOSITE_DISTINCT_PREPARATIONS with unchanged critical source/candidate hashes,not a single9/9 passing preparation.
