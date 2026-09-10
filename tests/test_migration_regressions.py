import json

import pytest

from logical.schema import (
    ClaimRecord,
    Evidence,
    ExtractionResult,
    QueryIntent,
    SourceRecord,
    record_to_dict,
)
from logical.service import (
    add_knowledge,
    ask_query,
    check_knowledge,
    compress_knowledge,
    export_prolog,
    freshness_report,
)
from logical.store import KnowledgeStore


def test_source_versions_without_identity_provenance_require_retranslation(tmp_path):
    store = KnowledgeStore(tmp_path)
    source = SourceRecord(
        "Ada is a person.",
        observed_at="2025-01-01T00:00:00Z",
        review_after="2099-01-01T00:00:00Z",
    )
    claim = ClaimRecord(
        "ada",
        "instance_of",
        "person",
        "",
        s_kind="object",
        o_kind="category",
        evidence=[Evidence(source.id, source.text)],
    )
    raw_source = record_to_dict(source)
    raw_source.pop("translation_version")
    store.ensure_root()
    store.knowledge_path.write_text(
        json.dumps(raw_source) + "\n" + json.dumps(record_to_dict(claim)) + "\n"
    )
    query = QueryIntent("ada", "instance_of", "person")
    assert ask_query(query, store).answer == "unknown"
    row = next(r for r in freshness_report(store) if r["id"] == source.id)
    assert row["freshness"] == "stale" and "identity provenance" in row["reasons"][0]
    assert check_knowledge(store).ok

    class Reextract:
        def extract_knowledge(self, text):
            return ExtractionResult(
                claims=[
                    ClaimRecord(
                        "ada",
                        "instance_of",
                        "person",
                        text,
                        s_kind="object",
                        o_kind="category",
                    )
                ]
            )

    result = add_knowledge(
        source.text, store, Reextract(), interactive=False, replaces=source.id
    )
    assert not result.invalid and not result.quarantined
    assert ask_query(query, store).answer == "true"
    assert (
        next(
            s for s in store.load_sources() if s.id == result.source_id
        ).translation_version
        == 2
    )


@pytest.mark.parametrize("export", [export_prolog, compress_knowledge])
def test_exports_refuse_an_inconsistent_active_snapshot(tmp_path, export):
    store = KnowledgeStore(tmp_path)
    store.append_records(
        [
            ClaimRecord("ada", "breathes", "true", "Ada breathes.", polarity=polarity)
            for polarity in (True, False)
        ]
    )
    with pytest.raises(ValueError, match="inconsistent"):
        export(store)


@pytest.mark.parametrize("value", [3, "2", True])
def test_unknown_or_malformed_source_versions_fail_explicitly(value):
    with pytest.raises(ValueError, match="translation version"):
        SourceRecord("Ada breathes.", translation_version=value)


def test_unsupported_current_quotes_cannot_be_queried_or_exported(tmp_path):
    store = KnowledgeStore(tmp_path)
    source = SourceRecord("Ada breathes.")
    claim = ClaimRecord(
        "ada", "breathes", "true", "", evidence=[Evidence(source.id, "Beth breathes.")]
    )
    store.append_records([source, claim])
    assert not check_knowledge(store).ok
    result = ask_query(QueryIntent("ada", "breathes", "true"), store)
    assert result.answer == "unknown" and "provenance" in result.reason
    with pytest.raises(ValueError, match="provenance"):
        export_prolog(store)
