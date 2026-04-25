from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from logical.schema import (
    AliasRecord,
    ClaimRecord,
    ConstraintRecord,
    KnowledgeStatus,
    record_from_dict,
    record_to_dict,
)


class KnowledgeStore:
    def __init__(self, root: str | Path = ".logical") -> None:
        self.root = Path(root)
        self.knowledge_path = self.root / "knowledge.jsonl"
        self.world_path = self.root / "world.pl"

    def ensure_root(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def append_records(
        self, records: Iterable[ClaimRecord | AliasRecord | ConstraintRecord]
    ) -> None:
        records = list(records)
        if not records:
            return
        self.ensure_root()
        with self.knowledge_path.open("a", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record_to_dict(record), sort_keys=True))
                handle.write("\n")

    def load_records(self) -> list[ClaimRecord | AliasRecord | ConstraintRecord]:
        if not self.knowledge_path.exists():
            return []
        records: list[ClaimRecord | AliasRecord | ConstraintRecord] = []
        with self.knowledge_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append(record_from_dict(json.loads(line)))
        return records

    def load_claims(self, status: KnowledgeStatus | None = None) -> list[ClaimRecord]:
        claims = [
            record for record in self.load_records() if isinstance(record, ClaimRecord)
        ]
        if status is None:
            return claims
        return [claim for claim in claims if claim.status is status]

    def load_aliases(self) -> list[AliasRecord]:
        return [
            record for record in self.load_records() if isinstance(record, AliasRecord)
        ]

    def load_constraints(self) -> list[ConstraintRecord]:
        return [
            record for record in self.load_records() if isinstance(record, ConstraintRecord)
        ]

    def write_world(self, prolog_text: str) -> Path:
        self.ensure_root()
        self.world_path.write_text(prolog_text, encoding="utf-8")
        return self.world_path

    def rewrite_records(
        self, records: Iterable[ClaimRecord | AliasRecord | ConstraintRecord]
    ) -> None:
        self.ensure_root()
        with self.knowledge_path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record_to_dict(record), sort_keys=True))
                handle.write("\n")
