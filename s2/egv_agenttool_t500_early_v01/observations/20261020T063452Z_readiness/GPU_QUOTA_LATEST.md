# GPU 配额与资源快照

实际查询：2026-10-20T06:35:49.313958+00:00（北京时间 14:35:49）。原始 HTTP 200 响应见
[wire_GetAcceleratorQuotaStatistics.json](wire_GetAcceleratorQuotaStatistics.json)。

| 原始字段 | 数值（报告配额秒） |
|---|---:|
| totalTimeAllowed | 108000 |
| timeUsed | 20805.644 |
| timeReserved | 0 |
| 可用差额 | 87194.356 |
| 冻结协议要求 | 20600 |
| 高于要求的余量 | 66594.356 |

**Quota Go。** 当前余额约为 24.221 个“报告配额小时”，约覆盖阈值 4.23 倍。
这些是平台 Duration 计账单位，不能当成 4×L4 的 GPU 设备小时或可用墙钟时间。
下一次重置为 2026-10-24 00:00 UTC（北京 08:00）。当前并未进入新周期：已用量与旧快照相同。

## 为什么此前显示只剩约 794 秒

当前 Kaggle 2.2.2 / kagglesdk 0.1.35 的原始 HTTP 总额是 **108000s**，不是21600s。
typed timedelta 为 1天6小时；SDK 的 TimeDeltaSerializer._to_dict_value 使用 `.seconds` 丢掉整天，
把总额错误格式化为21600s；小数又输出为 `20805.644.0s`。
这是可复现的客户端序列化缺陷，不是已经证明的配额新赠送或周期重置。
[SDK_DURATION_SERIALIZER.txt](SDK_DURATION_SERIALIZER.txt) 保存实际安装源码；
[DURATION_REGRESSION.log](DURATION_REGRESSION.log) 的3项离线测试验证 raw/typed 解释一致、
SDK错误重现、异常字符串拒绝及余额计算。没有修补 SDK，也没有“修正”历史响应。

## 设备、窗口与同时运行情况

- 最新只读 get_kernel 返回旧 Smoke 保存版本的 machineShape=NvidiaL4、模型v2、固定Docker摘要。
  历史真实轨迹证明那次获得4×L4；**当前4×L4即时可分配性 UNKNOWN**，未为探测而分配GPU。
- 官方 [Notebooks文档](https://www.kaggle.com/docs/notebooks) 搜索索引显示一般CPU/GPU窗口12小时，
  大于10000秒规划；直接打开页面未取得正文。它不能保证本账户当前L4保存版本获批的窗口。
- SDK可发送 `session_timeout_seconds` 整数和 `machine_shape`，但当前只读SDK没有实时机器配额/并发槽位/保存频率限制接口。
  请求参数可用不等于平台接受或容量可用；当前最大窗口、保存/启动限制均未完整核实。
- own saved-Notebook列表共165项、分页耗尽。77个成功状态查询均为终态（61 COMPLETE、16 ERROR）；
  其余88项未确认，其中83次429、4次其他HTTP错误、1次ValueError。没有重试风暴或持续轮询。
  关键Early CPU02、env01、旧GPU Smoke及正式打包Notebook均COMPLETE。
  该接口仅覆盖最近保存会话，不覆盖所有交互会话，故**全账户无并发运行 UNKNOWN**。
- GPU草案slug未出现在该保存Notebook清单；本轮未push/save/start。reserved=0不能证明没有任何运行会话。

**完整 GPU Resource No-Go（待机器及会话准入），不是配额不足。**
Execution Not Authorized。不能因为配额数字足够而把 UNKNOWN 字段填成已通过。
