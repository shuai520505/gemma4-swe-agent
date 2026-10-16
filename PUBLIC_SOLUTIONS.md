# 公开方案审查与 v19 源码核验

核验日期：2026-10-16。证据等级使用 [RESEARCH_REVIEW.md](RESEARCH_REVIEW.md) 的 V/A/S/H。公开作者成绩与本项目结果分开；未执行任何第三方 Notebook 或其中的脚本。

## 已取得的 v19 包与完整源码

- [原始评分 Code，固定 scriptVersionId=356344238](https://www.kaggle.com/code/yiyu0716/g4-pack-yiyu-v19-fixed-trace-t7p5?scriptVersionId=356344238)
- [完整源码 Notebook](https://www.kaggle.com/code/yiyu0716/g4-v19-complete-harness-source)
- [作者讨论：Time, Budget, and Thinking](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747696)

通过已授权 Kaggle CLI 下载原始 `.py` 和完整 `.ipynb`。原脚本内嵌 base64 ZIP；以 AST 常量解析和 base64 解码恢复文件，**没有执行脚本**。源码 Notebook 的11个 Markdown文件内容及导出 cell 的ZIP载荷均逐字节匹配。CLI output 过滤未取到独立 ZIP，因此本地包明确是**从公开原始载荷恢复的包**，不是声称另行下载的评分服务器产物。

| 证据 | 实际值 |
| --- | --- |
| ZIP 长度/CRC/成员数 | 15,499 bytes；CRC通过；11文件，根目录有 `agent.yaml` |
| ZIP SHA256 | `7515f0d89f26218f0f88caf336fbb5ecaf9db967b3e78ec74870cadd11c54040` |
| 原始脚本 SHA256 | `8b32258f92c079518f36181886531eeba041520f6c67bd5b4982b6d868406021` |
| 完整 Notebook SHA256 | `384837a20a4e7d8f9742d5cbbeafd780a98f1215ddd80eabaec6eeb4033e697e` |
| 本地包 | `artifacts/research-20261016/v19-audited/submission.zip` |
| 本地源码 | `artifacts/research-20261016/v19-source/g4-v19-complete-harness-source.ipynb` |
| 可提交的小型证据 | [逐成员哈希/一致性报告](docs/research/20261016/v19-static-audit.json) |

原始下载与完整解包保存在独立 ignored 目录，不覆盖已有 ZIP，不混入候选，也不把外部完整 Prompt 复制进仓库候选。公开可下载不等于已确认可无条件再发布全部代码；实施时优先自行实现机制。

## 成绩与可复现程度

| 对象 | 成绩/条件 | 证据等级及边界 |
| --- | --- | --- |
| 原 v19 Version1 | **Public LB 0.17，7.5分钟** | A：作者原帖和源码镜像明确归属；V：取得对应公开载荷。未独立拿到该Submission ID/平台评分记录，不能升级为我们复现的0.17 |
| 完整源码 Notebook | 导出同一ZIP | V：字节相同；作者明确说镜像**未单独评分** |
| 本地 Gemma v19 两次 | 15分钟；44/129、49/129 | A：作者报告；Alibaba PPU，本地模拟计时，历史硬件与并发存在差别；无本轮完整Trace审计 |
| 本地 DeepSeek 对照 | requested `deepseek-flash`，66/129 | A：2题smoke+127题合并；API延迟/采样不同，非受控模型消融，非Gemma比赛成绩 |

这些口径来自[同一原帖](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747696)。129题较高本地通过率不能推出私有任务榜分，也不能据一次0.10→0.17榜分变化证明 trace 的独立因果收益。v22时钟修正与v6.2–6.6硬保护属于本地版本，不在本次确认的评分包里。

## 实际结构与策略（V：源码静态核验）

| 层面 | 原包实际行为/声明 | 对当前六工具单Agent的启示 |
| --- | --- | --- |
| 架构 | root编辑Agent → `SequentialAgent` → read-only `code_analyzer`；同Runner共享 `analysis_plan`，root继续编辑 | 不是单Agent；只借用阶段划分与简短定位记录，不复制委派 |
| 模型与采样 | root/analyzer均31B；temperature1.0、top_p0.95、top_k64、输出2048 | 不能将它与我们默认16384的差异全归于Prompt |
| thinking | 两个YAML均 `thinking_budget:4096`、`include_thoughts:false` | 不能称为已验证的thinking-off包；当前官方桥接会开启thinking但剥离历史thought，历史评分环境语义未固定 |
| 预算 | max_time7.5分钟、100工具、120模型轮；timeout_seconds300；analyzer的10工具限制写在Prompt | Prompt限额不是强制运行时限额；命令时限不是Phase2独立验证上限 |
| 工具 | root四个基础工具，外加skill/transfer；analyzer含3个图工具及run_command；没有原生edit_file/write_file | 超出本项目六工具策略，不能整包替换S0 |
| 定位 | 抽取Issue标识符、有界搜索/局部读取；最小复现后采集实际函数路径；分析输出位置/根因/计划/测试/置信度 | 优先静态定位；trace只用于可复现行为，不对新增CLI/自动化强制使用 |
| 编辑 | skill安装 `/tmp/g4edit.py`；run_command提交SEARCH/REPLACE；语法检查、原子写入、错误反馈 | 可以研究“最近读过的区域+编辑后检查”，不新增工具或直接复制脚本 |
| 验证/收尾 | 复现、相关pytest、diff、检查后submit一次；get_status约每8工具，余量不足25%则收尾 | 先验证最危险接口，减少后期探索和重复提交 |

完整源码来源见上述两个 Code 链接；逐文件SHA见审计JSON。特别核对的代码位置：`g4edit.py:154–198`匹配逻辑、`:217–237`清理、`:462–486`语法检查与写入；`generation.py:407–446`的当前官方thinking语义见研究审查，不能据此倒推旧评分环境。

## 不能原样照搬的风险

1. Prompt声称SEARCH须唯一精确匹配，但脚本还允许尾空白、片段与忽略缩进等回退。反馈友好有价值，模糊匹配可能改错位置；新机制应先用严格匹配并显示diff。
2. `--check`会恢复受保护文件并删除部分未跟踪scratch。若任务真要新增相关文件，或目录已有用户文件，启发式清理可能损坏结果。本项目不运行该脚本，也不采用其删除规则。
3. 全面禁止CI、打包、pytest配置等修改会妨碍真实自动化需求。不得用该限制替代Issue契约判断。
4. 必须trace和强制首调用安装脚本增加启动、工具与依赖成本；多一个分析Agent不保证同预算收益。可用现有六工具直接完成结构检查和复现。
5. 2048总输出配4096thinking声明不保证可用答案长度；当前桥接语义与评分时包版本缺少一致性证据。应保存实际请求、finish_reason和token使用再比较。

## 其他已取得的公开方案

此前只读下载的三份Notebook及SHA见 [sources.json](docs/public-research/sources.json)，分析见 [PUBLIC_LEADERBOARD_STUDY.md](PUBLIC_LEADERBOARD_STUDY.md)。本轮复用已有证据，不把它们当新的独立复现。

| 公开来源 | 结构/预算 | 榜分证据与可复现边界 |
| --- | --- | --- |
| [Budget-Aware Coding Agent v2](https://www.kaggle.com/code/flexonafft/gemma-4-budget-aware-coding-agent-v2) | 单Agent；8分钟/28工具；输出8192；声明thinking4096；阶段化导航、编辑、测试 | 源码V；未建立具体评分版本到源码SHA的一对一关系 |
| [Baseline LB 0.24](https://www.kaggle.com/code/honghanhhh/gemma-4-baseline-lb-0-24) | 共享上一基线；加强接口覆盖与工作树检查 | **0.24是标题/作者陈述A**；不能把目录排序当平台评分证明 |
| [Budget-Fit Single Agent](https://www.kaggle.com/code/verracodeguacas/gemma-4-agent-budget-fit-single-agent) | 同组预算；限制无效探索、定向测试 | 作者引用129次本地运行；未取得全量原始运行作独立审核 |

此前CLI查询的领先分数0.24保存在 [leaderboard-query.json](docs/public-research/leaderboard-query.json)，只对应其查询时点，不能证明当前榜首或任何一份最新下载源码的得分。上述三份有共同来源，不是三次独立有效性验证。

结论：公开方案最值得迁移的是**预算内有证据的定位、尽早形成Patch、针对接口验证**。公开分数是研究线索，不是本项目收益保证；候选修改必须另起身份并做消融。
