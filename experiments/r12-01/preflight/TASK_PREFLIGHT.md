# 三题 CPU 预检
本报告的 PASS 表示可用于修复评估：未修改的原始行为应失败，正向控制应通过。它不表示 R1/R2 修复成功。
最终 Gate：**R12_PREFLIGHT_PARTIAL**。CPU 归档 SHA256：`a553bcd5150eecd6a6d92dc6d7555f8f88035e43111ed69b2d1557582102227b`；CRC 与上传扩展代码哈希已核对。
附件中的 `pytest__pytest-5631` 是名称差异；锁定 ID 保持 `pytest-dev__pytest-5631`，未换题、未改顺序。
来源：SWE-bench/SWE-bench_Verified，冻结版本 `78f471bf655a3137b2e8a75af1501690ec009ec3`，Parquet SHA256 `030cfd7f2a704c4c0226e7f104c725a3b41230b1d3517f9c915ad7ea5be3fa25`。仅投影允许的公开 Issue/仓库/base/ID；未读取参考修复、官方 Test Patch、隐藏测试或 hints。原始 Issue 文本以此数据版本为来源，没有另行打开可能包含参考修复的原始 PR。

## django__django-11964：PASS
- 仓库 `django/django`，base `fc2b1cc926e34041953738e58fa6ad3053059b22`；完整 Git tree 核对：True。源码包 SHA256 `db91d169474e7c279053b567fe072b34116f34c164b087e3e7777ea483efa35d`；原始源码内容 SHA256 `6efe8a6fa12b42d7917fc33f2e9480e094d6de9926bb513c89a9fbf580a3779d`；Issue SHA256 `9f510b2ad7d3833f07816f18dfa6dbb8dacf72061c288cfe399418bfe4da25ab`。
- 实际入口：python tests/runtests.py --help；独立 Python 行为检查使用真实 SQLite 模型。可执行：True。只验证目标所需依赖和入口，未声称完整项目测试套件可运行。
- 原始声明：Python>=3.6; pytz, sqlparse, asgiref。固定基础依赖：`{'pytz': '2025.2', 'sqlparse': '0.5.3', 'asgiref': '3.8.1', 'setuptools': '75.8.0'}`；额外任务依赖：`{}`。版本与来源哈希记录，不为目标行为改源码。
- 原始 Bug 复现：True；正向控制：True。
- Agent 无法读取/修改检查：True；独立评估副本的检查只读且哈希不变：True/True；测试不改变源码：True；清理：True。
- 旧记录分类：AUDITED_NOT_PREVIOUSLY_USED，仅限已审计本地运行/训练记录；三题均出现在旧的仅哈希排序元数据中，未发现旧运行准入。外部研究/模型训练和未穷尽压缩历史属于 EXPOSURE_UNKNOWN。
  - control: `retrieved_database_values` → PASS
  - control: `choice_values_and_labels` → PASS
  - target: `fresh_text_field_string_value` → FAIL（原始目标应失败）
  - target: `fresh_integer_field_string_value` → FAIL（原始目标应失败）

## pydata__xarray-6721：PASS
- 仓库 `pydata/xarray`，base `cc183652bf6e1273e985e1c4b3cba79c896c1193`；完整 Git tree 核对：True。源码包 SHA256 `7112e16f969863e9b4811a03715dbfbe647a0962372a642bb5fe99cd54b9a148`；原始源码内容 SHA256 `2696e6b83b4cff000cf60139fb33588293e89242970573fc44208bf42782f877`；Issue SHA256 `8885a8e303e07d8e74f13a24134ecd7d051a2e2ded38ac313d6667e68b93a021`。
- 实际入口：python -m pytest --version；独立检查调用真实 zarr、dask 和 xarray 源码。可执行：True。只验证目标所需依赖和入口，未声称完整项目测试套件可运行。
- 原始声明：Python>=3.8; numpy>=1.19, pandas>=1.2, packaging>=20.0; selected io/parallel extras zarr, fsspec, dask。固定基础依赖：`{'pandas': '2.2.3', 'pytz': '2025.2', 'six': '1.17.0', 'tzdata': '2025.2', 'numpy': '1.26.4', 'setuptools': '75.8.0', 'python_dateutil': '2.9.0.post0', 'packaging': '24.2'}`；额外任务依赖：`{'asciitree': '0.3.3', 'click': '8.1.7', 'cloudpickle': '3.0.0', 'dask': '2024.6.2', 'fasteners': '0.19', 'fsspec': '2024.6.1', 'locket': '1.0.0', 'numcodecs': '0.12.1', 'partd': '1.4.2', 'PyYAML': '6.0.2', 'toolz': '0.12.1', 'zarr': '2.18.3'}`。版本与来源哈希记录，不为目标行为改源码。
- 原始 Bug 复现：True；正向控制：True。
- Agent 无法读取/修改检查：True；独立评估副本的检查只读且哈希不变：True/True；测试不改变源码：True；清理：True。
- 旧记录分类：AUDITED_NOT_PREVIOUSLY_USED，仅限已审计本地运行/训练记录；三题均出现在旧的仅哈希排序元数据中，未发现旧运行准入。外部研究/模型训练和未穷尽压缩历史属于 EXPOSURE_UNKNOWN。
  - control: `real_zarr_values_and_counter` → PASS
  - control: `eager_numpy_chunks` → PASS
  - control: `real_dask_chunks` → PASS
  - target: `zarr_chunks_metadata_does_not_load_data` → FAIL（原始目标应失败）

## pytest-dev__pytest-5631：PASS
- 仓库 `pytest-dev/pytest`，base `cb828ebe70b4fa35cd5f9a7ee024272237eab351`；完整 Git tree 核对：True。源码包 SHA256 `160415366a032d5701056064cbdfc5f5b59c2321fbff973dc4f012418e855fb9`；原始源码内容 SHA256 `615f570627b277f0ad10fd054ff045d3f0a28718a34a9ea2fbae947e1c43af01`；Issue SHA256 `1e9120fbb21d881c388af3596eaa479bad2f604703eb79bd19898b5d7b18af03`。
- 实际入口：python -m pytest、pytest；真实源码框架收集并运行 /evaluation 下的独立测试，--assert=plain，禁用外部插件。可执行：True。只验证目标所需依赖和入口，未声称完整项目测试套件可运行。
- 原始声明：Python>=3.5; py>=1.5, packaging, attrs>=17.4, more-itertools>=4, atomicwrites>=1, pluggy>=0.12,<1.0, importlib-metadata>=0.12, wcwidth; build setuptools>=40 and setuptools-scm。固定基础依赖：`{'pandas': '2.2.3', 'pytz': '2025.2', 'six': '1.17.0', 'tzdata': '2025.2', 'numpy': '1.26.4', 'setuptools': '75.8.0', 'python_dateutil': '2.9.0.post0', 'packaging': '24.2'}`；额外任务依赖：`{'atomicwrites': '1.4.0', 'attrs': '23.2.0', 'importlib-metadata': '6.11.0', 'more-itertools': '10.3.0', 'pluggy': '0.13.1', 'py': '1.11.0', 'wcwidth': '0.2.13', 'zipp': '3.19.2'}`。版本与来源哈希记录，不为目标行为改源码。
- 原始 Bug 复现：True；正向控制：True。
- Agent 无法读取/修改检查：True；独立评估副本的检查只读且哈希不变：True/True；测试不改变源码：True；清理：True。
- 旧记录分类：AUDITED_NOT_PREVIOUSLY_USED，仅限已审计本地运行/训练记录；三题均出现在旧的仅哈希排序元数据中，未发现旧运行准入。外部研究/模型训练和未穷尽压缩历史属于 EXPOSURE_UNKNOWN。
  - control: `native_collection_default_mock_and_plain_function` → PASS
  - target: `native_collection_with_array_new` → FAIL（原始目标应失败）
- pytest 正常构建元数据：5.0.2.dev58+gcb828ebe；由官方声明的 setuptools-scm 8.2.0 生成 `.gitignore` 排除的 `_version.py`。原始文件逐字节核对未变；该构建产物在测试前纳入可执行基线，测试后仍未变。
- 默认项目环境：`{'PYTHONPATH': '/workspace/src:/opt/task:/opt/approved', 'PYTEST_ADDOPTS': '--assert=plain', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'reason': 'Original assertion rewriting AST is incompatible with Python 3.12; plain executes all Python assertions without enhanced rewriting.'}`。旧断言重写器与 Python 3.12 AST 不兼容，使用原生 `--assert=plain`；失败断言校验仍会 exit 1 且报告失败：True。未跳过目标或正向测试，未修改断言预期。

## 环境修复与边界
CPU v1：Django 缺声明依赖 pytz，pytest 缺归档不携带的构建元数据；xarray 通过。CPU v2：从已有固定依赖恢复 pytz 后 Django/xarray 通过；pytest 的 SCM 归档插件发现失败。后续改为对已核实的 Git tag/commit 元数据直接调用 SCM 写版本文件，并恢复 src 布局和项目声明的 pytest:main 默认入口。检查代码及其预期自 v1 起保持相同 SHA256。所有尝试保留，未做 Gemma 推理。
CPU v3：构建与行为检查已恢复，pytest 默认启动因旧断言重写 AST 报错 `required field lineno missing from alias`。CPU v4 仅用原生环境选项 --assert=plain 解决重写兼容，并验证失败断言仍失败。原始 Issue 检查文件 SHA256 始终为 b46f783792cb6c2019f2af50279dcff123828f806b0542babf2836bcc92bb667；所有早期阻断记录保留。
依赖来源及版本见 NEW_DEPENDENCIES.json、SCM_BUILD_TOOL_PROVENANCE.json；Django pytz 复用旧私有固定依赖包。原始源码均来自 GitHub 指定 base 的归档，以 Git tree 完整核对；xarray 仅恢复 Git export-subst 展开的 .git_archival.txt 为原始 blob。
Agent 与可信评估使用不同非 root chroot、不同源码副本和生命周期。Agent 副本没有 /evaluation、宿主输入、轨迹或可信脚本；网络 socket 被拒绝。只有评估副本才放入检查，并验证其不可写、内容未变。
研究环境保证固定源码、候选、依赖及原生工具/预算；官方兼容证据为三包官方 SDK 编译成功、固定 Gemma 4 v2 与此前真实运行版本。完整官方沙箱、项目依赖、上下文压缩/缓存策略与历史打分端的等价性仍未验证，不能把环境修复算作 Agent 算法收益。
