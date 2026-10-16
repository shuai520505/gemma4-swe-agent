# 新版 Gemma 4 模型路线核验

## 官方支持与文档差异

核验于2026-10-16。Kaggle 工作人员 Ryan Holbrook 的新公告允许 31B、12B、E4B、E2B 四种 QAT W4A16 CT 模型；同一提交所有 Agent 必须使用同一变体。工作人员确认小模型沿用相同资源和总时间条件；12B 需要官方 hf-overrides（Gemma4ForCausalLM / gemma4），后续回复称最新 wheelhouse 已修复视觉权重加载问题。旧线程仅31B的答复早于此公告，不应用来否定新支持。

主要来源：[新模型公告及工作人员回复](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287)。以上为工作人员声明，不当作我们已完成的模型启动实验。

## 本次实际检查

S0 的独立官方 Linux CPU Notebook 使用 swegemma0.2.11、adk-submission0.2.13、google-adk1.36.1、vLLM0.19.1、Transformers5.13.1、LiteLLM1.82.4。3个小模型标识均通过实际 compile_submission（临时副本、同样六工具、单Agent），没有修改任何31B候选。编译器通过不等于生产评分器白名单或 GPU 加载成功。

当前 gemma4.py 的 SHA 为31c752290ca93c2d004b61e14f9bf7e6de2f11e59b538a903b3b409c9b96b5c5，检测到 vision_embedder. 字符串；chat_utils.py 的 SHA 为8d1ed2b6321d587f89d3f59dbd6e6b4a942328bcdc0673fb30ec8e45559f834d，检测到 reasoning_content。此为源码标记探测，不足以单独证明对应分支运行正确。全量实际 wheels 哈希在 docs/validation/s0/official-wheel-hashes.json，编译记录在 official-validation.json。

Kaggle 挂载的官方 HARNESS_README.md SHA 为445000219b803942c469391ec8b69791a31e9cec2f934738c767e34b5ca0aa1f，与原始版本一致；本机父目录 README 已包含四模型列表。文档可能滞后，应分别记录具体版本并以工作人员新公告及实际服务检查交叉验证，不能仅看包版本号推断补丁状态。

## 可行性及下一条独立路线

12B 可进入独立候选研究阶段，暂不替换 S0/V0/V1，也不改变本次配对实验。官方允许不代表更高修复率。潜在收益是内存和推理开销较低；本项目尚无12B GPU测速、任务修复率或LoRA结果，不能使用他人的吞吐数字当本机数据。

后续应新建独立 M12 候选和模型版本注册，挂载指定官方权重，按官方额外参数启动；先验证模型身份、工具格式、tokenize与实际usage、上下文边界，再使用独立开发题验证启动、Patch、Phase2和清理。随后在新预注册协议中对比31B，不能与当前V0/V1八次实验混合。E4B/E2B同理。

现有 r12 worker 的模型身份审计有明确31B断言，因此小模型需要独立版本的参数化和完整CPU→GPU门禁，不能只替换一行 YAML 后假称当前Harness已经验证支持。严禁通过删改官方权重来绕过12B加载错误；若实际官方栈仍失败，应保存错误并停止，不声称模型已经可用。LoRA和多Agent不在本阶段范围。

结论：官方政策支持已确认；配置编译支持已实测；12B/E4B/E2B的GPU加载、吞吐和修复能力均未执行验证。31B提交及配对实验保持原样。
