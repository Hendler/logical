from pathlib import Path

from logical.conflicts import find_conflicts
from logical.prolog import project_world
from logical.schema import ClaimRecord, ConstraintRecord, KnowledgeStatus, RecordType
from logical.store import KnowledgeStore


def test_store_round_trips_jsonl_records(tmp_path):
    store = KnowledgeStore(tmp_path)
    claim = ClaimRecord(
        id="claim-1",
        s="sky",
        p="color",
        o="red",
        source_text="the sky is red",
        confidence=0.92,
    )

    store.append_records([claim])

    loaded = store.load_records()
    assert loaded == [claim]
    assert store.load_claims(status=KnowledgeStatus.ACCEPTED) == [claim]


def test_prolog_projection_uses_only_accepted_claims(tmp_path):
    accepted = ClaimRecord(
        id="claim-1",
        s="sky",
        p="color",
        o="red",
        source_text="the sky is red",
    )
    quarantined = ClaimRecord(
        id="claim-2",
        s="sky",
        p="color",
        o="blue",
        source_text="the sky is blue",
        status=KnowledgeStatus.QUARANTINED,
    )
    constraint = ConstraintRecord(
        kind="functional_for_subject",
        s="sky",
        p="color",
        source_claim_id="claim-constraint",
    )

    world = project_world([accepted, quarantined], [constraint])

    assert "triple(sky,color,red)." in world
    assert "triple(sky,color,blue)." not in world
    assert "functional_for_subject(sky,color)." in world


def test_functional_constraint_conflict_is_detected():
    existing = ClaimRecord(
        id="claim-1",
        s="sky",
        p="color",
        o="red",
        source_text="the sky is red",
    )
    candidate = ClaimRecord(
        id="claim-2",
        s="sky",
        p="color",
        o="blue",
        source_text="the sky is blue",
    )
    constraint = ConstraintRecord(
        kind="functional_for_subject",
        s="sky",
        p="color",
        source_claim_id="claim-3",
    )

    conflicts = find_conflicts(candidate, [existing], [constraint])

    assert len(conflicts) == 1
    assert conflicts[0].kind == "functional_for_subject"
    assert conflicts[0].existing_claim_id == "claim-1"


def test_direct_polarity_conflict_is_detected():
    existing = ClaimRecord(
        id="claim-1",
        s="bird",
        p="can_fly",
        o="penguin",
        source_text="penguins can fly",
    )
    candidate = ClaimRecord(
        id="claim-2",
        s="bird",
        p="can_fly",
        o="penguin",
        polarity=False,
        source_text="penguins cannot fly",
    )

    conflicts = find_conflicts(candidate, [existing], [])

    assert len(conflicts) == 1
    assert conflicts[0].kind == "direct_contradiction"


def test_record_type_is_persisted_for_future_migrations(tmp_path):
    store = KnowledgeStore(tmp_path)
    claim = ClaimRecord(
        id="claim-1",
        s="sky",
        p="color",
        o="red",
        source_text="the sky is red",
    )

    store.append_records([claim])

    raw = Path(tmp_path, "knowledge.jsonl").read_text()
    assert f'"type": "{RecordType.CLAIM.value}"' in raw
