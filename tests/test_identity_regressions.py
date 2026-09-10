from __future__ import annotations

import pytest

from logical.schema import (
    AliasRecord,
    ClaimRecord,
    Evidence,
    ExtractionResult,
    QueryIntent,
    ReferenceBinding,
    SourceRecord,
    parse_time,
)
from logical.service import (
    add_extraction,
    ask_knowledge,
    ask_query,
    freshness_report,
)
from logical.store import KnowledgeStore


@pytest.fixture(autouse=True)
def current_time(monkeypatch):
    current = ["2026-09-10T12:00:00Z"]
    monkeypatch.setattr(
        "logical.service.evaluation_time",
        lambda at=None: parse_time(at or current[0]),
    )
    return current


def source(text, *, review_after="2099-01-01T00:00:00Z", **kwargs):
    return SourceRecord(
        text,
        observed_at=kwargs.pop("observed_at", "2026-09-01T00:00:00Z"),
        review_after=review_after,
        **kwargs,
    )


def claim(
    subject,
    predicate,
    obj,
    quote,
    *,
    o_kind="value",
    polarity=True,
    s_ref=None,
    o_ref=None,
):
    return ClaimRecord(
        subject,
        predicate,
        obj,
        quote,
        s_kind="object",
        o_kind=o_kind,
        polarity=polarity,
        evidence=[Evidence("", quote, s_ref=s_ref, o_ref=o_ref)],
    )


def alias_source(store, text, canonical, alias, **kwargs):
    identity = source(text, **kwargs)
    result = add_extraction(
        ExtractionResult(
            aliases=[AliasRecord(canonical, alias, evidence=text)],
        ),
        store,
        source=identity,
    )
    assert not result.invalid and not result.unresolved
    return identity


def add_prize_claim(store, *, subject="bob", text="Bob won the prize.", s_ref=None):
    document = source(text)
    result = add_extraction(
        ExtractionResult(claims=[claim(subject, "won", "prize", text, s_ref=s_ref)]),
        store,
        source=document,
    )
    assert not result.invalid and not result.quarantined
    return document, result


def test_local_fruit_reference_does_not_rebind_canonical_company(tmp_path):
    store = KnowledgeStore(tmp_path)
    company = source("Apple is headquartered in Cupertino.")
    add_extraction(
        ExtractionResult(
            claims=[
                claim(
                    "apple",
                    "headquartered_in",
                    "cupertino",
                    company.text,
                    o_kind="object",
                )
            ]
        ),
        store,
        source=company,
    )
    document = source(
        "A red apple sat on the table. The apple fell. Apple sells phones."
    )
    result = add_extraction(
        ExtractionResult(
            claims=[
                claim(
                    "red_apple",
                    "sat_on",
                    "table",
                    "A red apple sat on the table.",
                    o_kind="object",
                ),
                claim(
                    "red_apple",
                    "fell",
                    "true",
                    "The apple fell.",
                    s_ref=ReferenceBinding("The apple", resolution=0),
                ),
                claim(
                    "apple", "sells", "phone", "Apple sells phones.", o_kind="category"
                ),
            ],
            resolutions=[
                {
                    "mention": "The apple",
                    "canonical": "red_apple",
                    "evidence": "A red apple sat on the table. The apple fell.",
                }
            ],
        ),
        store,
        source=document,
    )

    assert len(result.accepted) == 3 and not result.invalid
    assert ask_query(QueryIntent("apple", "sells", "phone"), store).answer == "true"
    assert (
        ask_query(QueryIntent("red_apple", "sells", "phone"), store).answer == "unknown"
    )
    assert ask_query(QueryIntent("red_apple", "fell", "true"), store).answer == "true"


def test_document_resolution_does_not_guess_an_unbound_pronoun(tmp_path):
    store = KnowledgeStore(tmp_path)
    document = source("Ada wrote a report. She submitted it. Beth arrived. She left.")
    result = add_extraction(
        ExtractionResult(
            claims=[
                claim("ada", "wrote", "report", "Ada wrote a report."),
                claim("ada", "submitted", "report", "She submitted it."),
                claim("she", "left", "true", "She left."),
            ],
            resolutions=[
                {
                    "mention": "She",
                    "canonical": "ada",
                    "evidence": "Ada wrote a report. She submitted it.",
                }
            ],
        ),
        store,
        source=document,
    )

    assert result.quarantined and result.invalid
    assert ask_query(QueryIntent("ada", "left", "true"), store).answer == "unknown"
    assert ask_query(QueryIntent("beth", "left", "true"), store).answer == "unknown"
    assert ask_query(QueryIntent("ada", "submitted", "report"), store).answer == "true"


def test_repeated_pronouns_use_their_own_explicit_claim_bindings(tmp_path):
    store = KnowledgeStore(tmp_path)
    ada_passage = "Ada wrote a report. She submitted it."
    beth_passage = "Beth wrote a letter. She mailed it."
    document = source(f"{ada_passage} {beth_passage}")
    result = add_extraction(
        ExtractionResult(
            claims=[
                claim(
                    "ada",
                    "submitted",
                    "report",
                    "She submitted it.",
                    s_ref=ReferenceBinding("She", resolution=0),
                ),
                claim(
                    "beth",
                    "mailed",
                    "letter",
                    "She mailed it.",
                    s_ref=ReferenceBinding("She", resolution=1),
                ),
            ],
            resolutions=[
                {"mention": "She", "canonical": "ada", "evidence": ada_passage},
                {"mention": "She", "canonical": "beth", "evidence": beth_passage},
            ],
        ),
        store,
        source=document,
    )

    assert len(result.accepted) == 2 and not result.invalid
    for subject, predicate, obj in (
        ("ada", "submitted", "report"),
        ("beth", "mailed", "letter"),
    ):
        assert ask_query(QueryIntent(subject, predicate, obj), store).answer == "true"
    assert ask_query(QueryIntent("ada", "mailed", "letter"), store).answer == "unknown"
    assert (
        ask_query(QueryIntent("beth", "submitted", "report"), store).answer == "unknown"
    )


def test_reference_binding_outside_its_resolution_passage_is_rejected(tmp_path):
    store = KnowledgeStore(tmp_path)
    ada_passage = "Ada wrote a report. She submitted it."
    document = source(f"{ada_passage} Beth arrived. She left.")
    result = add_extraction(
        ExtractionResult(
            claims=[
                claim(
                    "ada",
                    "submitted",
                    "report",
                    "She submitted it.",
                    s_ref=ReferenceBinding("She", resolution=0),
                ),
                claim(
                    "ada",
                    "left",
                    "true",
                    "She left.",
                    s_ref=ReferenceBinding("She", resolution=0),
                ),
            ],
            resolutions=[
                {"mention": "She", "canonical": "ada", "evidence": ada_passage}
            ],
        ),
        store,
        source=document,
    )

    assert len(result.quarantined) == 1 and result.invalid
    assert ask_query(QueryIntent("ada", "left", "true"), store).answer == "unknown"
    assert ask_query(QueryIntent("ada", "submitted", "report"), store).answer == "true"


def test_resolution_quote_must_locate_one_occurrence_of_the_mention(tmp_path):
    store = KnowledgeStore(tmp_path)
    document = source("Ada arrived. She waited. Beth arrived. She left.")
    result = add_extraction(
        ExtractionResult(
            claims=[
                claim(
                    "ada",
                    "left",
                    "true",
                    document.text,
                    s_ref=ReferenceBinding("She", 0),
                )
            ],
            resolutions=[
                {
                    "mention": "She",
                    "canonical": "ada",
                    "antecedent": "Ada",
                    "evidence": document.text,
                }
            ],
        ),
        store,
        source=document,
    )
    assert result.quarantined and result.invalid
    assert ask_query(QueryIntent("ada", "left", "true"), store).answer == "unknown"


def test_reference_cannot_match_only_a_substring_of_another_name(tmp_path):
    store = KnowledgeStore(tmp_path)
    document = source("Adaline left.")
    result = add_extraction(
        ExtractionResult(
            claims=[
                claim(
                    "ada", "left", "true", document.text, s_ref=ReferenceBinding("Ada")
                )
            ]
        ),
        store,
        source=document,
    )
    assert result.quarantined and result.invalid
    assert ask_query(QueryIntent("ada", "left", "true"), store).answer == "unknown"


def test_direct_name_binding_cannot_assert_a_different_identity(tmp_path):
    store = KnowledgeStore(tmp_path)
    document = source("Beth left.")
    result = add_extraction(
        ExtractionResult(
            claims=[
                claim(
                    "ada", "left", "true", document.text, s_ref=ReferenceBinding("Beth")
                )
            ]
        ),
        store,
        source=document,
    )

    assert result.quarantined and result.invalid
    assert ask_query(QueryIntent("ada", "left", "true"), store).answer == "unknown"


@pytest.mark.parametrize("explicit_antecedent", [False, True])
def test_pronoun_claim_preserves_its_antecedents_alias_dependency(
    tmp_path, explicit_antecedent
):
    store = KnowledgeStore(tmp_path)
    identity = alias_source(
        store,
        "Robert is also called Bob.",
        "robert",
        "bob",
        review_after="2026-09-15T00:00:00Z",
    )
    document = source("Bob arrived. He won the prize.")
    resolution = {
        "mention": "He",
        "canonical": "robert",
        "evidence": document.text,
    }
    if explicit_antecedent:
        resolution["antecedent"] = "Bob"
    added = add_extraction(
        ExtractionResult(
            claims=[
                claim(
                    "robert",
                    "arrived",
                    "true",
                    "Bob arrived.",
                    s_ref=ReferenceBinding("Bob"),
                ),
                claim(
                    "robert",
                    "won",
                    "prize",
                    "He won the prize.",
                    s_ref=ReferenceBinding("He", resolution=0),
                ),
            ],
            resolutions=[resolution],
        ),
        store,
        source=document,
    )
    assert len(added.accepted) == 2 and not added.invalid
    before = ask_query(QueryIntent("robert", "won", "prize"), store)
    assert before.answer == "true"
    assert identity.id in {a.source_id for a in before.identity_evidence}
    assert (
        ask_query(
            QueryIntent("robert", "won", "prize"),
            store,
            at="2026-09-16T00:00:00Z",
        ).answer
        == "unknown"
    )


@pytest.mark.parametrize("canonical_output", [False, True])
def test_alias_expiry_invalidates_dependent_attribution(tmp_path, canonical_output):
    store = KnowledgeStore(tmp_path)
    identity = alias_source(
        store,
        "Robert is also called Bob.",
        "robert",
        "bob",
        review_after="2026-09-15T00:00:00Z",
    )
    document, added = add_prize_claim(
        store,
        subject="robert" if canonical_output else "bob",
        s_ref=ReferenceBinding("Bob") if canonical_output else None,
    )

    before = ask_query(
        QueryIntent("robert", "won", "prize"), store, at="2026-09-14T00:00:00Z"
    )
    assert before.answer == "true"
    assert {s.id for s in before.sources} == {identity.id, document.id}
    assert [(a.alias, a.canonical, a.source_id) for a in before.identity_evidence] == [
        ("bob", "robert", identity.id)
    ]
    assert (
        ask_query(
            QueryIntent("robert", "won", "prize"), store, at="2026-09-16T00:00:00Z"
        ).answer
        == "unknown"
    )
    rows = freshness_report(store, at="2026-09-16T00:00:00Z")
    assert (
        next(r for r in rows if r["id"] == added.accepted[0].id)["freshness"] == "stale"
    )
    assert next(r for r in rows if r["id"] == document.id)["freshness"] == "fresh"


def test_canonical_object_reference_also_depends_on_its_alias_source(tmp_path):
    store = KnowledgeStore(tmp_path)
    identity = alias_source(
        store,
        "Robert is also called Bob.",
        "robert",
        "bob",
        review_after="2026-09-15T00:00:00Z",
    )
    document = source("Acme hired Bob.")
    result = add_extraction(
        ExtractionResult(
            claims=[
                claim(
                    "acme",
                    "hired",
                    "robert",
                    document.text,
                    o_kind="object",
                    o_ref=ReferenceBinding("Bob"),
                )
            ]
        ),
        store,
        source=document,
    )
    assert len(result.accepted) == 1 and not result.invalid
    answer = ask_query(QueryIntent("acme", "hired", "robert"), store)
    assert answer.answer == "true"
    assert identity.id in {a.source_id for a in answer.identity_evidence}
    assert (
        ask_query(
            QueryIntent("acme", "hired", "robert"),
            store,
            at="2026-09-16T00:00:00Z",
        ).answer
        == "unknown"
    )


def test_canonical_category_without_optional_binding_preserves_alias_dependency(
    tmp_path,
):
    store = KnowledgeStore(tmp_path)
    identity = alias_source(
        store,
        "The category Housecat is another name for the category Domestic Cat.",
        "domestic_cat",
        "housecat",
        review_after="2026-09-15T00:00:00Z",
    )
    document = source("Every Housecat breathes. Felix is a Domestic Cat.")
    added = add_extraction(
        ExtractionResult(
            claims=[
                ClaimRecord(
                    "domestic_cat",
                    "breathes",
                    "true",
                    "Every Housecat breathes.",
                    s_kind="category",
                    o_kind="value",
                    scope="all",
                    evidence=[Evidence("", "Every Housecat breathes.")],
                ),
                claim(
                    "felix",
                    "instance_of",
                    "domestic_cat",
                    "Felix is a Domestic Cat.",
                    o_kind="category",
                    s_ref=ReferenceBinding("Felix"),
                ),
            ]
        ),
        store,
        source=document,
    )
    assert len(added.accepted) == 2 and not added.invalid
    before = ask_query(QueryIntent("felix", "breathes", "true"), store)
    assert before.answer == "true"
    assert identity.id in {a.source_id for a in before.identity_evidence}
    assert (
        ask_query(
            QueryIntent("felix", "breathes", "true"),
            store,
            at="2026-09-16T00:00:00Z",
        ).answer
        == "unknown"
    )


@pytest.mark.parametrize("canonical_output", [False, True])
def test_alias_correction_does_not_keep_or_transfer_old_attribution(
    tmp_path, canonical_output
):
    store = KnowledgeStore(tmp_path)
    identity = alias_source(store, "Robert is also called Bob.", "robert", "bob")
    add_prize_claim(
        store,
        subject="robert" if canonical_output else "bob",
        s_ref=ReferenceBinding("Bob") if canonical_output else None,
    )
    assert ask_query(QueryIntent("robert", "won", "prize"), store).answer == "true"

    alias_source(
        store,
        "Barbara is also called Bob.",
        "barbara",
        "bob",
        observed_at="2026-09-09T00:00:00Z",
        supersedes=identity.id,
    )

    for subject in ("robert", "barbara", "bob"):
        assert (
            ask_query(QueryIntent(subject, "won", "prize"), store).answer == "unknown"
        )


@pytest.mark.parametrize("support_arrives_after_claim", [False, True])
def test_independent_identity_support_survives_one_alias_source_expiring(
    tmp_path, support_arrives_after_claim
):
    store = KnowledgeStore(tmp_path)
    alias_source(
        store,
        "Robert is also called Bob.",
        "robert",
        "bob",
        review_after="2026-09-15T00:00:00Z",
    )
    if support_arrives_after_claim:
        document, _ = add_prize_claim(store)
    independent = alias_source(
        store,
        "Bob is another name for Robert.",
        "robert",
        "bob",
        review_after="2030-01-01T00:00:00Z",
    )
    if not support_arrives_after_claim:
        document, _ = add_prize_claim(store)

    answer = ask_query(
        QueryIntent("robert", "won", "prize"), store, at="2026-09-16T00:00:00Z"
    )
    assert answer.answer == "true"
    assert set(answer.freshness.values()) == {"fresh"}
    assert {independent.id, document.id} <= {s.id for s in answer.sources}
    assert (
        ask_query(
            QueryIntent("robert", "won", "prize"), store, at="2031-01-01T00:00:00Z"
        ).answer
        == "unknown"
    )


def test_direct_evidence_survives_expiry_of_alias_dependent_duplicate(tmp_path):
    store = KnowledgeStore(tmp_path)
    alias_source(
        store,
        "Robert is also called Bob.",
        "robert",
        "bob",
        review_after="2026-09-15T00:00:00Z",
    )
    add_prize_claim(store)
    direct, result = add_prize_claim(
        store, subject="robert", text="Robert won the prize."
    )
    assert result.duplicates

    answer = ask_query(
        QueryIntent("robert", "won", "prize"), store, at="2026-09-16T00:00:00Z"
    )
    assert answer.answer == "true"
    assert set(answer.freshness.values()) == {"fresh"}
    assert direct.id in {s.id for s in answer.sources}


def test_query_translation_and_answer_use_the_same_snapshot(tmp_path, current_time):
    store = KnowledgeStore(tmp_path)
    original = source("The Countess is Ada. Ada breathes.")
    add_extraction(
        ExtractionResult(
            aliases=[AliasRecord("ada", "countess", evidence="The Countess is Ada.")],
            claims=[claim("ada", "breathes", "true", "Ada breathes.")],
        ),
        store,
        source=original,
    )
    independent = source("Beth breathes.")
    add_extraction(
        ExtractionResult(claims=[claim("beth", "breathes", "true", independent.text)]),
        store,
        source=independent,
    )
    assert (
        ask_query(QueryIntent("countess", "breathes", "true"), store).answer == "true"
    )
    started_at = parse_time(current_time[0])

    class ConcurrentQueryExtractor:
        def extract_query_with_context(self, text, context):
            assert context["aliases"]["countess"] == "ada"
            current_time[0] = "2026-09-10T12:00:01Z"
            replacement = source(
                "The Countess is Beth. Ada does not breathe.",
                observed_at=current_time[0],
                supersedes=original.id,
            )
            updated = add_extraction(
                ExtractionResult(
                    aliases=[
                        AliasRecord(
                            "beth", "countess", evidence="The Countess is Beth."
                        )
                    ],
                    claims=[
                        claim(
                            "ada",
                            "breathes",
                            "true",
                            "Ada does not breathe.",
                            polarity=False,
                        )
                    ],
                ),
                store,
                source=replacement,
            )
            assert not updated.invalid and not updated.quarantined
            return QueryIntent(context["aliases"]["countess"], "breathes", "true")

    answer = ask_knowledge(
        "Does the Countess breathe?", store, ConcurrentQueryExtractor()
    )

    assert (
        ask_query(QueryIntent("countess", "breathes", "true"), store).answer == "true"
    )
    assert ask_query(QueryIntent("ada", "breathes", "true"), store).answer == "false"
    assert answer.answer == "true"
    assert parse_time(answer.evaluated_at) == started_at
    assert original.id in {s.id for s in answer.sources}


@pytest.mark.parametrize("explicit_binding", [False, True])
def test_natural_language_query_retains_canonicalized_identity_proof(
    tmp_path, explicit_binding
):
    store = KnowledgeStore(tmp_path)
    identity = alias_source(store, "The Countess is Ada.", "ada", "countess")
    document = source("Ada breathes.")
    add_extraction(
        ExtractionResult(claims=[claim("ada", "breathes", "true", document.text)]),
        store,
        source=document,
    )

    class CanonicalQueryExtractor:
        def extract_query_with_context(self, text, context):
            return QueryIntent(
                context["aliases"]["countess"],
                "breathes",
                "true",
                s_ref=ReferenceBinding("the Countess") if explicit_binding else None,
            )

    answer = ask_knowledge(
        "Does the Countess breathe?", store, CanonicalQueryExtractor()
    )
    assert answer.answer == "true"
    assert {s.id for s in answer.sources} == {identity.id, document.id}
    assert [(a.alias, a.canonical, a.source_id) for a in answer.identity_evidence] == [
        ("countess", "ada", identity.id)
    ]
