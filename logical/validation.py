from __future__ import annotations

from dataclasses import dataclass

from logical.schema import ClaimRecord, ConstraintRecord


SUPPORTED_CONSTRAINTS = {"functional_for_subject"}


@dataclass(frozen=True)
class ValidationIssue:
    kind: str
    record_id: str
    message: str


def validate_claim(claim: ClaimRecord) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if "unknown" in {claim.s, claim.p, claim.o}:
        issues.append(
            ValidationIssue(
                kind="missing_term",
                record_id=claim.id,
                message=f"claim {claim.id} has an unknown subject, predicate, or object",
            )
        )
    if not claim.source_text.strip():
        issues.append(
            ValidationIssue(
                kind="missing_source",
                record_id=claim.id,
                message=f"claim {claim.id} is missing source text",
            )
        )
    if not 0 <= claim.confidence <= 1:
        issues.append(
            ValidationIssue(
                kind="invalid_confidence",
                record_id=claim.id,
                message=f"claim {claim.id} confidence must be between 0 and 1",
            )
        )
    return issues


def validate_constraint(constraint: ConstraintRecord) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if constraint.kind not in SUPPORTED_CONSTRAINTS:
        issues.append(
            ValidationIssue(
                kind="unsupported_constraint",
                record_id=constraint.source_claim_id,
                message=f"unsupported constraint kind {constraint.kind}",
            )
        )
    if "unknown" in {constraint.s, constraint.p}:
        issues.append(
            ValidationIssue(
                kind="missing_constraint_term",
                record_id=constraint.source_claim_id,
                message="constraint is missing a subject or predicate",
            )
        )
    return issues
