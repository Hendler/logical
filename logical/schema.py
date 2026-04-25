from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any
from uuid import uuid4


class RecordType(str, Enum):
    CLAIM = "claim"
    ALIAS = "alias"
    CONSTRAINT = "constraint"


class KnowledgeStatus(str, Enum):
    ACCEPTED = "accepted"
    QUARANTINED = "quarantined"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def normalize_term(value: Any) -> str:
    text = str(value or "").strip().lower()
    for article in ("the ", "a ", "an "):
        if text.startswith(article):
            text = text[len(article) :]
            break
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "unknown"


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
    type: RecordType = field(default=RecordType.CLAIM, init=False)

    def __post_init__(self) -> None:
        self.s = normalize_term(self.s)
        self.p = normalize_term(self.p)
        self.o = normalize_term(self.o)
        self.status = KnowledgeStatus(self.status)


@dataclass
class AliasRecord:
    canonical: str
    alias: str
    source_claim_id: str = ""
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
    type: RecordType = field(default=RecordType.CONSTRAINT, init=False)

    def __post_init__(self) -> None:
        self.kind = normalize_term(self.kind)
        self.s = normalize_term(self.s)
        self.p = normalize_term(self.p)
        self.o = normalize_term(self.o) if self.o else ""


@dataclass
class ExtractionResult:
    claims: list[ClaimRecord] = field(default_factory=list)
    aliases: list[AliasRecord] = field(default_factory=list)
    constraints: list[ConstraintRecord] = field(default_factory=list)


@dataclass
class QueryIntent:
    s: str
    p: str
    o: str
    polarity: bool = True

    def __post_init__(self) -> None:
        self.s = normalize_term(self.s)
        self.p = normalize_term(self.p)
        self.o = normalize_term(self.o)


def record_to_dict(record: ClaimRecord | AliasRecord | ConstraintRecord) -> dict[str, Any]:
    data = asdict(record)
    data["type"] = record.type.value
    if "status" in data:
        data["status"] = KnowledgeStatus(data["status"]).value
    return data


def record_from_dict(data: dict[str, Any]) -> ClaimRecord | AliasRecord | ConstraintRecord:
    record_type = RecordType(data["type"])
    payload = {key: value for key, value in data.items() if key != "type"}
    if record_type is RecordType.CLAIM:
        return ClaimRecord(**payload)
    if record_type is RecordType.ALIAS:
        return AliasRecord(**payload)
    if record_type is RecordType.CONSTRAINT:
        return ConstraintRecord(**payload)
    raise ValueError(f"Unsupported record type: {record_type}")
