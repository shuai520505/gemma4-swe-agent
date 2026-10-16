"""Stage allowances are wall-clock ceilings, not measured task performance."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Budgets:
    stage_caps: dict = field(default_factory=lambda: dict(
        prepare_agent=180, agent=510, save_patch=60, prepare_verifier=180,
        apply_patch=60, verification=300, persist=60, cleanup=120))
    safety_seconds: int = 60
    agent_seconds: int = 480
    command_seconds: int = 120
    max_tool_calls: int = 60

    @property
    def outer_seconds(self):
        return sum(self.stage_caps.values()) + self.safety_seconds

    def as_dict(self):
        return dict(stage_caps=self.stage_caps, safety_seconds=self.safety_seconds,
            outer_seconds=self.outer_seconds, agent_seconds=self.agent_seconds,
            command_seconds=self.command_seconds, max_tool_calls=self.max_tool_calls)
