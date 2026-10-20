# 查询范围与限制

query_kaggle.py执行了一次配额查询、一次提交列表、own保存Notebook完整分页以及每个返回ref的一次状态查询；随后只读取得旧GPU Smoke的保存版本metadata。
没有save_kernel/create_kernel_session/cancel_kernel_session/competitions submit调用。
GetAcceleratorQuotaStatistics的HTTP POST是只读RPC，不是资源申请。
所有请求设置30秒timeout；没有在限流后反复补查或启动后台轮询。

原始SDK字段使用camelCase；notebooks列表返回slug为空、ref有效。因此逐项status_*.json文件名碰撞成status_.json。
该单文件仅保留最后一次错误，不能用作完整会话审计；完整逐ref响应与时间均在notebook_statuses.json聚合记录中，没有丢失该聚合。
原执行脚本保持原样以便追溯；不建议直接重跑其全账户165次状态批次。后续准入应使用平台只读session管理或有限、顺序、遇429即停止的查询。
该执行失误与官方Agent/模型HTTP观察器无关，未修改任何研究执行器。

sdk_surface.json记录实际安装版本和可调用端点名称；SDK_KERNEL_PUSH_SOURCE.txt是本机已安装CLI的只读源码摘录（保存完整函数以核查参数），从未调用该写接口。
SDK_DURATION_SERIALIZER.txt为实际安装的序列化类源码；DURATION_REGRESSION.log证实days丢失及小数格式异常。

一般窗口资料：https://www.kaggle.com/docs/notebooks 、https://www.kaggle.com/docs/efficient-gpu-usage ，2026-10-20查询。
前者官方搜索索引显示CPU/GPU一般12小时；直接open两页均只返回标题、无正文。因此只作规划参考，不作为当前账户或NvidiaL4精确最大窗口证明。
未登录新的浏览器账号、未开启Notebook编辑器会话来尝试分配资源。
get_kernel旧版本的machineShape=NvidiaL4只证明保存配置，不证明即时库存；reserved=0不证明所有交互会话已结束。
后端推理日志和实时4L4硬件无法在本轮无GPU边界内实测，保持UNKNOWN/NOT_RUN。
