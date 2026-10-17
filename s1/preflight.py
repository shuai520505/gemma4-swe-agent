"""r03 compatibility fix: exercise the actual LiteLLMClient call shape on CPU."""
from harness_v2.context_budget import RequestGuard,VllmCounter,ContextBudgetExceeded


async def check_model(base_url,model_path,key,*,counter=None):
    from google.adk.models.lite_llm import LiteLLMClient
    count=counter or VllmCounter(base_url,key)
    admissions=[]
    guard=RequestGuard(count,LiteLLMClient().acompletion,core_issue='Reply READY.',emit=admissions.append)
    response=await guard.acompletion(model='openai/'+str(model_path),api_base=base_url,api_key=key,
        messages=[dict(role='user',content='Reply READY.')],tools=None,max_completion_tokens=16,
        extra_body={'chat_template_kwargs':{'enable_thinking':False}})
    assert response.model==str(model_path)
    assert response.usage.prompt_tokens==admissions[-1]['input_tokens']
    assert response.usage.completion_tokens>0
    async def forbidden(**kwargs):raise AssertionError('Oversize request sent')
    over=[]
    guard=RequestGuard(count,forbidden,core_issue='Boundary',emit=over.append)
    try:
        await guard.acompletion(model='openai/'+str(model_path),
            messages=[dict(role='user',content=' token'*30000)],tools=None,max_completion_tokens=16384)
    except ContextBudgetExceeded:pass
    else:raise AssertionError('Boundary not enforced')
    return dict(response=response.model_dump(),admission=admissions,oversize=over)
