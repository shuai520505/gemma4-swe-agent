# 可选 LoRA 数据计划：先审计数据，再决定是否训练

日期：2026-10-16。**本计划未执行训练、轨迹生成或大规模数据下载。** 本轮只取得数据卡/版本元数据和论文。V/A/S/H含义见 [研究审查](RESEARCH_REVIEW.md)。优先完成无训练消融；训练仅作为后续路线，不能用其他模型的SWE-bench成绩预估本比赛分数。

## 数据源选择与实际结构

| 数据源 | 可取得内容 | 选择理由与风险 |
| --- | --- | --- |
| [SWE-smith Python](https://huggingface.co/datasets/SWE-bench/SWE-smith-py) | 数据卡：50,908任务/131仓库；`instance_id, repo, image_name, problem_statement, patch, FAIL_TO_PASS, PASS_TO_PASS` | 推荐按需取少量环境生成ADK原生轨迹；多仓库，但合成bug/描述有分布偏差 |
| [SWE-smith trajectories](https://huggingface.co/datasets/SWE-bench/SWE-smith-trajectories) | `messages`为JSON字符串，另含 `instance_id,resolved,model,traj_id,patch`；tool/xml/ticks三种表示 | 可用于行为分析/候选示范筛选；必须按traj_id/任务去重，不能把三种序列化当三个独立样本 |
| [SWE-Gym](https://huggingface.co/datasets/SWE-Gym/SWE-Gym) | 2,438真实任务；含repo/base_commit/problem_statement/patch/test_patch、hints_text、F2P/P2P等 | 接近真实需求；仓库仅11个，严格仓库切分后有效训练量可能很小 |
| [OpenHands-SFT-Trajectories](https://huggingface.co/datasets/SWE-Gym/OpenHands-SFT-Trajectories) | 491条，split=`train.success.oss`；公开schema只列 `messages[{role,content}]` | 小、便于先审查；缺少schema级instance_id，若不能可靠关联原任务，就不能用于需要仓库拆分的正式训练 |
| 新生成的ADK六工具轨迹 | 本模型/教师在可执行公开训练环境中的真实动作、工具响应、Patch和验证 | 最贴近提交动作空间；生成和验真成本通常高于整理数据，不能偷用评测题答案 |

上述数据卡声明MIT；这不自动替代所含上游仓库源码、模型和教师输出的各自许可。数据卡小样本字段可核验，不等于全部数据都已验真。

固定元数据快照见 [dataset-revisions.json](docs/research/20261016/dataset-revisions.json)：

| 资源 | 本轮取得的 revision SHA |
| --- | --- |
| SWE-smith 原始合集 | `ea6d7173829c7ec8fa16c22055699ff2e9188091` |
| SWE-smith Python | `77cab9055d42ab4a5c25c89a8f937096db13558e` |
| SWE-smith trajectories | `08e109b4a59eaeebf80e4675cd125d42e7ac99a4` |
| SWE-Gym | `bb94ed9e39bbeb96a7fcbfb533b80f25a7fd59cb` |
| OpenHands SFT | `4aaa5a4a4b5861f4799d2336908760c190ac3b17` |

**版本矛盾须显式处理（V）：** SWE-smith原始合集数据卡metadata为59,136行，正文仍写50,137；轨迹卡正文写5,017而三种split metadata为24,100/26,076/25,826；论文v1用5,016条。不能把metadata总和当独立成功轨迹数。SWE-Gym README称Lite234，论文表格与实际Hub目录是230。未来加载必须固定revision并实际统计行数、唯一任务和成功数，本计划不伪造全量统计。

## 轨迹生成和正确性

SWE-smith从可运行仓库生成破坏既有测试的缺陷，保留至少一个原通过测试变失败的样本；Issue生成可访问缺陷diff和失败测试。SWE-Gym以真实PR与测试构造任务，成功轨迹经执行过滤。这些方法支持“环境先可用、再采样、再验真”，但公开resolved标记仍应在目标环境抽检。[SWE-smith生成/验证文档](https://swesmith.com/guides/harnesses/)；[训练文档](https://swesmith.com/guides/train_swe_agent/)；[SWE-Gym代码与环境](https://github.com/SWE-Gym/SWE-Gym)

注意两种 `patch` 的方向不同：SWE-smith任务字段是**注入缺陷**的diff，预测patch才是修复；SWE-Gym任务patch是原PR修复。转换器必须用环境与基线验证方向，不能把Smith任务patch当作应学习的修复标签。当前Smith gather文档还要求同时有F2P与P2P，不能只沿用论文摘要的“至少一个失败测试”作为全部准入条件。

建议的第一轮数据工作仅是**20条结构与重放审计**，通过后才扩到100–300条训练候选，另留50–100个不同仓库任务作验证/确认集（样本数为H级计划，不是已有数据）。有限仓库时宁可减少量，不拆同仓库轨迹充当独立泛化验证。

顺序如下：

1. 先冻结仓库分组和数据revision，后生成轨迹；只给Agent初始Issue、合法工作区和工具。参考Patch、测试补丁、奖励与去重信息留在评估侧。
2. 在训练任务上确认干净基线测试与oracle修复能产生有效F2P/P2P；这是校验训练环境，不是评测Agent时提供答案。无法运行的样本隔离为环境unknown。
3. 按正式的31B/六工具/单Agent/时间与上下文限制采样；先K=1，训练任务可对预先规定的困难层K=2，保存所有尝试与失败率。禁止只保留容易任务后宣称整体成功率。
4. 在独立干净容器重放Patch，要求可应用、正确收集、F2P通过、P2P无新增失败，显式提交并正常结束。环境超时、缺日志、清理不确认均不进入正例。
5. 对关键正例重复验证，检查测试篡改、关闭断言、跳过行为、外网依赖、写入答案/环境变量等捷径；只有语法通过或Patch相似不算正例。记录可验证范围，不宣称测试完备。
6. 成功但含长时间无效探索的轨迹不直接大量复制。可抽取已验证的一步编辑/动作样本，或重新采样短轨迹；不能删去中间失败动作却保留它产生的工作区状态，伪造可重放的成功轨迹。

SWE-RL式相似度适合辅助检查编辑转换，不能替代执行验证；DeepSWE式异常过滤可借用，但unknown不成为确认负例。失败轨迹单独保留作错误分析/未来偏好数据，**不默认全部作为正向SFT**。

## 目标格式（设计，尚无训练文件）

建议以两层JSONL保存：一层不可变审计record，一层由固定转换器产生的训练messages。下面是**schema示意**，不是声称存在的成功记录：

```json
{
  "schema": "adk6-trajectory-v1-draft",
  "instance_id": "<source-id>",
  "repo_group": "<canonical-owner/repo-and-forks>",
  "base_commit": "<sha>",
  "source_revision": "<dataset-sha>",
  "split": "train",
  "messages": [
    {"role": "user", "content": "<original issue>"},
    {"role": "assistant", "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "read_file", "arguments": "<actual JSON args>"}}]},
    {"role": "tool", "tool_call_id": "c1", "content": "<actual response>"}
  ],
  "audit": {"outcome": "<resolved/failed/unknown/not_run>", "phase2_log_sha256": "<sha>", "patch_sha256": "<sha>", "tool_schema_sha256": "<sha>"}
}
```

字段和参数名以实际编译器工具schema为准，不凭论文示例重命名。训练视图不得含 `audit`、oracle patch、test_patch、隐藏测试名或未来工具输出。六个工具限定 `run_command/read_file/write_file/edit_file/get_status/submit_patch`。OpenHands的代码块、SWE-agent XML动作与ADK原生函数调用不是同一种格式，必须转换并重放；不能转换的动作丢弃或重采样，不能捏造工具反馈。

Smith任务卡未列base_commit，必须由固定image/任务分支可靠还原工作树并记录内容哈希，不能凭repo名称假定与GitHub HEAD相同。OpenHands SFT缺少任务关联字段的问题也要先解决，关联失败就不进入训练。

用匹配基座的官方processor模板，逐回合验证tool_call_id对应、JSON转义、结束标记、thinking片段和输出截断。只训练assistant实际生成的合法内容/工具参数，user、工具响应、padding均mask；多轮不能直接照抄只查第一个assistant header的单轮教程collator。没有真实可见thought就不补写“教师推理”。长轨迹按完整动作边界截取，保留原Issue、必要状态和最近反馈；任一工具调用/响应不得跨切分遗漏。

## 去重与防泄漏

先按 canonical repo+fork网络形成分组，再按稳定哈希分配约70%训练/15%开发/15%封存确认；比例只是起点，必须公布实际任务/仓库数量。相同任务的所有采样、变体、逆PR、不同序列化及同祖先bug属于同组。用于选择超参数的开发集不能又作为最后确认集。

至少做：原文/归一化Issue哈希、base/parent/PR链接、Patch归一化哈希、函数AST与代码片段近重复、fork/vendor复制关系检查。近重复图跨split连通时整组移动或剔除，并保留阈值与排除清单。仅按instance_id随机切分会泄漏同仓库代码与bug模板；仅按时间切分仍会泄漏fork和反向补丁。

本项目已暴露的 FastAPI、requests、rich、HTTPX 任务及参考分析，全部退出新确认集。若这四仓库用于未来泛化验证，训练侧连同fork/镜像一起排除。具体已见任务为 `fastapi_15661, fastapi_15589, requests_7315, rich_3777, rich_4006, requests_7309, rich_3052, fastapi_14258, httpx_3672`；还须依据日志更新暴露清单，不能认为这九个ID就是所有潜在污染。

SWE-smith合成描述可能带入由oracle可见生成的过强提示；SWE-Gym的hints/PR讨论也可能含解答。训练用描述要审查并标记来源，评测prompt严格保持原Issue，不在看过答案后“清洗”出有利评测题。官方员工表示隐藏题来自非公开私有仓库，但这不证明基础模型预训练、fork或训练数据绝无污染。[工作人员说明](https://www.kaggle.com/ryanholbrook/discussion)

## 31B/12B训练和部署门禁

两条路线分开登记，模型revision、tokenizer/processor、target modules、rank/alpha、量化与库版本全部固定。对应IT未量化权重（可在训练时NF4加载）→PEFT adapter→官方QAT基模挂载是待验路径；31B adapter不能移到12B。Google教程给出当前QLoRA支持，但不证明比赛部署兼容。[Google教程](https://ai.google.dev/gemma/docs/core/huggingface_text_finetune_qlora)；[官方模型公告](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287)

未来先做无优化步骤的导出/加载检查，再做少量步数效果检查。要求：tensor名称/形状覆盖、官方discover_adapters与编译通过、rank/文件尺寸限制、基模与adapter确定性logprob确有差异、服务启动/工具多回合、显存/KV cache/context、12小时总预算。`adapter loaded`日志不足以排除历史静默清零问题。rank8/16仅作初始低成本假设；不直接用rank128，也不训练embedding/lm_head或改词表，除非先确认官方部署支持。

## 成本估算（规划假设，不是实测报价/耗时）

| 工作 | 可核算方式 | 示例与不确定性 |
| --- | --- | --- |
| 下载/整理现有轨迹 | 文件量、解析CPU时间、重放容器时间分别计 | OpenHands491条卡约10.4MB下载；SWE-smith三表示合集卡约3.17GB下载，不能无选择全量当低成本 |
| 本模型生成300任务，K=2 | 600尝试×每题最多5分钟 | 顺序GPU占用上限约50节点小时，若4GPU始终驻留约200 GPU小时；另加模型启动/验证，不是预算推荐值 |
| 验真600个Patch | 每次最多300秒 | 最坏50容器小时，CPU核小时还需乘实际核数；可并发不等于总成本降低 |
| 小型SFT | N×平均有效序列长度×epochs / 实测吞吐 | 假设200条×12k×2=4.8M tokens；若整个训练作业100–500 token/s，则2.7–13.3节点小时；假设4GPU则10.7–53.3 GPU小时，**吞吐未测，可能OOM或更慢** |
| DeepSWE全RL | 作者报告64H100×144h | 约9,216 H100 GPU小时，另需大规模CPU/存储；不列为当前可执行低成本路线 |

金额=实测GPU/CPU/存储/教师token用量×实际费率；本轮没有付费价格承诺。公开成功率不能直接用于预测本模型采样成功率。已有验证通过的轨迹优先于昂贵教师生成，但重放、工具格式和许可成本不能忽略。

SWE-Gym官方复现说明使用8GPU做policy全参数微调；这不是本计划的小LoRA成本，也不能从491条数据推断训练必然便宜。[原训练说明](https://github.com/SWE-Gym/SWE-Gym/blob/main/docs/OpenHands.md)

只算权重的4bit理论下限：31B约15.5GB、12B约6GB（十进制，未含量化元数据、LoRA/优化器/激活/KV）。BF16分别约62GB/24GB。4×L4显存不是单卡连续96GB；数据并行会复制模型，量化分片/训练框架支持和序列长度要实测。不要据此保证31B长轨迹QLoRA可在Kaggle运行。

## 是否进入训练

目前结论：**暂不进入训练**。先有无训练候选的完整可审计对照、少量数据重放通过、真实adapter有效性与12B/31B部署兼容证据，再冻结训练pilot。若整理后合规、无污染、可重放正例不足100条，优先继续解决scaffold问题；这只是投入门槛，不是宣称100条一定足够。
