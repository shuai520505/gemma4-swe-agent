"""Bounded contracts, with explicit provenance rather than a duplicate transcript."""
from dataclasses import asdict, dataclass, field
import hashlib
import math


KINDS = {'observation', 'model_inference', 'unconfirmed_hypothesis'}
STATUSES = {'unverified', 'failed', 'passed', 'blocked'}


def bounded(value, limit):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError(f'Expected text of at most {limit} characters')
    return value


def unit(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('Ordinal uncertainty/impact must be finite and between zero and one')
    return float(value)


@dataclass(frozen=True)
class Evidence:
    kind: str
    summary: str
    reference: str
    digest: str = ''
    role: str = 'read'
    exit_code: int | None = None

    def __post_init__(self):
        if self.kind not in KINDS or self.role not in {'read', 'probe', 'edit', 'verification'}:
            raise ValueError('Unknown evidence kind/role')
        bounded(self.summary, 400); bounded(self.reference, 200)
        if self.kind == 'observation' and (not self.reference or len(self.digest) != 64):
            raise ValueError('Observed evidence needs a tool-result reference and SHA256')

    @classmethod
    def tool_result(cls, raw, reference, *, role='read', exit_code=None):
        # This proves the bytes were observed, NOT that a semantic interpretation is true.
        if not isinstance(raw, str):
            raise ValueError('Tool result must be text')
        return cls('observation', raw[:400], reference, hashlib.sha256(raw.encode()).hexdigest(), role, exit_code)


@dataclass
class ContractState:
    id: str
    requirement: str
    evidence: list[Evidence] = field(default_factory=list)
    uncertainty: float = .8
    impact: float = .8
    verification_status: str = 'unverified'
    proposed_probe: str = ''
    located: bool = False
    inspected: bool = False
    ready_to_edit: bool = False
    edited: bool = False
    contradiction_count: int = 0
    dropped_evidence: int = 0
    max_evidence: int = 8

    def __post_init__(self):
        bounded(self.id, 64); bounded(self.requirement, 600); bounded(self.proposed_probe, 300)
        self.uncertainty = unit(self.uncertainty); self.impact = unit(self.impact)
        if self.verification_status not in STATUSES or self.evidence or self.max_evidence != 8:
            raise ValueError('Create an empty state; populate evidence through update()')

    def update(self, evidence, *, uncertainty=None, contradiction=False, **changes):
        """Semantic changes are caller annotations, not automatic truth extraction.

        Research fixtures supply explicit decoders; live model claims stay claims.
        Inferences cannot promote a contract to located/verified/ready-to-edit.
        """
        allowed = {'located', 'inspected', 'ready_to_edit', 'edited', 'verification_status', 'proposed_probe'}
        if set(changes) - allowed:
            raise ValueError('Unsupported state field')
        if not isinstance(evidence, Evidence):
            raise ValueError('Evidence required')
        new_u = self.uncertainty if uncertainty is None else unit(uncertainty)
        for key in ('located', 'inspected', 'ready_to_edit', 'edited'):
            if key in changes and type(changes[key]) is not bool:
                raise ValueError('State flags must be booleans')
        status = changes.get('verification_status', self.verification_status)
        if status not in STATUSES:
            raise ValueError('Invalid verification status')
        if 'proposed_probe' in changes:
            bounded(changes['proposed_probe'], 300)
        promoting = new_u < self.uncertainty or any(changes.get(k) is True for k in ('located', 'inspected', 'ready_to_edit', 'edited'))
        if evidence.kind != 'observation' and (promoting or status in {'passed', 'failed'} or contradiction):
            raise ValueError('Claims cannot establish executable facts or overturn observed evidence')
        if status == 'passed' and 'verification_status' in changes:
            if evidence.role != 'verification' or evidence.exit_code != 0:
                raise ValueError('Passed requires a completed zero-exit verification observation')
        self.evidence.append(evidence)
        if len(self.evidence) > self.max_evidence:
            del self.evidence[0]; self.dropped_evidence += 1
        self.uncertainty = new_u
        for key, value in changes.items():
            setattr(self, key, value)
        if contradiction:
            self.contradiction_count += 1
            self.uncertainty = max(.9, self.uncertainty)
            self.inspected = False; self.ready_to_edit = False
            self.verification_status = 'unverified'

    def snapshot(self):
        return asdict(self)


@dataclass
class ContractBook:
    contracts: list[ContractState]
    patch_ready: bool = False

    def __post_init__(self):
        if not 1 <= len(self.contracts) <= 6 or len({c.id for c in self.contracts}) != len(self.contracts):
            raise ValueError('Use one to six distinct contracts')

    def snapshot(self):
        return {'contracts': [c.snapshot() for c in self.contracts], 'patch_ready': self.patch_ready}
