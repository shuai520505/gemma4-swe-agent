# 重放与证据边界

**最终状态：s1-e1-public-01 已因启动探针API错误停止，禁止再运行它的任何GPU批次。r04最终CPU71/71通过，没有新GPU协议；以下旧Notebook仅供审计，不应重复消耗GPU配额。**

原 S0/CURE 工作目录保留在旁边的 gemma4-swe-agent；本研究工作目录为 gemma4-s1-score-optimization。PR基于S0分支，仅新增s1/。不要将此工作目录整体打包为submission。

## 直接重放冻结 Notebook

notebooks/r02/cpu/study.ipynb 与 kernel-metadata.json 是完整自包含上传，载荷SHA、源码SHA与WheelSHA会在安装前校验。可直接用已授权Kaggle CLI上传该目录；这会创建新平台运行，不得把新的输出覆盖旧results/或用于补拼原实验。需要GPU、付费或平台配额时遵守本轮协议与停止规则。

GPU smoke Notebook同样自包含，含匹配的成功CPU门与冻结协议，挂载官方比赛数据、Wheelhouse和31B version2。只有当前协议仍允许且没有已发生的门失败时才能运行；已有运行不应重复上传消耗配额。screen_a/screen_b需前批完整batch_gate且顺序匹配，禁止先启动后补审计。

机器协议记录全量任务记录哈希、Issue/base、快照/测试Patch哈希；任务记录和参考答案不复制进候选。官方数据仍由比赛输入挂载。官方提示模板会添加预算/工具规则；五题hints均为空。

## 原始输出

results/<run>/raw.zip 是平台生成的原始ZIP，逐字节保存。collect.py验证CRC与每个evidence_manifest条目，并检查嵌套run ZIP；便于读取的Trace、Patch、日志都是原ZIP的字节副本。CPU或开发任务的结果不代表榜单成绩。

完整CPU源载荷在CPU raw.zip的source/中；完整GPU源载荷也在其raw.zip中。r02构建时意外递归收录了40个**此前CPU源文件副本**，均位于host source/s1/_local/cpu-r01/source/，没有被活动执行器导入，也不包含任务答案或进入任何Agent ZIP。它们已被如实纳入注册哈希，见results/cpu-r02/git-byte-audit.json。不能事后从冻结载荷删除后声称仍是相同运行。重放已冻结Notebook不依赖这些文件存在于本机工作目录。

r03在新的CPU登记中已经排除_local/results/revisions，78项清单通过66项测试；r04新增贯穿安装/哈希/启动的全局时钟，80项清单通过71项测试。旧r02载荷不删除、不改写；其GPU协议已STOP，不能再生成跟随批次。禁止把研究端源文件描述成需要提交的Agent架构。

## 本机离线检查

`python -m unittest s1.tests.test_core s1.tests.test_analysis s1.tests.test_window -v` 只需本机Python/psutil，17项包括8配置/边界、4离线统计与5全局时钟，不是另17项官方Gemma测试。完整Runner与新worker测试需官方Linux Wheelhouse，使用冻结CPU Notebook。

`python -m s1.freeze verify <原工作目录>` 检查639项原分支文件、304项S0基础工作文件与2个历史正式ZIP；另核验historical-cure-raw-hashes.json的8个CURE原ZIP。Git只应新增s1/。r02的38个、最终r04的46个S1注册文件已与CPU测试字节和Git blob比对；候选Prompt使用-text保留原S0 CRLF字节，不能用换行归一化改变哈希。

离线分析：`python -m s1.analyze s1/experiments/e1-public-01/protocol.json <新summary路径> <各已完成批次records.json>`。工具拒绝重复index或身份漂移，未取得的槽位自动not_run；unknown不作确认失败。不要覆写已保存summary以挑结果。
