"""Passive live observation. Claims never become observed contract facts."""
import hashlib
import json
import re


class ContractObserver:
    def __init__(self, journal):
        self.journal = journal
        self.seen = set()

    def observe(self, event):
        if getattr(event, 'partial', False):
            return
        key = getattr(event, 'id', None) or id(event)
        if key in self.seen:
            return
        self.seen.add(key)
        for part in getattr(getattr(event, 'content', None), 'parts', None) or []:
            response = getattr(part, 'function_response', None)
            if response is not None:
                raw = json.dumps(response.response, sort_keys=True, default=str)
                self.journal.append(dict(kind='tool_observation', tool=response.name, event_id=str(key),
                    summary=raw[:400], sha256=hashlib.sha256(raw.encode()).hexdigest(),
                    provenance='actual_ADK_tool_response_not_a_semantic_verdict'), 'contract_observations.jsonl')
            text = getattr(part, 'text', None) or ''
            if getattr(part, 'thought', False):
                continue
            for match in re.finditer(r'<cure>(.*?)</cure>', text, re.S):
                payload = match.group(1)
                valid = False
                if len(payload) <= 6000:
                    try:
                        claim = json.loads(payload)
                        valid = isinstance(claim, dict) and claim.get('action') in {'locate', 'inspect', 'probe', 'edit', 'verify', 'submit'}
                    except ValueError:
                        pass
                self.journal.append(dict(kind='model_contract_claim', event_id=str(key), valid=valid,
                    summary=payload[:6000], provenance='model_report_only_unverified',
                    affects_controller_decisions=False), 'contract_observations.jsonl')
