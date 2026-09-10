from __future__ import annotations

from copy import deepcopy
import json

import pytest

from logical import cli
from logical.schema import (
    ClaimRecord,
    ConstraintRecord,
    Evidence,
    ExtractionResult,
    KnowledgeStatus,
    QueryIntent,
    SourceRecord,
)
from logical.service import (
    add_extraction,
    add_knowledge,
    ask_query,
    check_knowledge,
    export_prolog,
)
from logical.store import KnowledgeStore


def category_claim(position: str) -> ClaimRecord:
    if position == "object":
        return ClaimRecord(
            "ada",
            "instance_of",
            "person",
            "Ada is a person.",
            s_kind="object",
            o_kind="category",
        )
    return ClaimRecord(
        "person",
        "widespread",
        "true",
        "People are widespread.",
        s_kind="category",
        o_kind="value",
    )


def category_constraint() -> ConstraintRecord:
    return ConstraintRecord("functional_for_subject", "person", "home_city", "")


@pytest.mark.parametrize("position", ["object", "subject"])
@pytest.mark.parametrize("constraint_first", [False, True])
def test_category_typing_rejects_constraint_and_preserves_valid_facts(
    tmp_path, position, constraint_first
):
    store = KnowledgeStore(tmp_path)
    constraint = category_constraint()
    if constraint_first:
        initial = add_extraction(ExtractionResult(constraints=[constraint]), store)
        assert not initial.invalid
        assert store.load_constraints()

    typed = category_claim(position)
    result = add_extraction(
        ExtractionResult(
            claims=[typed], constraints=[] if constraint_first else [constraint]
        ),
        store,
    )

    assert {c.id for c in result.accepted} == {typed.id}
    assert not result.quarantined
    assert any(issue.kind == "category_error" for issue in result.invalid)
    assert ask_query(QueryIntent(typed.s, typed.p, typed.o), store).answer == "true"
    assert "functional_for_subject(person,home_city)." not in export_prolog(store)

    later = add_extraction(
        ExtractionResult(
            claims=[
                ClaimRecord(
                    "person",
                    "diverse",
                    "true",
                    "People are diverse.",
                    s_kind="category",
                    o_kind="value",
                )
            ]
        ),
        store,
    )
    assert len(later.accepted) == 1
    assert not later.invalid and not later.quarantined
    assert ask_query(QueryIntent("person", "diverse", "true"), store).answer == "true"
    assert check_knowledge(store).ok


def test_persisted_category_constraint_fails_check_and_qualifies_query(tmp_path):
    store = KnowledgeStore(tmp_path)
    member = category_claim("object")
    add_extraction(ExtractionResult(claims=[member]), store)
    # Simulate a store created before category-constraint validation was fixed.
    store.append_records([category_constraint()])
    before = store.knowledge_path.read_bytes()

    checked = check_knowledge(store)
    answer = ask_query(QueryIntent("ada", "instance_of", "person"), store)

    assert not checked.ok
    assert "category" in checked.message.lower()
    assert answer.answer == "unknown"
    assert "category" in answer.reason.lower()
    assert {c.id for c in store.load_claims(KnowledgeStatus.ACCEPTED)} == {member.id}
    assert store.knowledge_path.read_bytes() == before


def test_valid_category_source_update_can_retire_an_older_invalid_constraint(tmp_path):
    store = KnowledgeStore(tmp_path)
    add_extraction(ExtractionResult(constraints=[category_constraint()]), store)

    class KindExtractor:
        def __init__(self, kind):
            self.kind = kind

        def extract_knowledge(self, text):
            return ExtractionResult(
                claims=[
                    ClaimRecord(
                        "person",
                        "widespread",
                        "true",
                        text,
                        s_kind=self.kind,
                        o_kind="value",
                    )
                ]
            )

    old = add_knowledge(
        "People are widespread.", store, KindExtractor("unknown"), interactive=False
    )
    updated = add_knowledge(
        "People are a widespread category.",
        store,
        KindExtractor("category"),
        interactive=False,
        replaces=old.source_id,
    )
    assert updated.accepted and not updated.quarantined
    assert not updated.invalid and updated.warnings
    assert "older invalid constraint" in updated.warnings[0]
    assert (
        next(s for s in store.load_sources() if s.id == old.source_id).superseded_by
        == updated.source_id
    )
    assert not store.load_constraints()
    assert (
        ask_query(QueryIntent("person", "widespread", "true"), store).answer == "true"
    )
    assert check_knowledge(store).ok


@pytest.mark.parametrize("rejection", ["quarantined", "uncertain", "conflicting"])
def test_rejected_category_claim_cannot_disable_an_accepted_constraint(
    tmp_path, rejection
):
    store = KnowledgeStore(tmp_path)
    initial_claims = (
        [
            ClaimRecord(
                "person",
                "widespread",
                "true",
                "People are not widespread.",
                polarity=False,
            )
        ]
        if rejection == "conflicting"
        else []
    )
    add_extraction(
        ExtractionResult(claims=initial_claims, constraints=[category_constraint()]),
        store,
    )
    source = SourceRecord("People are widespread.")
    candidate = category_claim("subject")
    # Model evidence has no source ID until ingestion binds it to this source.
    candidate.evidence = [Evidence("", source.text)]
    if rejection == "quarantined":
        candidate.status = KnowledgeStatus.QUARANTINED
    elif rejection == "uncertain":
        candidate.confidence = 0.1

    result = add_extraction(ExtractionResult(claims=[candidate]), store, source=source)

    assert not result.accepted
    assert {c.id for c in result.quarantined} == {candidate.id}
    assert len(store.load_constraints()) == 1
    assert store.load_constraints()[0].status is KnowledgeStatus.ACCEPTED
    assert "functional_for_subject(person,home_city)." in export_prolog(store)

    # Rejected type evidence must not let a later object acquire two values.
    later = add_extraction(
        ExtractionResult(
            claims=[
                ClaimRecord(
                    "person",
                    "home_city",
                    city,
                    f"Person lives in {city}.",
                    s_kind="object",
                    o_kind="object",
                )
                for city in ("london", "paris")
            ]
        ),
        store,
    )
    assert len(later.accepted) == 1
    assert len(later.quarantined) == 1
    assert check_knowledge(store).ok


def test_rejected_constraint_quote_does_not_poison_active_integrity(tmp_path):
    store = KnowledgeStore(tmp_path)
    member = category_claim("object")
    add_extraction(ExtractionResult(claims=[member]), store)
    source = SourceRecord("A new policy was considered.")
    result = add_extraction(
        ExtractionResult(
            constraints=[
                ConstraintRecord(
                    "functional_for_subject",
                    "ada",
                    "home_city",
                    "",
                    evidence="This quotation does not occur in the source.",
                )
            ]
        ),
        store,
        source=source,
    )

    assert {issue.kind for issue in result.invalid} == {"unsupported_constraint"}
    assert not store.load_constraints()
    rejected = store.load_constraints(status=KnowledgeStatus.QUARANTINED)
    assert len(rejected) == 1 and rejected[0].issues
    assert (
        ask_query(QueryIntent("ada", "instance_of", "person"), store).answer == "true"
    )
    assert check_knowledge(store).ok


class ConstraintExtractor:
    model = "fixture"

    def __init__(self, extraction: ExtractionResult) -> None:
        self.extraction = extraction
        self.calls = 0

    def extract_knowledge_with_context(self, text, context):
        self.calls += 1
        return deepcopy(self.extraction)


def test_repeated_rejected_constraint_keeps_cli_failure_and_source_audit(
    tmp_path, capsys
):
    store = KnowledgeStore(tmp_path)
    add_extraction(
        ExtractionResult(
            claims=[
                ClaimRecord(
                    "door",
                    "color",
                    color,
                    f"The door is {color}.",
                    s_kind="object",
                    o_kind="value",
                )
                for color in ("red", "blue")
            ]
        ),
        store,
    )
    text = "The door can have at most one color."
    extractor = ConstraintExtractor(
        ExtractionResult(
            constraints=[
                ConstraintRecord(
                    "functional_for_subject", "door", "color", "", evidence=text
                )
            ]
        )
    )
    args = [
        "--store-dir",
        str(tmp_path),
        "add",
        text,
        "--source-ref",
        "doc:door-color-policy",
        "--noninteractive",
        "--json",
    ]

    first_code = cli.main(args, extractor=extractor)
    first = json.loads(capsys.readouterr().out)
    before_retry = store.knowledge_path.read_bytes()
    second_code = cli.main(args, extractor=extractor)
    second = json.loads(capsys.readouterr().out)

    assert (first_code, second_code) == (2, 2)
    assert extractor.calls == 1
    assert second["source_id"] == first["source_id"]
    assert second["invalid"] == first["invalid"]
    assert {issue["kind"] for issue in first["invalid"]} == {"conflicting_constraint"}
    source = next(s for s in store.load_sources() if s.id == first["source_id"])
    assert source.validation_issues == first["invalid"]
    assert store.knowledge_path.read_bytes() == before_retry
    assert not store.load_constraints()
    assert check_knowledge(store).ok


def test_retry_reports_constraint_rejected_after_later_category_typing(
    tmp_path, capsys
):
    store = KnowledgeStore(tmp_path)
    text = "Person has at most one home city."
    extractor = ConstraintExtractor(
        ExtractionResult(
            constraints=[
                ConstraintRecord(
                    "functional_for_subject", "person", "home_city", "", evidence=text
                )
            ]
        )
    )
    args = [
        "--store-dir",
        str(tmp_path),
        "add",
        text,
        "--source-ref",
        "doc:person-home-city-policy",
        "--noninteractive",
        "--json",
    ]
    assert cli.main(args, extractor=extractor) == 0
    first = json.loads(capsys.readouterr().out)
    typed = add_extraction(ExtractionResult(claims=[category_claim("object")]), store)
    assert len(typed.accepted) == 1
    assert not store.load_constraints()
    before_retry = store.knowledge_path.read_bytes()

    retry_code = cli.main(args, extractor=extractor)
    retry = json.loads(capsys.readouterr().out)

    assert retry_code == 2
    assert retry["source_id"] == first["source_id"]
    assert {issue["kind"] for issue in retry["invalid"]} == {"category_error"}
    assert extractor.calls == 1
    source = next(s for s in store.load_sources() if s.id == first["source_id"])
    assert source.validation_issues == retry["invalid"]
    assert store.knowledge_path.read_bytes() == before_retry
