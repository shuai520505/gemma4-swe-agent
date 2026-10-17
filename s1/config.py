"""Explicit registered budgets; shared baseline defaults are not S0 score replicas."""
from dataclasses import asdict, dataclass
from . import VERSION, MODEL, TOOLS


@dataclass(frozen=True)
class Config:
    version: str = VERSION
    agent_seconds: int = 300
    tool_budget: int = 60
    output_tokens: int = 16384
    thinking_budget: int = 4096
    include_thoughts: bool | None = None
    seed: int | None = 17
    command_seconds: int = 120

    def __post_init__(self):
        if self.version != VERSION:
            raise ValueError('Executor version mismatch')
        for name, low, high in [('agent_seconds',1,3600),('tool_budget',1,1000),
                ('output_tokens',1,32768),('thinking_budget',0,32768),('command_seconds',1,300)]:
            v=getattr(self,name)
            if type(v) is not int or not low <= v <= high:
                raise ValueError(name)
        if self.thinking_budget >= self.output_tokens:
            raise ValueError('Thinking must leave output for actions')
        if self.include_thoughts is not None and type(self.include_thoughts) is not bool:
            raise ValueError('include_thoughts')
        if self.seed is not None and (type(self.seed) is not int or not 0 <= self.seed < 2**31):
            raise ValueError('seed')

    @property
    def stage_caps(self):
        return dict(prepare_agent=180,agent=self.agent_seconds+30,save_patch=60,
                    prepare_verifier=180,apply_patch=60,verification=300,persist=60,cleanup=120)

    @property
    def outer_seconds(self):
        return sum(self.stage_caps.values())+60

    def snapshot(self):
        return asdict(self)


def validate_compiled(agent, config):
    cfg=agent.generate_content_config
    tools=[getattr(t,'__name__',getattr(t,'name',None)) for t in agent.tools]
    if set(tools)!=set(TOOLS) or len(tools)!=6 or agent.sub_agents:
        raise ValueError('Require one Agent and six official tools')
    tc=cfg.thinking_config
    if (cfg.max_output_tokens!=config.output_tokens or tc.thinking_budget!=config.thinking_budget or
            tc.include_thoughts!=config.include_thoughts or cfg.seed!=config.seed):
        raise ValueError('Compiled generation differs from registration')
    if MODEL not in agent.model.model:
        raise ValueError('Wrong model')
    return cfg
