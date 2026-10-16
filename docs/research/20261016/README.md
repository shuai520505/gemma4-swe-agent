# 研究证据索引

本目录只保存研究文档所需的小型证据与复查程序，不进入任何候选ZIP。

- `v19-static-audit.json`：原始载荷ZIP CRC、11成员SHA、Notebook可读文件与导出字节一致性。完整外部源码/ZIP保存在本机独立目录 `artifacts/research-20261016/`；没有执行外部脚本或将外部Prompt提供给Agent。
- `v19-downloads.json`：Kaggle CLI下载记录。过滤output只取到log，ZIP从原公开脚本的base64常量恢复；不声称下载了私有评分产物。
- `dataset-revisions.json`：五个Hugging Face数据源实际revision、数据卡SHA及版本化URL；未加载/验真全量数据。
- `wheelhouse-audit.ipynb` / `wheelhouse-kernel-metadata.json`：新CPU只读审计的源文件；Kaggle版本1 COMPLETE，非正式比赛提交，没有GPU/训练。
- `wheelhouse-audit.json` / `.log`：七个关键Wheel和57个源码文件的原始哈希/命中行。读取ZIP不是安装/运行或HTTP行为验证。
- `wheelhouse-view.json`：官方view API返回当前数据集v31；CLI简化metadata另存 `wheelhouse-dataset-metadata.json`。当前挂载字节身份以SHA为准。
- `wheelhouse-comparison.json`：七Wheel与旧S0实际SHA全部相同；四个重合的小Wheel也与原有官方下载锁相同。旧r12仅版本记录不能证明全部大Wheel历史字节一致。
- `evidence-manifest.json`：本轮小型证据校验清单，不覆盖任何旧实验manifest。
- `verification.log`：本地研究证据/冻结完整性检查实际输出，不是模型修复成功日志。

在仓库根目录执行 `python docs/research/20261016/verify_evidence.py` 可复查证据、76项原始保留清单（同时调用原39项V0校验）、28项r12源码以及受保护目录相对研究起点的diff。验证程序不调用模型或网络。

如需重取外部源码，可用已授权Kaggle CLI `kernels pull yiyu0716/g4-pack-yiyu-v19-fixed-trace-t7p5` 和 `kernels pull yiyu0716/g4-v19-complete-harness-source`，下载到新的目录后核对SHA；不要执行下载的Notebook。公开最新内容可能变化，本次证据只对应已记载字节。

研究期间V0/V1、S0、r12、Pilot和正式配对协议/原始结果均保持不变；没有新模型训练、GPU修复评测或新的榜单分数。
