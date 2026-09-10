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


def source_state(
    source: SourceRecord, at: datetime, *, inspect_file: bool = True
) -> tuple[str, str]:
    if parse_time(source.observed_at) > at:
        return "future", "source has not been observed yet"
    if source.superseded_at and parse_time(source.superseded_at) <= at:
        return "stale", f"source superseded by {source.superseded_by}"
    if source.translation_version < 2:
        return (
            "stale",
            "source predates identity provenance; retranslate with logical update",
        )
    if inspect_file and source.file_path:
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
    evidence: Evidence,
    sources: dict[str, SourceRecord],
    at: datetime,
    *,
    source_states: dict[str, tuple[str, str]] | None = None,
    identity_sources: dict[tuple[str, str], set[str]] | None = None,
) -> tuple[str, str]:
    source = sources.get(evidence.source_id)
    if source is None:
        return "stale", f"missing source {evidence.source_id}"

    def state(source_id: str) -> tuple[str, str]:
        if source_id not in sources:
            return "stale", f"missing identity source {source_id}"
        return (
            source_states[source_id]
            if source_states is not None
            else source_state(sources[source_id], at)
        )

    states = [state(source.id)]
    if evidence.valid_from and parse_time(evidence.valid_from) > at:
        states.append(("future", f"valid from {evidence.valid_from}"))
    if evidence.valid_until and parse_time(evidence.valid_until) <= at:
        states.append(("stale", f"validity ended {evidence.valid_until}"))
    for dependency in evidence.identity_dependencies:
        supporting_ids = (
            identity_sources.get((dependency.alias, dependency.canonical), set())
            if identity_sources is not None
            else set(dependency.source_ids)
        )
        alternatives = [state(sid) for sid in supporting_ids]
        eligible = next(
            (
                status
                for status in ("fresh", "unknown", "future", "stale")
                if any(s == status for s, _ in alternatives)
            ),
            "stale",
        )
        states.append(
            (
                eligible,
                f"identity {dependency.alias} = {dependency.canonical}: "
                + (
                    "; ".join(
                        sorted({reason for s, reason in alternatives if s == eligible})
                    )
                    or "no supporting identity evidence"
                ),
            )
        )
    # Every premise is required, while separate evidence entries are alternatives.
    for status in ("stale", "future", "unknown", "fresh"):
        if any(s == status for s, _ in states):
            return status, "; ".join(
                sorted({reason for s, reason in states if s == status})
            )
    raise AssertionError("unreachable")


def claim_state(
    claim: ClaimRecord,
    sources: dict[str, SourceRecord],
    at: datetime,
    *,
    source_states: dict[str, tuple[str, str]] | None = None,
    identity_sources: dict[tuple[str, str], set[str]] | None = None,
) -> tuple[str, list[str]]:
    if not claim.evidence:
        return "unknown", ["legacy claim has no source review policy"]
    states = [
        evidence_state(
            e,
            sources,
            at,
            source_states=source_states,
            identity_sources=identity_sources,
        )
        for e in claim.evidence
    ]
    for state in ("fresh", "unknown", "future", "stale"):
        if any(s == state for s, _ in states):
            return state, sorted({reason for s, reason in states if s == state})
    raise AssertionError("unreachable")


def source_index(records: list[Record]) -> dict[str, SourceRecord]:
    return {r.id: r for r in records if isinstance(r, SourceRecord)}


def evaluation_time(at: str | None = None) -> datetime:
    return parse_time(at or utc_now())
