"""Prospective metadata-only ordering; no execution, Issue/test or repair input."""
import hashlib

PREFIX='U-RE-V01-ACTION-FIRST-01:17:'
MAX_CPU_CHECKS=8
SELECTED_TASKS=2
ALWAYS_EXCLUDED={'fastapi_14262','fastapi_14492','fastapi_15800','rich_3471',
                 'rich_3676','fastapi_14458','requests_7433'}


def rank(metadata, inherited_exclusions, refreshed_exclusions):
    if not set(inherited_exclusions) <= set(refreshed_exclusions):
        raise ValueError('Cannot relax historical exclusions')
    excluded=set(refreshed_exclusions)|ALWAYS_EXCLUDED
    allowed={'instance_id','repo','base_commit','issue_sha256'}
    if any(set(row)-allowed for row in metadata):
        raise ValueError('Ranking consumes metadata only, never outcome/test/repair features')
    ids=[row['instance_id'] for row in metadata]
    if len(ids)!=len(set(ids)):raise ValueError('Ambiguous task identities')
    return sorted((row for row in metadata if row['instance_id'] not in excluded),
        key=lambda row:(hashlib.sha256((PREFIX+row['instance_id']).encode()).hexdigest(),row['instance_id']))
