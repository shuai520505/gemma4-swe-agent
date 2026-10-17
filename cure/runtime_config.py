"""Registered research-only limits; both candidates share identical values."""
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from . import MODEL, VERSION


@dataclass(frozen=True)
class ResearchConfig:
    version: str = VERSION
    agent_seconds: int = 300
    tool_budget: int = 60
    output_tokens: int = 8192
    thinking_budget: int = 4096
    include_thoughts: bool = True
    seed: int = 17
    command_seconds: int = 120

    def __post_init__(self):
        if self.version != VERSION:
            raise ValueError('Research executor version mismatch')
        for name, lower, upper in [('agent_seconds', 1, 3600), ('tool_budget', 1, 1000),
                                   ('output_tokens', 1, 32768), ('thinking_budget', 0, 32768),
                                   ('seed', 0, 2**31 - 1), ('command_seconds', 1, 300)]:
            value = getattr(self, name)
            if type(value) is not int or not lower <= value <= upper:
                raise ValueError(f'Invalid registered {name}')
        if type(self.include_thoughts) is not bool or self.thinking_budget >= self.output_tokens:
            raise ValueError('Thinking must leave some output allowance for actions')

    @property
    def stage_caps(self):
        return dict(prepare_agent=180, agent=self.agent_seconds + 30, save_patch=60,
                    prepare_verifier=180, apply_patch=60, verification=300, persist=60, cleanup=120)

    @property
    def outer_seconds(self):
        return sum(self.stage_caps.values()) + 60

    def snapshot(self):
        return asdict(self)

    @classmethod
    def load(cls, path):
        return cls(**json.loads(Path(path).read_text(encoding='utf-8')))


def validate_compiled(agent, config):
    from . import TOOLS
    cfg = agent.generate_content_config
    names = [getattr(t, '__name__', getattr(t, 'name', None)) for t in agent.tools]
    if set(names) != set(TOOLS) or len(names) != 6 or agent.sub_agents:
        raise ValueError('Require exactly six native tools and one Agent')
    tc = cfg.thinking_config
    if (cfg.max_output_tokens != config.output_tokens or tc.thinking_budget != config.thinking_budget
            or tc.include_thoughts != config.include_thoughts or cfg.seed != config.seed):
        raise ValueError('Candidate generation settings differ from registered research configuration')
    if agent.model.model.removeprefix('openai/').split('/')[-1] != MODEL:
        # Actual local model paths end in /2, but compiler registry models may use them.
        if MODEL not in agent.model.model:
            raise ValueError('Require the specified 31B model')
    return cfg
