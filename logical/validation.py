from __future__ import annotations

from dataclasses import dataclass
import math

from logical.resolution import PRONOUNS
from logical.schema import ClaimRecord, ConstraintRecord, TermKind, parse_time

SUPPORTED_CONSTRAINTS = {"functional_for_subject"}


@dataclass(frozen=True)
class ValidationIssue:
    kind: str
    record_id: str
    message: str


def validate_claim(claim: ClaimRecord) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    def issue(kind: str, message: str) -> None:
        issues.append(ValidationIssue(kind, claim.id, message))

    if "unknown" in {claim.s, claim.p, claim.o}:
        issue(
            "missing_term",
            f"claim {claim.id} has an unknown subject, predicate, or object",
        )
    if not claim.source_text.strip() and not claim.evidence:
        issue("missing_source", f"claim {claim.id} is missing source text")
    if (
        type(claim.confidence) not in (int, float)
        or not math.isfinite(claim.confidence)
        or not 0 <= claim.confidence <= 1
    ):
        issue(
            "invalid_confidence", f"claim {claim.id} confidence must be between 0 and 1"
        )
    if type(claim.polarity) is not bool:
        issue("invalid_polarity", "polarity must be a boolean")
    if claim.scope not in {"fact", "all"}:
        issue(
            "unsupported_scope",
            "only ground facts and explicit universal statements are supported",
        )
    if claim.scope == "all" and (
        claim.s_kind is not TermKind.CATEGORY
        or claim.p in {"instance_of", "subclass_of"}
    ):
        issue(
            "invalid_universal",
            "universal properties require a category subject; use subclass_of for category inclusion",
        )
    expected = {
        "instance_of": (TermKind.OBJECT, TermKind.CATEGORY),
        "subclass_of": (TermKind.CATEGORY, TermKind.CATEGORY),
    }
    if claim.p in expected and (claim.s_kind, claim.o_kind) != expected[claim.p]:
        issue(
            "category_error",
            f"{claim.p} requires {expected[claim.p][0].value} -> category",
        )
    if claim.s_kind is TermKind.VALUE:
        issue("category_error", "a literal value cannot be the subject of a claim")
    if claim.s in PRONOUNS or claim.o in PRONOUNS:
        issue(
            "unresolved_reference",
            "resolve pronouns in their source context before asserting a claim",
        )
    for evidence in claim.evidence:
        try:
            start = parse_time(evidence.valid_from) if evidence.valid_from else None
            end = parse_time(evidence.valid_until) if evidence.valid_until else None
            if start and end and start >= end:
                raise ValueError("valid_until must be after valid_from")
        except ValueError as exc:
            issue("invalid_validity", str(exc))
    return issues


def validate_constraint(
    constraint: ConstraintRecord, kinds: dict[str, TermKind] | None = None
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if kinds and kinds.get(constraint.s) in {TermKind.CATEGORY, TermKind.VALUE}:
        issues.append(
            ValidationIssue(
                "category_error",
                constraint.source_id or constraint.source_claim_id,
                "functional_for_subject needs an object, not a category or value",
            )
        )
    if constraint.kind not in SUPPORTED_CONSTRAINTS:
        issues.append(
            ValidationIssue(
                "unsupported_constraint",
                constraint.source_claim_id,
                f"unsupported constraint kind {constraint.kind}",
            )
        )
    if "unknown" in {constraint.s, constraint.p}:
        issues.append(
            ValidationIssue(
                "missing_constraint_term",
                constraint.source_claim_id,
                "constraint is missing a subject or predicate",
            )
        )
    return issues
