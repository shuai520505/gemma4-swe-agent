# 原始证据一致性及 PR15 报告勘误

TaskResult 的 agent_patch 为空、LLM/tool调用为0、resolved=false、test_exit_code=2。status=SUCCESS 表示评测流程返回，不表示修复成功。phase2_execution.exit_code 同为2。JUnit SHA 为 266a78fe40e3e921eb8d5390a263a0ab603d4e0015d7da115a442aa2316c4d2b，与清理前捕获记录一致；包含3个 collection error节点、0个failure节点、0个skip节点，不能称为执行了3项行为测试。原始 passed=null 保留不变。

原始 Issue/base/overlay 身份一致。snapshot SHA 40bf4271b23d5e094e5365474de25ca2509f5e0ad8adc1292055b9852da49311 来自原生输入身份记录；本轮没有重新解包或运行官方任务快照。六个关键 snapshot-derived 文件额外与固定 base 的 Git blob、运行前后文件哈希交叉核对。

**明确勘误：** PR15 的 CPU_ADMISSION_REPORT.md 及 PR 描述中“before/after 文件不存在、workspace_files_unchanged=false”的文字是错误的。原始 ZIP 中有 before_pytest_files.json 和 after_pytest_files.json，回收目录中也有；两份解析后的映射完全相同，共1191项；原 ledger 的布尔值为 true。原始数据自身一致，错误发生于上一轮解释报告。旧报告、ledger、ZIP、SHA 均不改写，本文件作为新增纠正证据。

相同哈希的范围由 screen.py:source_hashes 定义：Python源码、项目/pytest/setup/tox配置及requirements，排除缓存、.git、egg-info。它证明1191个受检查文件在两个检查点一致，不保证所有临时文件都未改变。六个源文件/依赖声明文件与两份快照及固定 base 精确一致。SOURCE_BYTE_VERIFICATION.json、STATIC_FINDINGS.json、EVIDENCE_LINE_INDEX.json 给出 SHA 和定位。

import observer 证明 fastapi.param_functions/params 来自真实工作区并执行了模块代码；不是完整行为断言覆盖。cleanup.json 的 complete=true、新残留进程列表为空。JUnit 已在 sandbox 清理前保存。没有发现 TaskResult/JUnit/任务身份矛盾；未捕获实际 pytest 版本和 metadata 的历史时间异常仍是独立限制，不能凭猜测补齐。
