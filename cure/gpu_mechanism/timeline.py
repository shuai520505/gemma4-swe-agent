"""Export native calls/results for human audit; no causal labels inferred."""
import argparse
import json
from pathlib import Path
from cure.build import write_new


def export(directory):
    directory=Path(directory)
    audits=sorted(directory.glob('results/*/runs/*/mechanism_audit.json'))
    lines=['# 原生工具逐事件记录','',
        '仅整理实际ADK事件，不依据CURE decision_changed判断有效性。完整参数/结果、模型文字和usage见各运行原始JSON。','']
    for p in audits:
        run=p.parent
        data=json.loads(p.read_text())
        lines+=['## '+run.name,'',f"基础设施门：{data['infrastructure_passed']}；HTTP请求：{data['model_requests']}；工具调用：{data['tool_calls']}。",'']
        for e in data['tool_sequence']:
            content=e.get('args',e.get('response',{}))
            text=json.dumps(content,ensure_ascii=False)
            if len(text)>1400: text=text[:1400]+' … [完整内容见JSON]'
            lines += [f"{e['index']}. {e['kind']} / {e.get('name','')} / event `{e['event_id']}`",'',
                '```text',text,'```','']
    write_new(directory/'TOOL_TIMELINE.md',('\n'.join(lines).rstrip()+'\n').encode())
    print(dict(runs=len(audits),output=str(directory/'TOOL_TIMELINE.md')))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory');export(p.parse_args().directory)
