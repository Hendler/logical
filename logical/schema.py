from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
from typing import Any
from uuid import uuid4


class RecordType(str, Enum):
    CLAIM = "claim"
    ALIAS = "alias"
    CONSTRAINT = "constraint"
    SOURCE = "source"


class KnowledgeStatus(str, Enum):
    ACCEPTED = "accepted"
    QUARANTINED = "quarantined"


class TermKind(str, Enum):
    OBJECT = "object"
    CATEGORY = "category"
    VALUE = "value"
    UNKNOWN = "unknown"  # Legacy records are never silently assigned a type.


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_time(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError(
            "timestamps must include a timezone, e.g. 2026-09-10T12:00:00Z"
        )
    return result.astimezone(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def normalize_term(value: Any) -> str:
    text = str(value or "").strip().lower()
    for article in ("the ", "a ", "an "):
        if text.startswith(article):
            text = text[len(article) :]
            break
    # Preserve non-ASCII names instead of collapsing them into the same identifier.
    text = re.sub(r"[^\w]+", "_", text, flags=re.UNICODE)
    return re.sub(r"_+", "_", text).strip("_") or "unknown"


@dataclass
class ReferenceBinding:
    mention: str
    resolution: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mention, str) or not self.mention.strip():
            raise ValueError("reference mention must be a nonempty string")
        if self.resolution is not None and (
            type(self.resolution) is not int or self.resolution < 0
        ):
            raise ValueError("resolution must be a nonnegative integer or null")


@dataclass
class AliasDependency:
    alias: str
    canonical: str
    source_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.alias, str)
            or not self.alias.strip()
            or not isinstance(self.canonical, str)
            or not self.canonical.strip()
            or not isinstance(self.source_ids, list)
            or any(not isinstance(sid, str) or not sid for sid in self.source_ids)
        ):
            raise ValueError(
                "identity dependency requires terms and a list of source IDs"
            )


@dataclass
class Evidence:
    source_id: str
    quote: str
    valid_from: str | None = None
    valid_until: str | None = None
    s_ref: ReferenceBinding | None = None
    o_ref: ReferenceBinding | None = None
    identity_dependencies: list[AliasDependency] = field(default_factory=list)

    def __post_init__(self) -> None:
        for name in ("s_ref", "o_ref"):
            value = getattr(self, name)
            if isinstance(value, dict):
                setattr(self, name, ReferenceBinding(**value))
        self.identity_dependencies = [
            AliasDependency(**d) if isinstance(d, dict) else d
            for d in self.identity_dependencies
        ]


@dataclass
class SourceRecord:
    text: str
    reference: str = ""
    file_path: str = ""
    id: str = field(default_factory=lambda: new_id("source"))
    observed_at: str = field(default_factory=utc_now)
    review_after: str | None = None
    created_at: str = field(default_factory=utc_now)
    model: str = ""
    translation_version: int = 2
    supersedes: str = ""
    superseded_by: str = ""
    superseded_at: str | None = None
    resolutions: list[dict[str, str]] = field(default_factory=list)
    unresolved: list[dict[str, str]] = field(default_factory=list)
    validation_issues: list[dict[str, str]] = field(default_factory=list)
    content_hash: str = ""
    type: RecordType = field(default=RecordType.SOURCE, init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("source text must be a nonempty string")
        if type(
            self.translation_version
        ) is not int or self.translation_version not in {1, 2}:
            raise ValueError("unsupported source translation version")
        digest = hashlib.sha256(self.text.encode("utf-8")).hexdigest()
        if self.content_hash and self.content_hash != digest:
            raise ValueError(f"source {self.id} content hash does not match its text")
        self.content_hash = digest
        parse_time(self.observed_at)
        if self.review_after:
            if parse_time(self.review_after) < parse_time(self.observed_at):
                raise ValueError("review_after must be on or after observed_at")
        if self.superseded_at:
            parse_time(self.superseded_at)


@dataclass
class ClaimRecord:
    s: str
    p: str
    o: str
    source_text: str
    id: str = field(default_factory=lambda: new_id("claim"))
    polarity: bool = True
    confidence: float = 1.0
    status: KnowledgeStatus = KnowledgeStatus.ACCEPTED
    created_at: str = field(default_factory=utc_now)
    s_kind: TermKind = TermKind.UNKNOWN
    o_kind: TermKind = TermKind.UNKNOWN
    scope: str = "fact"
    evidence: list[Evidence] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    type: RecordType = field(default=RecordType.CLAIM, init=False)

    def __post_init__(self) -> None:
        self.s = normalize_term(self.s)
        self.p = normalize_term(self.p)
        self.o = normalize_term(self.o)
        self.status = KnowledgeStatus(self.status)
        self.s_kind = TermKind(self.s_kind)
        self.o_kind = TermKind(self.o_kind)
        self.evidence = [
            Evidence(**e) if isinstance(e, dict) else e for e in self.evidence
        ]

    @property
    def key(self) -> tuple[str, str, str, bool, str]:
        return self.s, self.p, self.o, self.polarity, self.scope


@dataclass
class AliasRecord:
    canonical: str
    alias: str
    source_claim_id: str = ""
    source_id: str = ""
    evidence: str = ""
    type: RecordType = field(default=RecordType.ALIAS, init=False)

    def __post_init__(self) -> None:
        self.canonical = normalize_term(self.canonical)
        self.alias = normalize_term(self.alias)


@dataclass
class ConstraintRecord:
    kind: str
    s: str
    p: str
    source_claim_id: str
    o: str = ""
    source_id: str = ""
    evidence: str = ""
    status: KnowledgeStatus = KnowledgeStatus.ACCEPTED
    issues: list[str] = field(default_factory=list)
    s_ref: ReferenceBinding | None = None
    identity_dependencies: list[AliasDependency] = field(default_factory=list)
    type: RecordType = field(default=RecordType.CONSTRAINT, init=False)

    def __post_init__(self) -> None:
        self.status = KnowledgeStatus(self.status)
        evidence = Evidence(
            self.source_id,
            self.evidence,
            s_ref=self.s_ref,
            identity_dependencies=self.identity_dependencies,
        )
        self.s_ref = evidence.s_ref
        self.identity_dependencies = evidence.identity_dependencies
        self.kind = normalize_term(self.kind)
        self.s = normalize_term(self.s)
        self.p = normalize_term(self.p)
        self.o = normalize_term(self.o) if self.o else ""


@dataclass
class ExtractionResult:
    claims: list[ClaimRecord] = field(default_factory=list)
    aliases: list[AliasRecord] = field(default_factory=list)
    constraints: list[ConstraintRecord] = field(default_factory=list)
    resolutions: list[dict[str, str]] = field(default_factory=list)
    unresolved: list[dict[str, str]] = field(default_factory=list)


@dataclass
class QueryIntent:
    s: str
    p: str
    o: str
    polarity: bool = True
    unresolved: str = ""
    s_ref: ReferenceBinding | None = None
    o_ref: ReferenceBinding | None = None

    def __post_init__(self) -> None:
        self.s = normalize_term(self.s)
        self.p = normalize_term(self.p)
        self.o = normalize_term(self.o)
        for name in ("s_ref", "o_ref"):
            value = getattr(self, name)
            if isinstance(value, dict):
                setattr(self, name, ReferenceBinding(**value))


Record = ClaimRecord | AliasRecord | ConstraintRecord | SourceRecord


def record_to_dict(record: Record) -> dict[str, Any]:
    return asdict(record)


def record_from_dict(data: dict[str, Any]) -> Record:
    record_type = RecordType(data["type"])
    payload = {key: value for key, value in data.items() if key != "type"}
    if record_type is RecordType.CLAIM:
        payload.setdefault(
            "id",
            "claim-legacy-"
            + hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
        )
        payload.setdefault("created_at", "1970-01-01T00:00:00+00:00")
    if record_type is RecordType.SOURCE:
        payload.setdefault("translation_version", 1)
    constructors = {
        RecordType.CLAIM: ClaimRecord,
        RecordType.ALIAS: AliasRecord,
        RecordType.CONSTRAINT: ConstraintRecord,
        RecordType.SOURCE: SourceRecord,
    }
    return constructors[record_type](**payload)
