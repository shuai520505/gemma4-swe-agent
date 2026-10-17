"""Transparent research heuristic. Scores are NOT repair probabilities."""
from dataclasses import asdict, dataclass
import math
from .contract_state import ContractBook

ACTIONS = ('locate', 'inspect', 'probe', 'edit', 'verify', 'submit')
COSTS = {'locate': 4., 'inspect': 4., 'probe': 6., 'edit': 5., 'verify': 8., 'submit': 2.}


@dataclass(frozen=True)
class Budget:
    seconds: float
    tools: int
    submit_reserve: float = 2.

    def __post_init__(self):
        if isinstance(self.seconds, bool) or not math.isfinite(self.seconds) or self.seconds < 0:
            raise ValueError('Invalid remaining time')
        if type(self.tools) is not int or self.tools < 0 or self.submit_reserve < 0 or not math.isfinite(self.submit_reserve):
            raise ValueError('Invalid tool/reserve budget')


@dataclass(frozen=True)
class Option:
    action: str
    contract_id: str | None
    score: float
    feasible: bool
    reason: str
    estimated_seconds: float
    estimated_tools: int = 1


@dataclass(frozen=True)
class Decision:
    action: str
    contract_id: str | None
    feasible: bool
    reason: str
    options: tuple[Option, ...]

    def snapshot(self):
        return asdict(self)


def select(book: ContractBook, budget: Budget) -> Decision:
    options = []
    all_passed = all(c.verification_status == 'passed' and c.edited for c in book.contracts)
    for c in book.contracts:
        gates = {
            'locate': (not c.located, 4 * c.impact * c.uncertainty, 'No location supported by a tool observation'),
            'inspect': (c.located and not c.inspected, 5 * c.impact * c.uncertainty, 'Inspect contract/caller; evidence absent or contradicted'),
            'probe': (c.inspected and not c.ready_to_edit and bool(c.proposed_probe), 4 * c.impact * c.uncertainty, 'Resolve remaining uncertainty using a directed probe'),
            'edit': (c.inspected and c.ready_to_edit and not c.edited, 6 * c.impact * (1 - c.uncertainty), 'Evidence supports a concrete repair; ready-to-edit annotation is explicit'),
            'verify': (c.edited and c.verification_status != 'passed', 7 * c.impact, 'Changed behavior has no successful targeted verification'),
        }
        for action, (eligible, benefit, reason) in gates.items():
            cost = COSTS[action]
            affordable = budget.tools >= 2 and budget.seconds >= cost + budget.submit_reserve
            options.append(Option(action, c.id, round(benefit / cost, 6), eligible and affordable,
                reason if eligible and affordable else ('Not eligible in current state' if not eligible else 'Preserve submission budget'), cost))
    near_end = budget.seconds < 12 or budget.tools <= 2
    options.append(Option('submit', None, 100. if all_passed or near_end else .01,
        budget.tools >= 1 and budget.seconds >= COSTS['submit'],
        'Verified patch' if all_passed and book.patch_ready else ('Best effort: preserve patch; unresolved contracts remain' if book.patch_ready else 'No patch: record incompleteness; never invent a repair'), COSTS['submit']))
    feasible = [o for o in options if o.feasible]
    if not feasible:
        return Decision('submit', None, False, 'Budget exhausted; persist evidence without invoking another tool', tuple(options))
    winner = max(feasible, key=lambda o: o.score)
    return Decision(winner.action, winner.contract_id, True, winner.reason, tuple(options))


class Checklist:
    """Fixed sequence baseline; results do not reorder its next action."""
    def __init__(self):
        self.index = 0

    def choose(self, book, budget):
        action = ACTIONS[min(self.index, len(ACTIONS) - 1)]
        feasible = budget.tools >= 1 and budget.seconds >= COSTS[action]
        return Decision(action, book.contracts[0].id, feasible, 'Fixed checklist order', ())

    def advance(self):
        self.index += 1
