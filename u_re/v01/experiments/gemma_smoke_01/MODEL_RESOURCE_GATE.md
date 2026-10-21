# Model and runtime gates

Exact source google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2; model alias gemma-4-31b-it-qat-w4a16-ct. Eight expected files and SHA are in MODEL_RUNTIME_CONFIG.json and SMOKE_PLAN.json. This turn did not load weights or validate the current remote mount.

Historically successful S2:4xNVIDIA L4,TP4,CUDA12.8,vLLM0.19.1,swegemma0.2.11,adk-submission0.2.13,ADK1.36.1,genai2.11.0,litellm1.82.4. Model context32768,safety1024,bfloat16,gemma4 tool/reasoning parsers,auto tool choice on,LoRA off. These pins are preferred; no upgrade or alternate model.

At runtime before inference: verify account/quota and reservation arithmetic from raw API units; exactly4L4 without conflicting compute;>=22GiB physical memory/device; all8model and41official/124task wheel SHA; exact task snapshot/Issue/overlay identity; installed versions,CUDA/driver/backend compatibility; sufficient accepted Notebook window measured from container start; local /models routes to pinned weights; cancellation and idle counters observable. Current values are RUNTIME_RECHECK_REQUIRED.

Model access and applicable model licence acceptance must be reconfirmed in the user's existing account. Historical access is evidence of past technical feasibility, not a new licence determination or current entitlement. No remote service fallback is allowed.
