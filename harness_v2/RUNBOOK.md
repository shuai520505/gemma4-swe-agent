# Harness V2 开发运行

从仓库根目录运行。这里只构建预指定两道开发题，不生成正式对照或提交排行榜。需要本机已授权Kaggle CLI；凭据不能放入输入bundle。

1. 使用从未使用过的修订名：`python -m harness_v2.build <new_revision>`。构建前检查原始V0和Pilot 01哈希；输出在 `artifacts/harness-v2/<new_revision>/`，注册在 `registrations/`。任何已有文件内容不同都会拒绝覆盖。
2. 在该修订的 `input/` 目录执行 `kaggle datasets version -p . -m "revision note"`，更新已核验私有的输入数据集。不要使用创建公开数据集的参数。若CLI2.2.2的旧上传缓存解析失败，保留旧缓存，在单次CLI进程使用独立上传缓存；不要改动实验bundle或已授权凭据。
3. 在 `cpu-kernel/` 目录执行 `kaggle kernels push -p .`。用 `python -m harness_v2.kaggle_watch <kernel_slug> <fresh_output_directory>` 留存状态、原生日志和原始ZIP。
4. 从真实输出读取 `validation/cpu_gate.json`，检查tests、failures、errors、skips、官方API执行及版本。失败必须保留并使用新revision修正，不能把JSON手工改成通过。
5. 只有完整CPU门禁通过，才执行 `python -m harness_v2.gpu_build <revision> <actual_cpu_gate_json>`。构建器再次核验核心运行时和版本匹配；生成GPU Notebook及预注册哈希。当前GPU必须挂载同一注册bundle，任何输入变化都会停止。
6. 在新修订 `gpu-kernel/` 目录提交Notebook。两题在不同工作进程串行运行；异常、unknown或清理未确认时停止接纳。GPU Notebook COMPLETE只代表Notebook结束，任务是否完成看原始结果与批次门禁。
7. 使用 `python -m harness_v2.audit <original_zip> <revision> cpu` 或 `gpu` 只读核验注册源码、CRC和证据manifest。结果输出到新的 `results/<revision>-<kind>-audit.json`；它不会回写官方字段。超时缺少完整Trace、Patch或验证结果时如实记录。

本机CPU控制器可运行 `python -m unittest discover -s tests -p test_harness_v2.py -v`。官方Linux API、真实六工具及跨沙箱安装回归由CPU Notebook执行；其中脚本化仓库或可丢弃包只用于基础设施测试，不是Gemma修复任务。Windows不执行需要/bin/bash的官方沙箱测试，不能据本机结果放行GPU。

实际执行历史见 `VALIDATION.md` / `RESULTS.md`。正式配对实验必须另行注册任务、实验ID、候选/控制器哈希及两个完整配对批次，不能直接复用开发实验的成功率，也不能补接Pilot 01。
