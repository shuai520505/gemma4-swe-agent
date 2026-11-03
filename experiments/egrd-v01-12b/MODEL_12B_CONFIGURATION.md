# Verified 12B configuration

Fresh official Kaggle Starter and HARNESS_README explicitly allow gemma-4-12b-it-qat-w4a16-ct. Authenticated read-only Kaggle model_instance_get confirms google/gemma-4/Other/gemma-4-12b-it-qat-w4a16-ct, version2, Apache2.0 and10296456900 uncompressed bytes. Exact weights are not inferred from a similar name.

Independent configs/12b.json and31b.json retain separately selectable aliases/mounts. No LoRA, extra Agent or model substitution is introduced. The official12B vLLM override is --hf-overrides '{"architectures": ["Gemma4ForCausalLM"], "model_type": "gemma4"}'. Both use the official gemma4 tool/reasoning parsers, TP4, max_model_len32768, BF16 execution with W4A16 compressed-tensors weights, output8192/thinking4096, temperature.2/top_p.95 and no prefix caching for the research run.

Google's model card reports12B architectural context256K; the official competition server is constrained to32768. Architectural capacity is not an effective runtime allowance. Loaded model latency and real tool compatibility require the actual pilot, not compiler success or a model listing. The recovered pilot now verifies actual12B serving and ordinary official-tool calling; see the observation below. Every actual Session logs alias and mounted path, and every model load records its observed file hashes, server command and elapsed time.

Primary sources: https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent ; authenticated competition HARNESS_README.md (fresh snapshot in evidence); https://ai.google.dev/gemma/docs/core ; https://huggingface.co/google/gemma-4-12B-it-qat-w4a16-ct . No third-party performance estimate substitutes for our latency measurement.


REAL_GPU_OBSERVATION: one accepted Notebook version1 actually allocated four NVIDIA L4 (23034MiB each); all nine12B files matched CPU-observed version2 hashes before load. Pinned vLLM0.19.1 loaded in209.260873661 seconds, with torch2.10.0+cu128/CUDA12.8 and official parsers/override. Three actual12B sessions generated83 HTTP requests,80 received responses and3 deadline-cancelled requests. All received responses were HTTP200. Ordinary six-tool calls were usable; the first requests also advertised all four official Skill accessors. Gemma invoked none of them, so **real12B EGRD Skill-calling compatibility remains NOT_VERIFIED**, even though CPU scripted SDK execution passed. Model loading success is not repair success.

No31B session/load occurred after the stop. Comparative latency and model-size repair effect remain UNKNOWN. Six inherited SDK conversation-compaction requests used the same model; they are included in usage and time and are not extra next-action controller calls. Main request generation and SDK summarizer settings are distinct.
