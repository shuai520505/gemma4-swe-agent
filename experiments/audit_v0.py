"""Read-only extraction of reproducible V0 audit evidence, never agent input."""
import collections
import hashlib
import json
from pathlib import Path

from experiments.prepare import ROOT, verify_frozen

SUMMARIES = [
    '识别描述为空且外部参考不可访问；将目标解释成通用发布脚本。',
    '读取已有日期脚本。', '再次讨论任务歧义，做全仓release搜索。',
    '追索外部参考名；搜索无可执行契约。', '重复讨论缺失描述，再次宽泛搜索。',
    '首次明确假设新建release.py；查看依赖配置首段。', '在核心库中搜索release，未找到新线索。',
    '再次列全仓目录，命令排除了隐藏目录。', '继续猜测通用检查编排，读取lint入口。',
    '读取测试入口。', '定位版本变量。', '扩展为改版本/说明，读取大量文档管理脚本。',
    '再搜脚本目录。', '重复读取日期脚本。', '重复读取测试入口。', '重复读取lint入口。',
    '提出Typer新脚本与额外选项，仍做宽泛搜索。', '读发布说明布局。',
    '细化自拟功能，再读相同pyproject范围。', '接受Typer可用假设，写入新脚本。',
    '仅执行自拟CLI happy path，显式跳过测试和lint。',
    '关注输出顺序，第三次读日期脚本。', '将顺序疑问归于缓冲，grep检查真实版本文件。',
    '读取真实发布说明的变更结果。',
    '在思考中重述大量代码，考虑后放弃重复版本检查；未实际执行diff即提交。',
    '提交后继续生成最终文本，并把自拟脚本名转述为用户要求；不能证明其输入来源。',
]


def build_audit():
    verify_frozen()
    raw = ROOT / 'artifacts/kaggle-single/output-v2/v0_runs/20261014T161032_870715Z'
    entries = json.loads((raw / 'tasks/001/trace_legacy.json').read_text(encoding='utf-8'))['entries']
    rows = []
    reads = []
    for n, (index, event) in enumerate([(i, e) for i, e in enumerate(entries) if e['type'] == 'thinking'], 1):
        calls = []
        end = next((i for i in range(index + 1, len(entries)) if entries[i]['type'] == 'thinking'), len(entries))
        for i in range(index + 1, end):
            e = entries[i]
            if e['type'] != 'tool_call':
                continue
            args = dict(e['args'])
            if e['tool'] == 'write_file':
                args = {k: v for k, v in args.items() if k != 'content'}
            response = entries[i + 1]
            value = json.loads(response['result'])
            result = {k: value[k] for k in ('status', 'exit_code', 'start_line', 'end_line', 'total_lines', 'is_truncated') if k in value}
            if e['tool'] == 'read_file':
                reads.append(dict(event=i, path=e['args']['filepath'],
                    sha256=hashlib.sha256(value['content'].encode()).hexdigest()))
            calls.append(dict(event=i, response_event=i + 1, tool=e['tool'], args=args, result=result))
        rows.append(dict(model_call=n, event=index, elapsed_s=event['elapsed_s'],
                         usage=event.get('usage', {}), interpretation=SUMMARIES[n - 1], calls=calls))
    usage = {k: sum(e.get('usage', {}).get(k, 0) for e in entries)
             for k in ('prompt_tokens', 'completion_tokens', 'total_tokens', 'cached_tokens')}
    report = dict(event_indexing='zero-based entries[] in trace_legacy.json',
        trace_sha256=hashlib.sha256((raw / 'tasks/001/trace_legacy.json').read_bytes()).hexdigest(),
        event_counts=dict(collections.Counter(e['type'] for e in entries)), usage_sum=usage,
        read_paths=dict(collections.Counter(r['path'] for r in reads)),
        repeated_identical_reads=len(reads) - len({(r['path'], r['sha256']) for r in reads}), rows=rows)
    out = ROOT / 'docs/validation/v1'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'v0-event-audit.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    table = ['| 模型调用 | Trace事件 / 秒 | 工具与返回证据 | 解释 |', '| --- | --- | --- | --- |']
    for row in rows:
        desc = []
        for call in row['calls']:
            args = call['args']
            action = args.get('command', args.get('filepath', '{}')).replace('|', '\\|').replace('\n', ' ')
            result = call['result']
            flags = f"exit={result['exit_code']}" if 'exit_code' in result else f"status={result.get('status')}"
            if result.get('is_truncated'):
                flags += ', 截断'
            desc.append(f"E{call['event']}→E{call['response_event']} `{call['tool']} {action}` ({flags})")
        table.append(f"| M{row['model_call']:02} | E{row['event']} / {row['elapsed_s']:.3f}s | {'; '.join(desc) or '无后续工具；E78为最终文本'} | {row['interpretation']} |")
    (out / 'v0-timeline.md').write_text('\n'.join(table) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('event_counts', 'usage_sum', 'read_paths', 'repeated_identical_reads')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    build_audit()
