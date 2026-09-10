from __future__ import annotations

from copy import deepcopy

import pytest

from logical.schema import (
    AliasDependency,
    AliasRecord,
    ClaimRecord,
    ConstraintRecord,
    Evidence,
    ExtractionResult,
    QueryIntent,
    ReferenceBinding,
    SourceRecord,
    parse_time,
)
from logical.service import (
    add_extraction,
    add_knowledge,
    ask_knowledge,
    ask_query,
    check_knowledge,
    compress_knowledge,
    export_prolog,
)
from logical.store import KnowledgeStore
from logical.freshness import evidence_state


def test_future_validity_does_not_hide_expired_identity_support():
    from logical.schema import parse_time

    identity = SourceRecord(
        "Robert is Bob.",
        observed_at="2025-01-01T00:00:00Z",
        review_after="2026-01-01T00:00:00Z",
    )
    document = SourceRecord(
        "Bob will live in Paris from 2030.",
        observed_at="2025-01-01T00:00:00Z",
        review_after="2099-01-01T00:00:00Z",
    )
    evidence = Evidence(
        document.id,
        document.text,
        "2030-01-01T00:00:00Z",
        identity_dependencies=[AliasDependency("bob", "robert", [identity.id])],
    )
    status, reason = evidence_state(
        evidence,
        {s.id: s for s in (identity, document)},
        parse_time("2026-09-10T00:00:00Z"),
    )
    assert status == "stale" and "identity bob = robert" in reason


def test_future_constraint_conflict_cites_rule_and_its_identity_premise(tmp_path):
    from logical.schema import AliasRecord, ConstraintRecord

    store = KnowledgeStore(tmp_path)
    identity = SourceRecord(
        "Robert is Bob.",
        observed_at="2025-01-01T00:00:00Z",
        review_after="2099-01-01T00:00:00Z",
    )
    add_extraction(
        ExtractionResult(
            aliases=[AliasRecord("robert", "bob", evidence=identity.text)]
        ),
        store,
        source=identity,
    )
    rule = SourceRecord(
        "Bob has at most one home city.",
        observed_at="2025-01-01T00:00:00Z",
        review_after="2099-01-01T00:00:00Z",
    )
    add_extraction(
        ExtractionResult(
            constraints=[
                ConstraintRecord(
                    "functional_for_subject", "bob", "home_city", "", evidence=rule.text
                )
            ]
        ),
        store,
        source=rule,
    )
    document = SourceRecord(
        "From 2030 Robert will have home cities London and Paris.",
        observed_at="2025-01-01T00:00:00Z",
        review_after="2099-01-01T00:00:00Z",
    )
    add_extraction(
        ExtractionResult(
            claims=[
                ClaimRecord(
                    "robert",
                    "home_city",
                    city,
                    document.text,
                    s_kind="object",
                    o_kind="object",
                    evidence=[
                        Evidence(document.id, document.text, "2030-01-01T00:00:00Z")
                    ],
                )
                for city in ("london", "paris")
            ]
        ),
        store,
        source=document,
    )
    answer = ask_query(
        QueryIntent("robert", "home_city", "london"), store, at="2031-01-01T00:00:00Z"
    )
    assert answer.answer == "unknown" and "functional conflict" in answer.reason
    assert {s.id for s in answer.sources} == {identity.id, rule.id, document.id}
    assert [c.source_id for c in answer.constraint_evidence] == [rule.id]
    assert [a.source_id for a in answer.identity_evidence] == [identity.id]


class FixedExtractor:
    model = "fixture"

    def __init__(self, claim: ClaimRecord) -> None:
        self.claim = claim

    def extract_knowledge_with_context(self, text, context):
        claim = deepcopy(self.claim)
        claim.source_text = text
        return ExtractionResult(claims=[claim])


def object_claim(subject: str, predicate: str, obj: str) -> ClaimRecord:
    return ClaimRecord(
        subject,
        predicate,
        obj,
        "fixture",
        s_kind="object",
        o_kind="object",
    )


def test_historical_file_answers_survive_replacement_and_deletion(tmp_path):
    store = KnowledgeStore(tmp_path / "store")
    path = tmp_path / "source.txt"
    path.write_text("Ada lives in London.", encoding="utf-8")
    old = add_knowledge(
        path.read_text(encoding="utf-8"),
        store,
        FixedExtractor(object_claim("ada", "lives_in", "london")),
        file_path=str(path),
        observed_at="2025-01-01T00:00:00Z",
        ttl_days=36500,
        interactive=False,
    )
    london = QueryIntent("ada", "lives_in", "london")
    paris = QueryIntent("ada", "lives_in", "paris")
    assert ask_query(london, store, at="2024-12-31T23:59:59Z").answer == "unknown"
    assert ask_query(london, store, at="2025-01-02T00:00:00Z").answer == "true"

    path.write_text("Ada lives in Paris.", encoding="utf-8")
    new = add_knowledge(
        path.read_text(encoding="utf-8"),
        store,
        FixedExtractor(object_claim("ada", "lives_in", "paris")),
        file_path=str(path),
        observed_at="2025-01-03T00:00:00Z",
        ttl_days=36500,
        replaces=old.source_id,
        interactive=False,
    )

    earlier = ask_query(london, store, at="2025-01-02T00:00:00Z")
    assert earlier.answer == "true"
    assert {source.id for source in earlier.sources} == {old.source_id}
    assert ask_query(paris, store, at="2025-01-02T00:00:00Z").answer == "unknown"
    assert ask_query(london, store, at="2025-01-03T00:00:00Z").answer == "unknown"
    replacement = ask_query(paris, store, at="2025-01-03T00:00:00Z")
    assert replacement.answer == "true"
    assert {source.id for source in replacement.sources} == {new.source_id}
    assert ask_query(paris, store, at="2025-01-04T00:00:00Z").answer == "true"
    assert ask_query(paris, store).answer == "true"

    path.unlink()
    assert ask_query(paris, store).answer == "unknown"
    assert ask_query(london, store, at="2025-01-02T00:00:00Z").answer == "true"
    assert ask_query(paris, store, at="2025-01-04T00:00:00Z").answer == "true"


@pytest.fixture
def future_kind_collision(tmp_path):
    store = KnowledgeStore(tmp_path)
    source = SourceRecord(
        "From 2090 Mercury is an individual planet and also a category of mammals.",
        observed_at="2025-01-01T00:00:00Z",
        review_after="2099-01-01T00:00:00Z",
    )
    claims = [
        ClaimRecord(
            "mercury",
            predicate,
            obj,
            source.text,
            s_kind=kind,
            o_kind="category",
            evidence=[Evidence(source.id, source.text, "2090-01-01T00:00:00Z")],
        )
        for predicate, obj, kind in (
            ("instance_of", "planet", "object"),
            ("subclass_of", "mammal", "category"),
        )
    ]
    result = add_extraction(ExtractionResult(claims=claims), store, source=source)
    assert len(result.accepted) == 2
    assert not result.invalid
    return store


@pytest.mark.parametrize(
    ("predicate", "obj"),
    [("instance_of", "planet"), ("subclass_of", "mammal")],
)
def test_future_type_conflict_cannot_produce_a_verified_answer(
    future_kind_collision, predicate, obj
):
    query = QueryIntent("mercury", predicate, obj)
    assert (
        ask_query(query, future_kind_collision, at="2089-12-31T23:59:59Z").answer
        == "unknown"
    )
    result = ask_query(query, future_kind_collision, at="2090-01-01T00:00:00Z")
    assert result.answer == "unknown"
    assert "inconsistent" in result.reason.lower()
    assert "object" in result.reason and "category" in result.reason


def test_check_rejects_time_activated_type_conflict(future_kind_collision):
    result = check_knowledge(future_kind_collision, at="2090-01-01T00:00:00Z")
    assert not result.ok
    assert "object" in result.message and "category" in result.message


@pytest.mark.parametrize("export", [export_prolog, compress_knowledge])
def test_exports_reject_time_activated_type_conflict(future_kind_collision, export):
    with pytest.raises(ValueError, match=r"object.*category|category.*object"):
        export(future_kind_collision, at="2090-01-01T00:00:00Z")


def test_query_translation_uses_one_file_freshness_snapshot(tmp_path):
    store = KnowledgeStore(tmp_path / "store")
    path = tmp_path / "source.txt"
    path.write_text("Ada lives in London.", encoding="utf-8")
    add_knowledge(
        path.read_text(encoding="utf-8"),
        store,
        FixedExtractor(object_claim("ada", "lives_in", "london")),
        file_path=str(path),
        interactive=False,
    )

    class FileChangingQueryExtractor:
        def extract_query_with_context(self, text: str, context: dict):
            assert any(
                claim["s"] == "ada" and claim["o"] == "london"
                for claim in context["claims"]
            )
            path.write_text("Ada lives in Paris.", encoding="utf-8")
            return QueryIntent("ada", "lives_in", "london")

    result = ask_knowledge(
        "Does Ada live in London?", store, FileChangingQueryExtractor()
    )
    assert result.answer == "true"
    assert set(result.freshness.values()) == {"fresh"}
    assert (
        ask_query(QueryIntent("ada", "lives_in", "london"), store).answer == "unknown"
    )


@pytest.mark.parametrize("canonical_output", [False, True])
@pytest.mark.parametrize("independent_identity_support", [False, True])
def test_constraint_freshness_requires_current_identity_evidence(
    tmp_path, monkeypatch, canonical_output, independent_identity_support
):
    store = KnowledgeStore(tmp_path)
    current = ["2026-09-10T00:00:00Z"]
    monkeypatch.setattr(
        "logical.service.evaluation_time",
        lambda at=None: parse_time(at or current[0]),
    )

    def source(text, review_after="2099-01-01T00:00:00Z"):
        return SourceRecord(text, observed_at=current[0], review_after=review_after)

    identity = source("Robert is also called Bob.", "2026-09-15T00:00:00Z")
    add_extraction(
        ExtractionResult(
            aliases=[AliasRecord("robert", "bob", evidence=identity.text)]
        ),
        store,
        source=identity,
    )
    document = source("Bob has at most one home city.")
    constraint = ConstraintRecord(
        "functional_for_subject",
        "robert" if canonical_output else "bob",
        "home_city",
        "",
        evidence=document.text,
        s_ref=ReferenceBinding("Bob") if canonical_output else None,
    )
    added = add_extraction(
        ExtractionResult(constraints=[constraint]), store, source=document
    )
    assert not added.invalid
    assert "functional_for_subject(robert,home_city)." in export_prolog(store)

    if independent_identity_support:
        independent = source("Bob is another name for Robert.")
        added = add_extraction(
            ExtractionResult(
                aliases=[AliasRecord("robert", "bob", evidence=independent.text)]
            ),
            store,
            source=independent,
        )
        assert not added.invalid

    london_source = source("Robert's home city is London.")
    london_claim = object_claim("robert", "home_city", "london")
    london_claim.source_text = london_source.text
    london = add_extraction(
        ExtractionResult(claims=[london_claim]),
        store,
        source=london_source,
    )
    assert len(london.accepted) == 1

    current[0] = "2026-09-16T00:00:00Z"
    paris_source = source("Robert's home city is Paris.")
    paris_claim = object_claim("robert", "home_city", "paris")
    paris_claim.source_text = paris_source.text
    paris = add_extraction(
        ExtractionResult(claims=[paris_claim]), store, source=paris_source
    )
    if independent_identity_support:
        assert len(paris.quarantined) == 1 and paris.conflicts
        assert "functional_for_subject(robert,home_city)." in export_prolog(store)
    else:
        assert len(paris.accepted) == 1 and not paris.conflicts
        assert "functional_for_subject(robert,home_city)." not in export_prolog(store)
        assert (
            ask_query(QueryIntent("robert", "home_city", "paris"), store).answer
            == "true"
        )
