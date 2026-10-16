# Harness V2 开发运行及归因

这些结果用于验证基础设施，不构成V0/V1配对对照或排行榜成绩。Pilot 01保持原样，未补跑或拼接。

## 2.0.0 / infra-dev-01 / r07 / GPU Notebook v1

2026-10-15 23:18（UTC+8）完成。指定官方31B v2、4×L4，使用已通过31项官方Linux CPU测试的核心运行时。注册：`registrations/r07-gpu.json`。

| 预指定任务 | 实际状态 | 官方验证 | 调用与耗时 | 证据 |
| --- | --- | --- | --- | --- |
| requests_7315 / V0 | resolved | 原始resolved=true，exit=0，1 passed | 17次官方LLM调用、15次工具；官方264.408秒、控制器277.558秒 | 非空Patch 1534字节，在Phase 2前保存；完整边界Trace、增量事件和测试输出；进程停止、清理确认 |
| rich_3777 / V1 | unknown | 导入阶段ImportError，没有官方TaskResult、Patch或Phase 2 | 控制器4.009秒；官方调用计数缺失，不能写0 | worker_top_exception及stderr保留；进程停止，清理未确认；阻止继续接纳 |

基础设施门禁未通过。不得将这两道不同任务计算为V0/V1成功率，也不能将Notebook COMPLETE解释为两道任务完成。第一题是指定Gemma的真实官方单题通过记录；整批环境完整性不足，不能用于比较候选。

上下文探针：tokenizer和生成接口均为19输入token，指定模型返回2输出token。超限探针总预留37428（20020+16384+1024）在生成前被拒绝。第一题18次准入均在预算内，最大输入8389、最大总预留25797；官方LLM计数17与准入次数不完全相同，保留两个原始口径。

### 跨题依赖污染的证据与边界

确认事实：两个沙箱的stderr均记录ensurepip失败并回退；第一题官方流程包含裸`pip install ... -e /workspace`，第二工作进程在导入google.auth.transport.requests时找不到requests。原始第一题Agent工具轨迹中没有pip安装命令。第一题退出时目录清理和进程树停止均为true，说明这些字段不足以证明共享Python包未被改变。

源码支持的机制：swegemma0.2.11的SubprocessManager.start()允许回退venv通过system site-packages导入pip，却不保证venv/bin中存在pip入口；exec()的PATH下一项为宿主Python目录。官方install_editable_package()使用裸pip，因此可能执行带宿主解释器shebang的入口，令editable安装指向随后被删除的工作目录。这是最符合现有证据的原因；旧运行未记录pip解析后的绝对路径或包删除前后快照，不能声称已从旧Trace直接观测到每个卸载动作。

2.0.1新增独立回归复现同一fallback条件，在可丢弃父venv中安装夹具版本，再让沙箱安装另一版本，核验父venv与下一沙箱未变；不对本机或Kaggle全局requests做破坏性卸载。pip和pytest入口均绑定沙箱Python，先核验sys.prefix；失败则禁止开始安装。它处理已知PATH/解释器缺口，不把本地subprocess沙箱称为操作系统级安全隔离。

### 原始文件

`artifacts/harness-v2/r07/gpu-output/files/harness_v2_gpu/20261015T150057_240641Z.zip`：169373字节，SHA-256 `37dc4ad905a01210bfe7d89bc74b689388facc48e807adc7440875f1b9b07aa1`。

ZIP CRC、全部24项注册源码及证据manifest均已核验。只读审计在 `results/r07-gpu-audit.json`，完整原生日志在同级 `gpu-output/native-kernel.log`。第二题原始failure_stage为null，事后从明确的worker_top_exception定位为worker bootstrap；原记录没有被回写。2.0.1提前记录prepare_agent/worker_bootstrap并修复该归因缺口。

## 2.0.1 / infra-dev-02

这是新的开发实验，重新执行CPU门禁；相同两道开发题仅用于验证环境链路。r08增加pip隔离；r09再将共享pytest启动脚本绑定沙箱Python，避免裸pytest使用宿主解释器读到错误包。每一修订保留独立注册、源码哈希和输出，不覆盖r07，也不把新旧记录拼成一个完整对照。当前实际门禁及后续执行结果见 `VALIDATION.md`。
