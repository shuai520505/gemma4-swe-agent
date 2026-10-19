from dataclasses import dataclass
from s1.config import Config as PriorConfig

@dataclass(frozen=True)
class Config(PriorConfig):
    agent_seconds: int = 500
