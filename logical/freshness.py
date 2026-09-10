"""Freshness is a property of evidence, distinct from logical acceptance."""

from __future__ import annotations

from datetime import datetime
import hashlib
from pathlib import Path

from logical.schema import (
    ClaimRecord,
    Evidence,
    Record,
    SourceRecord,
    parse_time,
    utc_now,
)


def source_state(source: SourceRecord, at: datetime) -> tuple[str, str]:
    if parse_time(source.observed_at) > at:
        return "future", "source has not been observed yet"
    if source.superseded_at and parse_time(source.superseded_at) <= at:
        return "stale", f"source superseded by {source.superseded_by}"
    if source.file_path:
        try:
            text = Path(source.file_path).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return "stale", "source file is unavailable"
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != source.content_hash:
            return (
                "stale",
                "source file contents changed; retranslate with logical update",
            )
    if not source.review_after:
        return "unknown", "source has no review deadline"
    if parse_time(source.review_after) <= at:
        return "stale", f"source review due {source.review_after}"
    return "fresh", f"source review due {source.review_after}"


def evidence_state(
    evidence: Evidence, sources: dict[str, SourceRecord], at: datetime
) -> tuple[str, str]:
    source = sources.get(evidence.source_id)
    if source is None:
        return "stale", f"missing source {evidence.source_id}"
    if evidence.valid_from and parse_time(evidence.valid_from) > at:
        return "future", f"valid from {evidence.valid_from}"
    if evidence.valid_until and parse_time(evidence.valid_until) <= at:
        return "stale", f"validity ended {evidence.valid_until}"
    return source_state(source, at)


def claim_state(
    claim: ClaimRecord, sources: dict[str, SourceRecord], at: datetime
) -> tuple[str, list[str]]:
    if not claim.evidence:
        return "unknown", ["legacy claim has no source review policy"]
    states = [evidence_state(e, sources, at) for e in claim.evidence]
    for state in ("fresh", "unknown", "future", "stale"):
        if any(s == state for s, _ in states):
            return state, sorted({reason for s, reason in states if s == state})
    raise AssertionError("unreachable")


def source_index(records: list[Record]) -> dict[str, SourceRecord]:
    return {r.id: r for r in records if isinstance(r, SourceRecord)}


def evaluation_time(at: str | None = None) -> datetime:
    return parse_time(at or utc_now())
