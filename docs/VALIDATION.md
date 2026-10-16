# V0 真实验证记录

验证日期：2026-10-14。对象：本 PR 的单 Agent V0；没有比赛提交或得分。

## 来源访问

| 项目 | 真实结果 |
| --- | --- |
| 初始 Kaggle/GitHub API 网络 | 代理拒绝 403；增加必要域名后重试成功 |
| 比赛与规则 URL | HTTP 200，但返回 SPA HTML，未取得完整规则正文 |
| 公共 Competition API | 成功；确认要求 `submission.zip`、规则接受与身份验证 |
| Getting Started Notebook | 公共 API 成功下载版本 3，实际阅读全部代码单元 |
| HARNESS_README.md | 竞争数据下载 API 返回 401 Unauthorized，未读取 |
| sample_submission / tasks / snapshots | 比赛文件列表 API 返回 401，未取得 |
| 官方 wheelhouse | 公共数据集 API 成功；完整分页获取文件列表，下载并检查五个 wheel |
| Kaggle 凭据 | KAGGLE_API_TOKEN / KAGGLE_USERNAME / KAGGLE_KEY 均未注入；没有打印任何凭据 |
| GPU | 当前机器无 nvidia-smi；未取得 Kaggle GPU 执行权限或模型权重 |

官方 Notebook 明确给出四种允许模型、31B 是 sample 默认模型；本实现固定用户指定 31B。官方 wheel 源码确认闭合工具注册表、沙箱 `!include`、可选 eval 配置与 ZIP 根配置要求。完整比赛规则、README 和 sample 的逐项核对仍待完成。

## 本地验证

- 官方包：google-adk 1.36.1、google-genai 2.11.0、adk-submission 0.2.13、adk-eval-core 0.1.0、swegemma 0.2.11，来自官方 wheelhouse。
- `scripts/check.sh`：官方 `load_yaml`、`validate_directory`、`compile_submission`，传入真实 `SwegemmaContext.create_tools()` 和官方 `build_submission_limits()`，编译成功。验证单 Agent、六个真实工具绑定及指定模型的本地 LiteLLM 路由。没有调用模型。
- 6 项 unittest：官方编译；ZIP 布局/确定性/解压后再编译；模型/提示词/架构篡改拒绝；未批准或缺失工具拒绝；符号链接拒绝；官方工具修复/测试/diff/submit_patch 集成。
- 集成测试使用真实 `SubprocessManager` 与官方工具工厂创建独立临时 Git 仓库，先验证故障，再编辑、验证成功、检查 diff 并捕获 patch。**这是脚本驱动的合成测试，不是 Gemma Agent 推理，也不是公开比赛任务。**
- 初轮集成测试发现同秒、同大小 Python 编辑产生过期 pyc 命中；测试改用 `python -B`，避免缓存影响。同一修复流程随后通过。没有修改官方依赖或绕过断言。
- 初始 google-adk 1.18.0 普通加载器检查通过，随后发现官方使用 1.36.1，已替换为正式沙箱编译器；早期普通加载结果不用于宣称 Harness 兼容。
- CPU 开发依赖安装一度因新 Transformers 更新 click/tokenizers 导致 LiteLLM 版本冲突；固定兼容开发版本后 `pip check` 通过。正式 Notebook 继续使用官方完整 GPU wheelhouse。
- Kaggle Notebook 所有代码单元 AST 解析成功；输出与执行计数清空，未冒充已经运行。

原始检查日志保存在 `docs/validation/check.log`；环境重复安装、依赖和构建日志也保存在同目录。ZIP 摘要见 `docs/validation/build.json`。

## 未完成与后续门禁

1. 参赛账户读取并核对完整规则、HARNESS_README 与 sample；目前无法声称规则已全部审核。
2. 在 Kaggle GPU 使用指定 Gemma 4 31B、官方 vLLM 和 Evaluator 跑至少一个真实公开任务，检查显式 submit_patch 和 Phase 2 结果。
3. 验证 Notebook 中数据挂载路径与当前 Harness 版本一致，保存真实轨迹。Notebook 集成操作可用，不等于已在 Kaggle 验证。
4. 最后才进行官方比赛提交。当前没有公开任务通过数、排行榜分数或正式评测结果。

本地可开发、打包、编译与测试；Gemma 实际完成 issue 修复的能力仍未验证。Codex 仅用于仓库实现，没有充当正式评测模型。
