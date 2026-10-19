# fastapi_15800 原生 CPU 环境准入

CPU01 已在官方固定 Linux 镜像真实执行并通过准入。完整 Compiler→空 State
ADK Runner→模拟 HTTP 兼容与冻结基础设施回归实际115/115通过；不代表模型推理。
最终接受的是独立CPU03：再次完整115/115通过，同一原生基线60项调用失败、0errors，
原生TaskResult、JUnit、导入与清理证据完整；没有拼接三次运行。CPU01先验证原生
环境，CPU02加入最终协调器和插件入口记录，CPU03仅在基线函数内部补强No-Go抛错，
保证GPU入口不能在不合格基线后启动模型。三个准备版本及精确载荷分别保留。

CPU03原始ZIP SHA：12aebe6825033a8be451d9f40f54fecb5f6f2bcb3daf89ca3af1afa98d601c11，
1283442bytes，CRC及795个manifest条目核验通过。实际上传154个源码/配置/候选文件。
CPU02原始SHA:a90226431836d93e060084ec9df7a0a9ff729e277057ae77d732469d183e1e16。
115项包含完整113旧回归及2项真实Compiler/Runner模拟HTTP候选门；没有新增Gemma推理。

## 干净基线

使用未修复快照，agent_patch为空；仅原生 Evaluator 装载原始测试补丁，没有读取
参考修复。任务、Issue、base、整条元数据及测试补丁 SHA 与已有草案完全相同。
快照39db9ef995f8066b5f3cc70a7d8c54325e7bdc4faa9599e76099b533a4e034c0。

快照3442个tar条目中没有tests/test_frontend.py。评估补丁负责增加该文件；
在原生pytest之前，实际Evaluator工作区该文件存在，SHA为
212f404c39ff7c86d546df53a830a7b3fe35449634f635eef873ffca98d3f27b。
故“初始快照缺少目标评估测试”不构成此任务环境缺失。

原生命令保持：python3 -s -m pytest tests/test_frontend.py，带原生JUnit、
PYTHONSAFEPATH=1、PYTHONNOUSERSITE=1、-p no:anyio及其余官方参数。
完整精确命令见test_overlay_before_pytest.json，未添加或删除测试。

实际结果：**60项收集并运行，0通过、60测试调用失败、0setup/collection errors，
exit1，原生resolved=false**。其中44项缺FastAPI.frontend、5项缺APIRouter.frontend、
5项缺APIRouter._low_priority_routes，另6项调用测试发现新frontend教程文件未实现。
这不是60项AssertionError：原生JUnit failure节点包含AttributeError/FileNotFoundError，
分类器assertion_failure表示测试call阶段失败。没有将普通失败当环境故障，也没有
因为字符串含Error而停止。教程文件属于评估所要求的交付内容，未伪造文件或改预期。
测试执行失败与未来实际Agent错误须继续按真实调用链归因。

CPU01原生pytest执行4.262秒；完整TaskResult、stdout/stderr、JUnit、工作区源码SHA、
实际导入路径、清理记录均已保存。JUnit在原生sandbox仍存在时复制，之后清理完成。
原生JUnit SHA:f627c92acbceebb3063321f5ed645fab00727f39f38bc3bfe793d1d64824293b。
原始档案9e2d7528a7e6a8711a64d9fc4dadb1f5319044cac11b63b8f5f28c05a37312d7，
1228343bytes，CRC及790个manifest条目通过。

## 来源与版本

真实导入FastAPI来自独立sandbox/workspace/fastapi，非系统安装FastAPI。
fastapi/__init__.py SHA为bc51e835818dfdeba72e73aad33d7ab57cfe3b7d3db8d0824eb9dd128b982361；
applications.py SHA为5f6555ae17f7b9fa24c35b24dbf67272ecced669f71b1179a9e22263d13e9338。
其余pytest/Pydantic/Starlette/HTTPX来自共享固定镜像site-packages，路径及源码SHA有
被动导入记录。sys.path、executable及实际模块执行记录保留；导入证明不是函数覆盖率。

实际宿主版本swegemma0.2.11、adk-submission0.2.13、google-adk1.36.1、
LiteLLM1.82.4、pytest8.4.2、Pydantic2.12.3、Starlette0.52.1、HTTPX0.28.1。
共享依赖的实际导入路径与宿主分发对应；不根据Wheelhouse文件名臆测生效版本。
CPU02/03额外记录已安装pytest入口点：anyio4.13.0、typeguard4.5.1、langsmith0.7.34。
安装不等于已加载，anyio保持原生命令禁用。

本报告及评估结果只在研究侧，不能进入Agent Prompt、仓库或提交ZIP。
原始resolved保持false；基线不是EGV或Control模型结果。
