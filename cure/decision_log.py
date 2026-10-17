"""One bounded snapshot per action, with same-budget counterfactual comparisons."""
from dataclasses import asdict
import json
from pathlib import Path
from harness_v2.evidence import Journal
from .action_selector import select


class DecisionLog:
    def __init__(self, directory):
        self.journal = Journal(directory)
        self.sequence = 0

    def begin(self, book, budget, decision):
        self.sequence += 1
        row = {'kind': 'decision', 'sequence': self.sequence, 'known': book.snapshot(),
               'budget': asdict(budget), 'selection': decision.snapshot(), 'score_semantics': 'ordinal heuristic per estimated second; not probability'}
        self.journal.append(row, 'decisions.jsonl')
        return self.sequence

    def finish(self, sequence, result, before_action, after_decision, elapsed, tools):
        self.journal.append({'kind': 'action_result', 'sequence': sequence, 'result': result,
            'actual_seconds': elapsed, 'actual_tools': tools,
            'same_budget_next_without_observation': before_action,
            'next_with_observation': after_decision.snapshot(),
            'observation_changed_next': before_action != after_decision.action}, 'decisions.jsonl')
