# inline_snapshot：已声明、运行时不可用、批准 wheel 缺失

原始 traceback：新增 tutorial 测试第6行导入 ...utils；冻结 tests/utils.py:5 导入 inline_snapshot.Snapshot，发生 ModuleNotFoundError。对应发行包在 requirements-tests.txt:13 明确声明为 inline-snapshot>=0.21.1。两份文件的字节都匹配 CPU02 工作区前后哈希。因此它是已声明但未供给当前测试解释器的依赖，分类为 DECLARED_BUT_NOT_INSTALLED；不是 UNDECLARED_TEST_DEPENDENCY。是否存在于其他未使用位置，现有证据不能回答。

pyproject.toml 的 standard、standard-no-fastapi-cloud-cli、all extras 都不包含 inline-snapshot。[tool.inline-snapshot] 是工具配置，不是安装声明。requirements-tests.txt 虽包含 -e .[all]，还必须单独安装其中的 inline-snapshot 行；仅开启 all extra 不足以解决。

实际供给链如下：

1. Notebook 用 --no-index --no-deps --force-reinstall 安装41个批准的非 cutlass 官方 wheel。installation.log 没有 inline-snapshot 安装记录。
2. 与 CPU02 SHA 一致的 swegemma0.2.11 中，install_test_dependencies 对 SubprocessManager/SubprocessSandbox 直接 return，见 official_source/swegemma/harness/container_setup.py:529-530。不能把这条研究 subprocess 路径的行为推断成未观测过的正式评分 Docker 环境行为。
3. 研究适配器 s1/infrastructure_recovery/environment.py:46-72 仅补装 build-system.requires（实际为 pdm-backend2.4.9，exit0），再执行 --no-index --no-build-isolation --no-deps -e /workspace。它不处理 requirements-tests.txt。ensurepip 曾失败，但后续构建和 editable 安装成功，不能把 ensurepip 警告当成 inline_snapshot 缺失的完整原因。
4. CPU02 已归档的41个官方 wheel、124个任务 wheel，按发行名规范化后均无 inline-snapshot。结论是 APPROVED_WHEEL_UNAVAILABLE / OFFLINE_DEPENDENCY_RECOVERY_UNAVAILABLE，限于本实验冻结批准资源；不是宣称整个比赛永远禁止官方提供新依赖。

实际 sandbox Python 为3.12；FastAPI base 的 Requires-Python>=3.8允许它。缺失包没有可用批准 wheel，所以其 wheel SHA、Python/ABI标签、Requires-Python、实际版本和传递依赖均为 UNKNOWN/null，不能声称 VERSION_INCOMPATIBLE，也不能假装已证明完整兼容。当前相关安装命令用 --no-deps，且没有尝试安装该包，因此没有证据支持“解析冲突导致安装失败”。实际 pytest 版本同样未捕获，批准清单中的版本不等于已安装版本。

根因包含两层：研究 subprocess 环境准备没有安装上游测试 requirements；冻结离线资源也没有所缺包。只改安装步骤仍无法离线取得不存在的 artifact。目前 ENVIRONMENT_RECOVERY_BLOCKED，不值得原样重复 CPU02。本轮未联网安装、未下载额外 wheel、未修改测试或 Verifier。
