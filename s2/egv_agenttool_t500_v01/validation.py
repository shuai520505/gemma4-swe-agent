"""Research admission for the two allowed declarative architectures."""
from s1 import MODEL, TOOLS
from s1.config import validate_compiled


def validate_candidate(agent, config):
    if agent.name=='v0_coding_agent':return validate_compiled(agent,config)
    assert agent.name=='main_coding_agent' and not agent.sub_agents
    delegation=[t for t in agent.tools if getattr(t,'name',None)=='egv_verifier']
    assert len(delegation)==1 and len(agent.tools)==7
    child=delegation[0].agent
    assert not delegation[0].skip_summarization and delegation[0].include_plugins
    assert not child.sub_agents
    name=lambda t:getattr(t,'__name__',getattr(t,'name',None))
    assert {name(t) for t in child.tools}=={'get_status','read_file','run_command'}
    assert len(child.tools)==3
    assert {name(t) for t in agent.tools}==set(TOOLS)|{'egv_verifier'}
    assert agent.model.model==child.model.model and MODEL in agent.model.model
    for a in (agent,child):
        g=a.generate_content_config
        assert g.max_output_tokens==config.output_tokens and g.seed==config.seed
        assert g.thinking_config.thinking_budget==config.thinking_budget
        assert g.thinking_config.include_thoughts==config.include_thoughts
        assert g.temperature is None and g.top_p is None and g.top_k is None
    return agent.generate_content_config
