from __future__ import annotations

from dataclasses import dataclass

from logical.schema import ClaimRecord, ConstraintRecord, KnowledgeStatus


@dataclass(frozen=True)
class Conflict:
    kind: str
    candidate_claim_id: str
    existing_claim_id: str
    message: str


def find_conflicts(
    candidate: ClaimRecord,
    existing_claims: list[ClaimRecord],
    constraints: list[ConstraintRecord],
) -> list[Conflict]:
    conflicts: list[Conflict] = []
    for existing in existing_claims:
        if existing.status is not KnowledgeStatus.ACCEPTED:
            continue
        if _is_direct_contradiction(candidate, existing):
            conflicts.append(
                Conflict(
                    kind="direct_contradiction",
                    candidate_claim_id=candidate.id,
                    existing_claim_id=existing.id,
                    message=(
                        f"{candidate.s} {candidate.p} {candidate.o} contradicts "
                        f"accepted claim {existing.id}"
                    ),
                )
            )
        if _violates_functional_constraint(candidate, existing, constraints):
            conflicts.append(
                Conflict(
                    kind="functional_for_subject",
                    candidate_claim_id=candidate.id,
                    existing_claim_id=existing.id,
                    message=(
                        f"{candidate.s} {candidate.p} can only have one value; "
                        f"{existing.o} is already accepted"
                    ),
                )
            )
    return conflicts


def _is_direct_contradiction(candidate: ClaimRecord, existing: ClaimRecord) -> bool:
    return (
        candidate.s == existing.s
        and candidate.p == existing.p
        and candidate.o == existing.o
        and candidate.polarity != existing.polarity
    )


def _violates_functional_constraint(
    candidate: ClaimRecord,
    existing: ClaimRecord,
    constraints: list[ConstraintRecord],
) -> bool:
    if not candidate.polarity or not existing.polarity:
        return False
    if candidate.s != existing.s or candidate.p != existing.p or candidate.o == existing.o:
        return False
    return any(
        constraint.kind == "functional_for_subject"
        and constraint.s == candidate.s
        and constraint.p == candidate.p
        for constraint in constraints
    )
