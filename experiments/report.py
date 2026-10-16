"""Render a report only from an audited real pilot, never from fixtures."""
import json
from experiments.prepare import ROOT, write_new


def number(value, digits=1):
    return '未测得' if value is None else f'{value:.{digits}f}'


def rate(value):
    return '未完成' if value is None else f'{value:.1%}'


def render():
    directory = ROOT / 'experiments/results/pilot-01'
    audit = json.loads((directory / 'result_audit.json').read_text())
    records = json.loads((directory / 'raw_comparison_records.json').read_text())
    summary = audit['summary']
    lines = ['# V0/V1 真实配对pilot结果', '',
        f"Run ID：`{audit['run_id']}`；Notebook第{audit['kernel_version']}版。",
        f"预定{summary['planned_runs']}次，实际记录{summary['observed_runs']}次；完整：{summary['complete']}。",
        f"实际候选提示/指定模型校验：{audit['treatment_integrity_confirmed']}；V0原始{audit['original_v0_files_unchanged']}项哈希不变。", '',
        'Kaggle平台COMPLETE只表示Notebook已退出。本轮实验未完成：外层超时后按预注册规则停止，剩余运行未执行。两个有完整Trace的运行均通过提示与指定31B v2模型校验；第3次缺失Trace，无法确认其实际处理变量。', '',
        '| 指标 | V0 | V1 |', '| --- | --- | --- |']
    arms = summary['arms']
    for label, key, formatter in [
        ('Resolution Rate', 'resolution_rate', rate),
        ('Patch可应用有效率', 'patch_validity_rate', rate),
        ('收集失败率 / 全部预定任务', 'collection_failure_rate_all_planned', rate),
        ('收集失败率 / 已调用验证', 'collection_failure_rate_invoked', rate),
        ('Phase2调用次数', 'phase2_invoked', str),
        ('平均模型调用', 'mean_llm_calls', number),
        ('平均计费工具调用', 'mean_tool_calls', number),
        ('平均单题秒数（不含共同启动）', 'mean_duration_seconds', number),
        ('平均观测累计Token', 'mean_observed_total_tokens', number),
        ('显式超时次数', 'timeouts', str),
        ('控制器执行异常次数', 'errors', str),
        ('官方结果error非空次数', 'official_error_runs', str)]:
        lines.append('| ' + label + ' | ' + ' | '.join(formatter(arms[a][key]) for a in ('v0', 'v1')) + ' |')
    lines += ['', '## 逐任务官方结果', '', '| 任务 | 版本 | resolved | 测试退出码 | collection失败 | LLM / 工具 | 秒 |', '| --- | --- | --- | --- | --- | --- | --- |']
    for r in records:
        resolved = str(r.get('resolved')) if not r.get('execution_error') else '控制器false；官方未知'
        collection = str(r.get('collection_failed')) if r.get('phase2_invoked') else '未测得'
        lines.append(f"| `{r['instance_id']}` | {r['arm']} | {resolved} | {r.get('test_exit_code', '未测得')} | {collection} | {r.get('total_llm_calls')} / {r.get('tool_calls')} | {number(r.get('duration_seconds'))} |")
    pair = summary['paired']
    lines += ['', f"完整配对{pair['n']}个；V1独胜{pair['v1_only_resolved']}个，V0独胜{pair['v0_only_resolved']}个。", '', '## 是否继续优化', '']
    ratios = {}
    for key in ('mean_llm_calls', 'mean_tool_calls', 'mean_duration_seconds', 'mean_observed_total_tokens'):
        v0, v1 = arms['v0'][key], arms['v1'][key]
        ratios[key] = v1 / v0 if v0 is not None and v0 > 0 and v1 is not None else None
    errors = sum(arms[a]['errors'] for a in ('v0', 'v1'))
    if not summary['complete'] or not audit['treatment_integrity_confirmed'] or errors:
        conclusion = '本轮不支持版本优劣结论，暂不替换V0。建议继续优化实验可靠性：先解决上下文容量与输出预留冲突、超时后的证据落盘和取消隔离，再登记共同Harness修订并运行新的完整配对。当前候选与本轮所有失败结果保留；不能静默更改已执行方案或只补最有利的运行。'
    elif arms['v1']['resolved'] > arms['v0']['resolved'] and all(v is not None and v <= 1.25 for v in ratios.values()):
        conclusion = '达到预注册的扩大样本信号：V1净多解决至少1题，且观测资源均值均未超过25%门槛。建议固定候选，在更多未看过任务和重复运行上继续验证；不建议凭4题直接替换V0或声称总体泛化。'
    elif arms['v1']['resolved'] > arms['v0']['resolved']:
        conclusion = 'V1解决数增加，但未满足全部资源门槛或Token观测不完整。建议继续做成本消融和更大样本验证，暂不替换V0；不在本批任务上继续调到通过。'
    else:
        conclusion = '本轮没有证明V1解决率优于V0。暂不替换V0；建议保留候选，优先用更短的契约/验证提示做预注册消融，并扩展未看过任务。即使过程指标改善，也不能当成修复率提升。'
    lines += [conclusion, '', '已观测运行的V1/V0资源均值比：' + '；'.join(f'{k}={number(v, 3)}' for k, v in ratios.items()) + '。', '',
        '本轮均值分母不对称：V0只有1条，V1有1条完成记录和1条被截断的超时记录；Token只各有1条。以上比值仅是原始描述，不能用于25%成本门槛或优劣判定。唯一完整任务配对中，V1/V0模型调用64/38、计费工具60/38、耗时401.8/351.5秒、观测Token517411/341512，均无题目解决；这也不足以归因于提示词长度。', '',
        '## 失败审计与缺失记录', '',
        '- V0 / rich_3777：38次读取或命令调用后，官方结果报告ContextWindowExceededError；服务配置32768上下文，请求预留16384输出，输入至少16385。没有编辑、Patch或Phase2。上下文压缩为何未能及时生效尚未验证。',
        '- V1 / rich_3777：非空1867字节Patch被应用，Phase2退出1，98 passed / 1 failed。实现绕过实例环境接口，使用全局环境；自写happy path通过却没有覆盖既有依赖注入契约。Trace中还出现过度转义导致的SyntaxError、只读属性赋值错误，修复这些错误消耗工具预算。',
        '- V1 / rich_4006：约483秒Harness记录Agent超时，并记录捕获690字节fallback Patch和启动验证沙箱；720秒外层截止先于最终结果落盘。缺少result、Trace、Patch及Phase2输出，因此官方resolved、可应用性、测试收集状态均未知。原始控制器记录中的false只是保守占位，不能证明未启动验证或没有Patch。',
        '- 未执行：V0 / rich_4006；V0和V1 / fastapi_15589；V1和V0 / requests_7315。未完成多类型对照。', '',
        '逐事件依据、证据缺口及后续修订建议见[本轮审计](PILOT_01_AUDIT.md)。', '',
        '## 解释限制与原始证据', '',
        '原计划为4道按公开标题选择的任务、3个仓库、每版本一次运行的探索性pilot；实际只尝试2题，完成1个配对。任务不是总体的随机样本。顺序按预注册种子固定并平衡版本冷热顺序，但采样随机性、服务缓存和任务相关性仍存在。不能声称统计显著或总体提升。历史已审计任务未混入分母。', '',
        'Patch有效仅指非空Patch进入官方验证测试命令，不能等同功能正确；收集失败与未启动验证分别报告。原始first_task_goal_completed/phase2_tests_ran只表示证据包络，汇总不使用它们来判定解决。显式超时从实际异常/退出码判断，不用耗时猜测；所有原始记录均可检查。Token是Trace逐调用累计，不是唯一上下文长度或GPU总计费。', '',
        f"完整原始目录：`{audit['local_original_evidence_directory']}`。", f"证据ZIP SHA-256：`{audit['evidence_zip_sha256']}`。", '',
        '- [原始逐次记录](results/pilot-01/raw_comparison_records.json)',
        '- [汇总与处理变量核验](results/pilot-01/result_audit.json)',
        '- [全部下载文件的大小与SHA-256](results/pilot-01/download_manifest.json)',
        '- [预注册方案](PLAN.md)',
        '- [冻结任务顺序与候选哈希](preregistered.json)', '',
        '完整Trace、Patch、stdout/stderr、GPU/模型路由、安装与服务日志保留在本地新目录及账号私有Notebook Output；不发布完整任务输入或验证测试内容。没有排行榜提交或排行榜成绩。', '']
    write_new(ROOT / 'experiments/RESULTS.md', '\n'.join(lines).encode())
    return conclusion


if __name__ == '__main__':
    print(render())
