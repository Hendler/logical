from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Iterable, Iterator

from logical.schema import (
    AliasRecord,
    ClaimRecord,
    ConstraintRecord,
    KnowledgeStatus,
    Record,
    SourceRecord,
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

    @contextmanager
    def transaction(self) -> Iterator[list[Record]]:
        """Serialize read/modify/write, committing once or leaving the old file intact."""
        self.ensure_root()
        with (self.root / ".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                records = self.load_records()
                yield records
                self._atomic_write(self.knowledge_path, self._serialize(records))
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def revision(self) -> str:
        data = self.knowledge_path.read_bytes() if self.knowledge_path.exists() else b""
        return hashlib.sha256(data).hexdigest()

    def append_records(self, records: Iterable[Record]) -> None:
        additions = list(records)
        if additions:
            with self.transaction() as current:
                current.extend(additions)

    def load_records(self) -> list[Record]:
        if not self.knowledge_path.exists():
            return []
        records: list[Record] = []
        with self.knowledge_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if line.strip():
                    try:
                        records.append(record_from_dict(json.loads(line)))
                    except (ValueError, TypeError, KeyError) as exc:
                        raise ValueError(
                            f"Invalid knowledge record on line {line_number}: {exc}"
                        ) from exc
        return records

    def load_claims(self, status: KnowledgeStatus | None = None) -> list[ClaimRecord]:
        claims = [r for r in self.load_records() if isinstance(r, ClaimRecord)]
        return claims if status is None else [c for c in claims if c.status is status]

    def load_aliases(self) -> list[AliasRecord]:
        return [r for r in self.load_records() if isinstance(r, AliasRecord)]

    def load_constraints(self) -> list[ConstraintRecord]:
        return [r for r in self.load_records() if isinstance(r, ConstraintRecord)]

    def load_sources(self) -> list[SourceRecord]:
        return [r for r in self.load_records() if isinstance(r, SourceRecord)]

    def write_world(self, prolog_text: str) -> Path:
        self.ensure_root()
        self._atomic_write(self.world_path, prolog_text)
        return self.world_path

    def rewrite_records(self, records: Iterable[Record]) -> None:
        replacement = list(records)
        with self.transaction() as current:
            current[:] = replacement

    @staticmethod
    def _serialize(records: Iterable[Record]) -> str:
        return "".join(
            json.dumps(
                record_to_dict(r), sort_keys=True, ensure_ascii=False, allow_nan=False
            )
            + "\n"
            for r in records
        )

    @staticmethod
    def _atomic_write(path: Path, text: str) -> None:
        fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
