# 收尾与提交审计

|任务/臂|显式成功submit|首次成功完成秒|fallback|最终无关诊断文件|
|---|---:|---:|---|---:|
|Rich A|0|N/A|是|1|
|Rich B|1|457.13|否|5|
|FastAPI B|3|135.08|否|0|
|FastAPI A|1|122.89|否|0|

按任务计的显式提交比例A1/2、B2/2；不可把B的4次调用当4题成功。
Rich B行239–244做git diff并成功提交；A工具预算耗尽，无submit，Harness捕获工作树。
FastAPI B行91–96做git diff --check并提交，107–108、119–120重复提交。
三个submit返回完全相同391字节/1文件，相关源码在39.63秒后未再修改；无证据证明后两次提交有新增修复价值。
首次成功submit到Agent结束B约74.42秒，A约0.51秒。最后一次B提交后还约17.15秒才终止；不能把submit工具返回当成会话已经结束。

诊断污染：

- Rich A最终包含reproduce_notes.py。
- Rich B最终包含output.txt（ANSI渲染输出）、repro.py、reproduction.py、standard_traceback.py、standard_traceback_multi.py，另有真实生产rich/traceback.py。
- Rich B工作区还有test_notes_capture.py；官方过滤后未进入最终Patch。
- FastAPI B修改了本地tests/test_tutorial/test_metadata/test_tutorial001_1.py，运行其测试；官方submit只捕获文档示例源码，测试修改不在最终391字节Patch。

这不是研究者修改Verifier或评分测试：原生Phase2在独立sandbox按固定Task测试补丁执行，JUnit/命令/原始TaskResult均保存。
但B的本地测试已被改动，应据实披露，不称为“未经修改的既有测试全通过”。
四臂均未观察到删除自己诊断文件的动作。B提升了观察到的显式提交任务比例，但没有达成诊断清理目标；Rich的污染文件从1增加到5。
原生21 passed/1 skipped或2 passed不能消除这些Patch卫生问题，也不能证明未运行的所有旧行为无回归。
