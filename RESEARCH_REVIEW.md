# 修复率研究审查（2026-10-16）

建议先做三项无训练实验：**thinking/输出预算消融、受限的分层定位、接口驱动的定向验证**。它们直接对应目前空 Patch、探索耗时和接口遗漏问题；没有证据证明增加 LoRA、子 Agent 或思考长度会提高本项目比赛分数。具体实验见 [NEXT_EXPERIMENTS.md](NEXT_EXPERIMENTS.md)。本轮只做文献、公开源码和 CPU 静态审计，没有启动训练、GPU 修复实验或新的正式提交。

## 证据口径

- **V：本轮核验**，下载字节、静态源码、Kaggle CPU 输出或本仓库原始记录；V 不代表行为/修复效果已复现。
- **A：作者报告**，论文、项目原文或参赛者自报成绩，未由我们重跑。
- **S：官方工作人员声明**，注明公告与实际包审计的差别。
- **H：待验证假设/本项目设计**，不附会成已取得的增益。

研究起点 `3dbeefa`，Harness `2.0.3/r12`。此前官方 Linux CPU/API 38/38 与真实 GPU 基础设施门禁通过，只说明基础设施。新正式配对实验七次执行中六个 confirmed failed、一个 unknown，另一个 not_run；不能报告完整成功率或 V1 优势，详见 [原报告](experiments/formal-paired-01/REPORT.md)。公开任务及其失败分析已经暴露，不能再当独立确认集。

## 可比较的核心数字

下表均是相应作者报告，**只有第一行涉及本比赛 Public LB**；不同模型、数据、时限和采样次数不可横比。

| 工作与固定来源 | 模型/评测口径 | 核心数字与限制 |
| --- | --- | --- |
| [公开 v19 原帖](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747696) | Gemma 4 31B、无 LoRA；7.5 分钟正式包 | 作者报告 Public LB **0.17**。15 分钟本地两次分别 **44/129、49/129**；不能用本地 34.11%/37.98% 替代榜分 |
| [SWE-agent，2405.15793v1](https://arxiv.org/html/2405.15793v1) | GPT-4 Turbo，原 SWE-bench 2,294 题 | **12.5%**；ACI 消融在另一个 300 题子集开展，不是 Gemma 或本比赛 |
| [Agentless，2407.01489](https://arxiv.org/html/2407.01489) | GPT-4o，SWE-bench Lite 300 题；定位、采样、验证与重排 | **96/300=32.00%**，作者当时 API 成本 **$0.70/题**；修复配置包含 **4×10** 个候选，不是一次廉价生成 |
| [SWE-smith，2504.21798v1](https://arxiv.org/html/2504.21798v1) | Qwen2.5-Coder-Instruct-32B + SWE-agent，Verified | **40.2% pass@1**；20k 任务收集 **5,016** 成功专家轨迹进行 SFT。论文约 50k 合成任务、128 仓库，不等于全部训练轨迹 |
| [SWE-Gym，2412.21139v1，表 9/§4.1](https://arxiv.org/html/2412.21139v1) | Qwen2.5-Coder-32B + OpenHands，Verified | **20.6%** 单次；**32.0% Best@16** 含学习到的 verifier。491 成功教师轨迹来自 2,438 任务/11 仓库；32% 不能归为单次 SFT 效果 |
| [SWE-RL，2502.18449v1，§3.1](https://arxiv.org/html/2502.18449v1) | Llama-3.3-70B + Agentless Mini，Verified | **41.0%** 为每题生成 **500** 补丁、用前 **30** 个复现测试重排后提交一个；训练 1,600 步，16k 上下文、全局 batch512、每题16 rollout |
| [DeepSWE-Preview 代码说明](https://github.com/agentica-project/rllm/blob/main/examples/swe/README.md) | Qwen3-32B + R2E-Gym，Verified | **42.2% pass@1、71.0% pass@16、59.2% hybrid TTS**。后两者分别是至少一解覆盖率和选中一解成绩，不能混用 |

Agentless 的旧版本 27.33%/$0.34、SWE-smith 最新数据卡规模和论文规模、DeepSWE 博客的四舍五入 59% 与当前 README 的 59.2% 均有版本差别。本审查不把它们拼成同一实验。

## SWE-agent / Agentless 如何适配 ADK 六工具

SWE-agent 的可迁移点是简洁动作、局部文件视图、搜索结果压缩和编辑错误反馈；原文用接口消融支持这些设计，未证明对 Gemma 同样有效。[论文 ACI 设计](https://arxiv.org/html/2405.15793v1)

Agentless 将定位分成文件、符号、编辑区域，再进行候选修复与测试筛选。保留其减少无关上下文的思路，不复制高采样数和额外模型流水线。[论文 §3](https://arxiv.org/html/2407.01489)

以下是本项目 H 级适配，不更改六个注册工具，也不引入子 Agent：

| 机制 | 现有工具中的实现方式 | 约束/可观察指标 |
| --- | --- | --- |
| 文件→符号→调用方定位 | `run_command` 查目录、入口配置及有界 `rg`/`grep`；`read_file` 读候选区域 | 每次读取须对应一个假设；先查可用命令，不能假设容器有 rg；记录重复读取率、首个有效编辑时间 |
| 行为定位 | `run_command` 执行最小复现，必要时跟随调用链；不可复现时记录原因 | CLI/新功能不强制执行 trace；失败路径不一定等于应修改路径 |
| 安全编辑 | `edit_file`/`write_file` 后经 `run_command` 做语法、diff 检查 | 不新增原生工具；匹配失败重新读，不盲重试；语法通过不等于语义通过 |
| 验证与覆盖 | `run_command` 做导入/CLI 启动→复现→相关回归；`get_status` 决定剩余验证量 | 失败区分环境、收集和行为；不读参考答案/Phase2 隐藏测试 |
| 收尾 | `get_status`、检查 diff/未跟踪文件，`submit_patch` | 可应用 Patch 尽早形成；提交后结束，不反复提交；不删除用户原有文件 |

对自动化任务，要从 Issue 可见需求核对入口、参数、工作流、环境变量和依赖；不能把某道 FastAPI 题的脚本名称植入提示。不要沿用公开 v19 对全部 CI/打包文件的禁改规则，否则会排除合法自动化需求。

## 数据生成与验证：可以借用方法，不能照搬结论

SWE-smith 先构建可执行仓库，再用 LM 改写、AST 变换、组合 bug、逆转 PR 产生缺陷；候选必须破坏原先通过的测试。其 Issue 生成器可见 bug diff 与失败测试，容易把定位线索泄漏进合成任务描述。这类数据适合练习动作与恢复，真实需求分布仍需另测。[论文 §2](https://arxiv.org/html/2504.21798v1)

SWE-Gym 更接近真实 PR/Issue：任务有 base commit、环境、补丁及 F2P/P2P 测试。成功轨迹经测试筛选；教师动作空间与 ADK 不同，不能只替换角色名就训练。其论文的 491 轨迹平均约 18,578 tokens；**OpenHands 分支自采样再训练并未奏效**，而另一个 scaffold 的 RSFT 有收益，说明“自训练必有提升”没有依据。[论文 §3/B](https://arxiv.org/html/2412.21139v1)

具体数据卡版本矛盾、字段、去重、仓库级拆分及成本见 [LORA_DATA_PLAN.md](LORA_DATA_PLAN.md)。测试通过只覆盖已执行的测试；不等于需求完备、无泄漏或私有榜泛化。

## SWE-RL / DeepSWE：奖励和成本必须分开看

SWE-RL 的主要奖励是对 oracle 修改的 `SequenceMatcher` 相似度，格式错误为负奖励；不是执行测试的二元正确性奖励。它减少每次奖励的容器执行成本，但会惩罚语义等价的不同实现，也可能奖励表面相似的错误修复。[论文奖励定义](https://arxiv.org/html/2502.18449v1)；[官方 reward 源码](https://github.com/facebookresearch/swe-rl/blob/main/src/swerl/core/reward.py)

论文所列1,600步×512 rollout/步约为819,200次训练采样（按配置推算，不是独立任务数），还要承担70B策略优化与参考模型成本。本轮未找到可可靠换算的完整GPU时长/账单，因此不把“奖励计算便宜”描述成“训练便宜”。

低成本可迁移方法（H）：离线用相似度发现格式/编辑转换错误，或辅助筛选；最终正例仍用执行验证。不要将相似度替代比赛 resolved。其公开代码注明 Agentless Mini 部分测试生成/执行仍在整理，并含 oracle 文件演示；演示结果不等于端到端评测。多数代码 CC-BY-NC4.0、Mini 部分 MIT，应按具体组件确认可复用范围。[官方仓库](https://github.com/facebookresearch/swe-rl)

DeepSWE 使用可执行的 F2P/P2P 选定测试及限时结果产生稀疏奖励，且过滤超长/超时/未正常完成轨迹。作者报告 4,500 任务、**64 H100 × 6 天**；按持续占用计算约 **9,216 H100 GPU 小时**，这是由报告推算的资源量，不是实付账单。另有 512 并发容器和 CPU/存储成本。[Together 作者博客](https://www.together.ai/blog/deepswe)；[复现说明](https://github.com/agentica-project/rllm/blob/main/examples/swe/README.md)

因此当前不推荐复现完整 RL。可先迁移“只收干净结束且验证通过的成功轨迹”“将环境异常与负奖励分开”“在单题内用一个复现加相关回归选择修订”这三点。不要把论文训练时将 timeout 奖励设为0，移植成实验审计中 unknown=failed。此处 DeepSWE 指 2025 Agentica/Together 训练项目，与同名的新基准不同。

## 官方 Wheelhouse 与 r12 的实际差异

本轮新建 [CPU 审计 Notebook](https://www.kaggle.com/code/wudangdexiaodoashi/gemma4-research-wheelhouse-audit-01)，版本1已 COMPLETE；**只读取挂载 Wheel ZIP，无安装、模型导入、GPU 或训练**。原始 [audit.json](docs/research/20261016/wheelhouse-audit.json) 记录 2026-10-16 12:38:16 UTC 的七个关键 Wheel SHA 和57个源码文件 SHA/命中行。CLI metadata未返回版本号；进一步查询[官方dataset view API](https://www.kaggle.com/api/v1/datasets/view/metric/gemma-4-developer-agent-wheelhouse)，实际返回 **currentVersionNumber=31**、lastUpdated=`2026-10-12T19:51:31.09Z`，原始选定字段保存在 [wheelhouse-view.json](docs/research/20261016/wheelhouse-view.json)。工作人员评论里的“v25”是历史状态，不是当前最新版本。CPU Notebook使用未指定版本的数据集引用，最终以挂载字节SHA作为环境身份，不能只靠数据集版本或包版本名。

| 部件 | 本轮实测版本/字节关系 | 对 r12 的判断 |
| --- | --- | --- |
| swegemma / adk-submission | 0.2.11 / 0.2.13；SHA 与仓库原有 `scripts/official_wheels.json` 一致 | 这两个小包未发现新字节差异 |
| google-adk / google-genai | 1.36.1 / 2.11.0；同原有小包 SHA | 不需要因公告日期就推断升级 ADK；v2 迁移未验证 |
| vLLM / Transformers / compressed-tensors | 0.19.1 / 5.13.1 / 0.15.0.1；与 S0 官方验证 SHA 一致 | r12 历史 GPU 记录版本相同；仅该历史版本记录不足以证明旧运行每个大 Wheel 字节相同 |
| r12 自有控制器 | 源码28项哈希冻结 | 新 Wheel 不替代其预算准入、增量证据和四态归因；本轮未修改 |

官方员工称 LoRA 别名层重置问题已修复，另称动态 adapter rank/count、thinking/seed 传递和双重 JSON 编码已修复；compaction、未声明工具及测试文件还原问题的处理状态不可一概视为完成。[LoRA 问题原帖](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/743508)；[工作人员状态评论](https://www.kaggle.com/ryanholbrook/discussion)

本轮可从源码进一步确认（V，静态）：

- `adk_submission/server.py:783–791` 按实际挂载 adapter 数量和 rank 生成 vLLM 参数，降低固定大预留风险；没有实测 LoRA 权重是否生效、显存或吞吐。
- `vllm/model_executor/models/gemma4.py:727/841` 存在通过 `__dict__` 保存共享decoder层、避免重复注册的分支，与静默清零问题的修复方向相符；具体分支及实际LoRA权重生效仍需GPU验证，不能只凭 `SupportsLoRA` 标记认定修复完成。
- `resolvers/generation.py:65–76` 把 `reasoning_content` 复制到 `reasoning`；`:431–446` 传递 seed、enable_thinking 和 `thinking_token_budget`。这比只搜索 vLLM 中是否出现字段名更有力，但仍不是 HTTP 请求/生成端验收。[历史问题及官方回应](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/744354)
- **正 thinking_budget 优先于 include_thoughts=false**（`:407–417`）。后者仍会清除返回/历史 thought parts（`:195–206`）。因此“隐藏 thought”“关闭 thinking”“保留工具回合中的思路”是三件不同的事；v19 YAML 的二者组合尤其需要按当前运行时复验。
- 服务上下文默认 **32,768**；swegemma 默认输出 **16,384**、thinking4096，允许输出1..32768、thinking0..32768。thinking 是总输出中的占用，不能把它再重复加一次；须实测 parser/截断行为。

r12 采用最终序列化请求的 tokenizer 计数，安全量1024、提前压缩并保留 Issue。应继续要求 `input + output_reserved + 1024 <= 32768`；恢复 thought 会增加输入，不能因修复保留问题而取消预算保护。r12 的压缩/截断是**开发控制器**行为，不能声称它自动进入只含 YAML/Prompt 的 S0 正式 ZIP；未来候选须在官方评分路径独立验证。[r12 设计](HARNESS_V2_DESIGN.md)

另一个已核实限制是 `harness_v2/worker.py` 将Agent时间设为480秒并断言输出16384。因此新预算消融需要独立登记的研究执行器，不能仅改YAML就复用r12并宣称设置已生效。两臂必须在同一新执行器中比较，旧r12与候选全部冻结。

## 31B 与 12B：支持、可加载和有效是三道门

官方新公告允许31B、12B、E4B、E2B，但同一次提交只能一种基础模型；原 overview 的旧限制存在文档滞后。工作人员确认其他运行条件相同，并指向未量化变体供适配器训练。[公告与回应](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287)

| 项目 | 31B | 12B |
| --- | --- | --- |
| 基础模型/架构 | 30.7B dense、60层 | 11.95B unified、48层；不是31B的裁剪兼容体 |
| 当前项目证据 | 指定QAT模型真实 GPU 基础设施已跑通；没有修复能力提升结论 | 之前官方CPU配置编译通过；尚无 GPU 加载、工具回合、速度或修复率结果 |
| LoRA | 必须匹配31B checkpoint、层名和形状 | 必须重新针对12B训练；31B adapter不能直接使用 |
| 推理路线 | 保持既有官方QAT模型 | 已知旧vLLM兼容问题；试验需独立版本与官方模型架构 override，不改冻结31B |

架构依据 [Google 官方模型卡](https://huggingface.co/google/gemma-4-12B-it)。旧12B加载错误与 `Gemma4ForCausalLM/model_type=gemma4` override 及视觉权重处理修复见[公告讨论](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287)。本轮 vLLM `gemma4.py` 视觉权重跳过标记存在，**不构成12B或LoRA GPU可用证明**。

Google 当前 QLoRA 示例列出31B与12B，使用 Transformers>=5.10.1、PEFT>=0.19.0、TRL、NF4冻结权重和官方 processor。但教程是短文本演示，不证明长轨迹或4×L4可以直接训练31B。我们应匹配比赛对应的 **IT** 基座与 processor；不能照抄示例中预训练模型名/小模型processor。`modules_to_save`、词表改动和多轮 loss mask 均须另验。[官方教程](https://ai.google.dev/gemma/docs/core/huggingface_text_finetune_qlora)

QLoRA 的 NF4 训练加载与比赛 compressed-tensors QAT W4A16 是不同量化路线。可行性假设是从对应未量化 IT 变体加载训练、导出 PEFT adapter，再由官方 QAT 基座挂载；需要权重效果和格式兼容实测。不要上传合并后的替代基模，也不要把参数量比值31/12当作吞吐提升倍数。

## 尚未验证的结论

没有重跑 v19 的129题，没有独立取得0.17对应的私有 Submission 记录，没有验证当前 LoRA 激活效果，没有完成12B GPU加载，没有测出本项目任何新方案的修复率增益。本轮 CPU 包审计只消除了部分版本/配置不确定性。下一步先用新候选、新任务和真实 Phase2 做小规模消融，再决定是否投资数据与训练。
