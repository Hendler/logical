from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json

import pytest

from logical import cli
from logical.openai_client import parse_extraction_response
from logical.reasoning import infer
from logical.schema import (
    AliasRecord,
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
    compress_knowledge,
    export_prolog,
    freshness_report,
)
from logical.store import KnowledgeStore


def claim(
    s, p, o, *, s_kind="object", o_kind="value", scope="fact", polarity=True, **kwargs
):
    return ClaimRecord(
        s,
        p,
        o,
        f"{s} {p} {o}",
        s_kind=s_kind,
        o_kind=o_kind,
        scope=scope,
        polarity=polarity,
        **kwargs,
    )


def taxonomy():
    return [
        claim("ada", "instance_of", "person", o_kind="category", id="ada-person"),
        claim(
            "person",
            "subclass_of",
            "mammal",
            s_kind="category",
            o_kind="category",
            id="person-mammal",
        ),
        claim(
            "mammal",
            "breathes",
            "true",
            s_kind="category",
            scope="all",
            id="mammals-breathe",
        ),
    ]


class ScriptedExtractor:
    model = "fixture"

    def __init__(self, extraction):
        self.extraction = extraction
        self.calls = 0
        self.contexts = []

    def extract_knowledge_with_context(self, text, context):
        self.calls += 1
        self.contexts.append(context)
        result = deepcopy(self.extraction)
        for c in result.claims:
            c.source_text = text
        return result


def ingest(store, text, claims, **kwargs):
    return add_knowledge(
        text,
        store,
        ScriptedExtractor(ExtractionResult(claims=claims)),
        interactive=False,
        **kwargs,
    )


def test_typed_entailment_has_complete_proof_and_open_world_answers(tmp_path):
    store = KnowledgeStore(tmp_path)
    added = add_extraction(ExtractionResult(claims=taxonomy()), store)
    assert len(added.accepted) == 3
    result = ask_query(QueryIntent("ada", "breathes", "true"), store)
    assert result.answer == "true"
    assert {c.id for c in result.evidence} == {
        "ada-person",
        "person-mammal",
        "mammals-breathe",
    }
    assert (
        ask_query(QueryIntent("someone_else", "breathes", "true"), store).answer
        == "unknown"
    )
    assert (
        ask_query(QueryIntent("ada", "breathes", "true", False), store).answer
        == "false"
    )
    assert check_knowledge(store).ok


def test_collective_category_properties_do_not_apply_to_members(tmp_path):
    store = KnowledgeStore(tmp_path)
    claims = taxonomy()[:2] + [claim("mammal", "widespread", "true", s_kind="category")]
    add_extraction(ExtractionResult(claims=claims), store)
    assert (
        ask_query(QueryIntent("mammal", "widespread", "true"), store).answer == "true"
    )
    assert (
        ask_query(QueryIntent("ada", "widespread", "true"), store).answer == "unknown"
    )


@pytest.mark.parametrize(
    "bad",
    [
        claim("mammal", "instance_of", "animal", s_kind="category", o_kind="category"),
        claim("ada", "subclass_of", "person", o_kind="category"),
        claim("ada", "breathes", "true", scope="all"),
        claim("ada", "breathes", "true", scope="most"),
        claim("she", "breathes", "true"),
    ],
)
def test_category_quantifier_and_unresolved_reference_errors_are_quarantined(
    tmp_path, bad
):
    store = KnowledgeStore(tmp_path)
    result = add_extraction(ExtractionResult(claims=[bad]), store)
    assert result.invalid and result.quarantined
    assert not result.accepted
    assert not infer(store.load_claims(KnowledgeStatus.ACCEPTED)).proofs


def test_known_object_cannot_be_reused_as_category(tmp_path):
    store = KnowledgeStore(tmp_path)
    add_extraction(
        ExtractionResult(claims=[claim("ada", "lives_in", "london", o_kind="object")]),
        store,
    )
    result = add_extraction(
        ExtractionResult(
            claims=[
                claim(
                    "ada", "subclass_of", "person", s_kind="category", o_kind="category"
                )
            ]
        ),
        store,
    )
    assert {i.kind for i in result.invalid} == {"category_error"}


def test_inferred_contradiction_is_quarantined_in_either_order(tmp_path):
    for negative_first in (False, True):
        store = KnowledgeStore(tmp_path / str(negative_first))
        claims = taxonomy()
        negative = claim("ada", "breathes", "true", polarity=False)
        first, second = ([negative], claims) if negative_first else (claims, [negative])
        add_extraction(ExtractionResult(claims=first), store)
        result = add_extraction(ExtractionResult(claims=second), store)
        assert result.quarantined and result.conflicts
        assert result.conflicts[0].kind == "inferred_contradiction"
        assert check_knowledge(store).ok


def test_late_constraint_cannot_make_accepted_facts_inconsistent(tmp_path):
    store = KnowledgeStore(tmp_path)
    add_extraction(
        ExtractionResult(
            claims=[claim("door", "color", "red"), claim("door", "color", "blue")]
        ),
        store,
    )
    result = add_extraction(
        ExtractionResult(
            constraints=[
                ConstraintRecord("functional_for_subject", "door", "color", "")
            ]
        ),
        store,
    )
    assert {i.kind for i in result.invalid} == {"conflicting_constraint"}
    assert not store.load_constraints()
    assert check_knowledge(store).ok


def test_duplicates_combine_independent_evidence_and_provenance(tmp_path):
    store = KnowledgeStore(tmp_path)
    a = ingest(
        store, "Ada breathes.", [claim("ada", "breathes", "true")], source_ref="doc:a"
    )
    b = ingest(
        store,
        "Ada does breathe.",
        [claim("ada", "breathes", "true")],
        source_ref="doc:b",
    )
    claims = store.load_claims()
    assert len(claims) == 1 and len(claims[0].evidence) == 2
    assert b.duplicates == [a.accepted[0].id]
    assert {e.source_id for e in claims[0].evidence} == {a.source_id, b.source_id}
    assert claims[0].source_text == ""
    assert len(store.load_sources()) == 2
    assert compress_knowledge(store)["stats"]["assertions_per_basis_claim"] == 2


def test_retry_does_not_call_model_or_make_stale_evidence_fresh(tmp_path):
    store = KnowledgeStore(tmp_path)
    extractor = ScriptedExtractor(
        ExtractionResult(claims=[claim("ada", "breathes", "true")])
    )
    observed = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    first = add_knowledge(
        "Ada breathes.", store, extractor, observed_at=observed, ttl_days=1
    )
    original = store.knowledge_path.read_bytes()
    retry = add_knowledge("Ada breathes.", store, extractor, ttl_days=100)
    assert extractor.calls == 1
    assert retry.source_id == first.source_id
    assert store.knowledge_path.read_bytes() == original
    assert freshness_report(store)[0]["freshness"] == "stale"
    assert ask_query(QueryIntent("ada", "breathes", "true"), store).answer == "unknown"


def test_expired_premise_invalidates_derived_answer(tmp_path):
    store = KnowledgeStore(tmp_path)
    premises = taxonomy()
    ingest(store, "Ada is a person.", [premises[0]], ttl_days=0)
    ingest(store, "All people are mammals and all mammals breathe.", premises[1:])
    assert ask_query(QueryIntent("ada", "breathes", "true"), store).answer == "unknown"
    assert "triple(ada,instance_of,person)." not in export_prolog(store)


def test_validity_window_is_exclusive_and_requires_timezone(tmp_path):
    store = KnowledgeStore(tmp_path)
    source = SourceRecord(
        "Ada lives in London.",
        observed_at="2025-01-01T00:00:00Z",
        review_after="2027-01-01T00:00:00Z",
    )
    timed = claim(
        "ada",
        "lives_in",
        "london",
        o_kind="object",
        evidence=[
            Evidence(
                source.id, source.text, "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z"
            )
        ],
    )
    add_extraction(ExtractionResult(claims=[timed]), store, source=source)
    query = QueryIntent("ada", "lives_in", "london")
    assert ask_query(query, store, at="2025-12-31T00:00:00Z").answer == "unknown"
    assert ask_query(query, store, at="2026-01-01T00:00:00Z").answer == "true"
    assert ask_query(query, store, at="2026-02-01T00:00:00Z").answer == "unknown"
    bad = claim(
        "ada",
        "lives_in",
        "paris",
        o_kind="object",
        evidence=[Evidence(source.id, source.text, "2026-01-01")],
    )
    result = add_extraction(ExtractionResult(claims=[bad]), store)
    assert "invalid_validity" in {i.kind for i in result.invalid}


def test_source_update_preserves_history_and_other_independent_support(tmp_path):
    store = KnowledgeStore(tmp_path)
    old = ingest(
        store,
        "Ada lives in London.",
        [claim("ada", "lives_in", "london", o_kind="object")],
    )
    ingest(
        store,
        "Another source says Ada lives in London.",
        [claim("ada", "lives_in", "london", o_kind="object")],
    )
    new = ingest(
        store,
        "Ada lives in Paris.",
        [claim("ada", "lives_in", "paris", o_kind="object")],
        replaces=old.source_id,
    )
    assert ask_query(QueryIntent("ada", "lives_in", "london"), store).answer == "true"
    assert ask_query(QueryIntent("ada", "lives_in", "paris"), store).answer == "true"
    sources = {s.id: s for s in store.load_sources()}
    assert sources[old.source_id].superseded_by == new.source_id
    assert sources[new.source_id].supersedes == old.source_id


def test_failed_update_does_not_change_any_persisted_record(tmp_path):
    store = KnowledgeStore(tmp_path)
    old = ingest(store, "Ada breathes.", [claim("ada", "breathes", "true")])
    before = store.knowledge_path.read_bytes()
    ambiguous = ScriptedExtractor(
        ExtractionResult(
            claims=[claim("ada", "breathes", "true", polarity=False)],
            unresolved=[{"text": "She moved.", "reason": "unclear referent"}],
        )
    )
    with pytest.raises(ValueError, match="previous source preserved"):
        add_knowledge("She moved.", store, ambiguous, replaces=old.source_id)
    assert store.knowledge_path.read_bytes() == before
    assert ask_query(QueryIntent("ada", "breathes", "true"), store).answer == "true"


def test_changed_and_deleted_files_are_stale_without_refreshing_timestamps(tmp_path):
    store = KnowledgeStore(tmp_path / "store")
    path = tmp_path / "source.txt"
    path.write_text("Ada breathes.")
    ingest(
        store, path.read_text(), [claim("ada", "breathes", "true")], file_path=str(path)
    )
    assert freshness_report(store)[0]["freshness"] == "fresh"
    path.write_text("Ada does not breathe.")
    assert "contents changed" in freshness_report(store)[0]["reasons"][0]
    assert ask_query(QueryIntent("ada", "breathes", "true"), store).answer == "unknown"
    path.unlink()
    assert "unavailable" in freshness_report(store)[0]["reasons"][0]


def test_aliases_apply_to_ingestion_queries_and_conflicts(tmp_path):
    store = KnowledgeStore(tmp_path)
    text = "Ada Lovelace, also known as Ada, breathes."
    extractor = ScriptedExtractor(
        ExtractionResult(
            claims=[claim("ada_lovelace", "breathes", "true")],
            aliases=[AliasRecord("ada_lovelace", "ada", evidence=text)],
        )
    )
    add_knowledge(text, store, extractor)
    assert ask_query(QueryIntent("ada", "breathes", "true"), store).answer == "true"
    conflicting = ingest(
        store,
        "Ada does not breathe.",
        [claim("ada", "breathes", "true", polarity=False)],
    )
    assert conflicting.quarantined and conflicting.conflicts


@pytest.mark.parametrize(
    "aliases",
    [
        [AliasRecord("ada", "she")],
        [AliasRecord("ada", "lovelace"), AliasRecord("other_person", "lovelace")],
        [AliasRecord("a_person", "b_person"), AliasRecord("b_person", "a_person")],
    ],
)
def test_unsafe_alias_sets_cannot_affect_knowledge(tmp_path, aliases):
    store = KnowledgeStore(tmp_path)
    extractor = ScriptedExtractor(
        ExtractionResult(claims=[claim("ada", "breathes", "true")], aliases=aliases)
    )
    result = add_knowledge("An ambiguous source.", store, extractor)
    assert result.invalid and result.quarantined
    assert not store.load_aliases()
    assert ask_query(QueryIntent("ada", "breathes", "true"), store).answer == "unknown"


def test_unresolved_mentions_remain_auditable_and_never_become_global_aliases(tmp_path):
    store = KnowledgeStore(tmp_path)
    unresolved = [
        {"text": "She left.", "reason": "Alice or Beth could be the referent"}
    ]
    result = add_knowledge(
        "Alice met Beth. She left.",
        store,
        ScriptedExtractor(ExtractionResult(unresolved=unresolved)),
    )
    assert result.unresolved == unresolved
    assert store.load_sources()[0].unresolved == unresolved
    assert not store.load_aliases() and not store.load_claims()


def test_quotes_must_exist_in_source_before_accepting_claim(tmp_path):
    store = KnowledgeStore(tmp_path)
    payload = {
        "claims": [
            {
                "s": "ada",
                "p": "breathes",
                "o": "true",
                "s_kind": "object",
                "o_kind": "value",
                "evidence": "Ada breathes.",
            }
        ]
    }
    extraction = parse_extraction_response(payload, "Ada is here.")
    result = add_knowledge("Ada is here.", store, ScriptedExtractor(extraction))
    assert result.quarantined
    assert "unsupported_evidence" in {i.kind for i in result.invalid}
    assert not ask_query(QueryIntent("ada", "breathes", "true"), store).evidence


def test_compaction_removes_only_entailed_facts_with_final_basis_proofs(tmp_path):
    store = KnowledgeStore(tmp_path)
    claims = taxonomy() + [
        claim("ada", "breathes", "true", id="redundant"),
        claim("ada", "favorite_color", "red", id="independent"),
    ]
    add_extraction(ExtractionResult(claims=claims), store)
    before = store.knowledge_path.read_bytes()
    compressed = compress_knowledge(store)
    assert compressed["entailed"] == {
        "redundant": ["ada-person", "mammals-breathe", "person-mammal"]
    }
    assert {c["id"] for c in compressed["basis"]} == {
        "ada-person",
        "mammals-breathe",
        "person-mammal",
        "independent",
    }
    basis_ids = {c["id"] for c in compressed["basis"]}
    assert set(infer([c for c in claims if c.id in basis_ids]).proofs) == set(
        infer(claims).proofs
    )
    assert store.knowledge_path.read_bytes() == before


def test_concurrent_writers_do_not_drop_records(tmp_path):
    store = KnowledgeStore(tmp_path)

    def write(index):
        return add_extraction(
            ExtractionResult(claims=[claim(f"object_{index}", "color", "red")]), store
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(write, range(20)))
    assert all(len(r.accepted) == 1 for r in results)
    assert len(store.load_claims()) == 20
    assert check_knowledge(store).ok


def test_interrupted_atomic_write_preserves_previous_store(tmp_path, monkeypatch):
    store = KnowledgeStore(tmp_path)
    store.append_records([claim("ada", "breathes", "true")])
    original = store.knowledge_path.read_bytes()

    def fail(*args):
        raise OSError("simulated disk failure")

    monkeypatch.setattr("logical.store.os.replace", fail)
    with pytest.raises(OSError, match="disk failure"):
        store.append_records([claim("bob", "breathes", "true")])
    assert store.knowledge_path.read_bytes() == original
    assert not list(tmp_path.glob(".knowledge.jsonl.*"))


def test_translation_context_race_preserves_newer_writes(tmp_path):
    store = KnowledgeStore(tmp_path)

    class RacingExtractor(ScriptedExtractor):
        def extract_knowledge_with_context(self, text, context):
            store.append_records([claim("concurrent", "exists", "true")])
            return super().extract_knowledge_with_context(text, context)

    with pytest.raises(ValueError, match="changed during translation"):
        add_knowledge(
            "Ada breathes.",
            store,
            RacingExtractor(
                ExtractionResult(claims=[claim("ada", "breathes", "true")])
            ),
        )
    assert [c.s for c in store.load_claims()] == ["concurrent"]
    assert not store.load_sources()


def test_legacy_records_remain_readable_with_explicit_unknown_freshness(tmp_path):
    store = KnowledgeStore(tmp_path)
    store.knowledge_path.write_text(
        json.dumps(
            {
                "type": "claim",
                "s": "sky",
                "p": "color",
                "o": "red",
                "source_text": "the sky is red",
            }
        )
        + "\n"
    )
    result = ask_query(QueryIntent("sky", "color", "red"), store)
    assert result.answer == "true"
    assert set(result.freshness.values()) == {"unknown"}
    assert freshness_report(store)[0]["freshness"] == "unknown"


def test_integrity_check_detects_hash_tampering_and_inconsistent_store(tmp_path):
    store = KnowledgeStore(tmp_path)
    ingest(store, "Ada breathes.", [claim("ada", "breathes", "true")])
    store.append_records([claim("ada", "breathes", "true", polarity=False)])
    assert not check_knowledge(store).ok
    text = store.knowledge_path.read_text().replace(
        '"text": "Ada breathes."', '"text": "Altered source."'
    )
    store.knowledge_path.write_text(text)
    assert "content hash" in check_knowledge(store).message


def test_cli_offline_flow_and_invalid_update_recovery(tmp_path, capsys):
    args = ["--store-dir", str(tmp_path)]
    extractor = ScriptedExtractor(
        ExtractionResult(claims=[claim("ada", "breathes", "true")])
    )
    assert cli.main(args + ["add", "Ada breathes.", "--json"], extractor) == 0
    source_id = json.loads(capsys.readouterr().out)["source_id"]
    assert cli.main(args + ["query", "ada", "breathes", "true", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["answer"] == "true"
    assert cli.main(args + ["compress"]) == 0
    assert json.loads(capsys.readouterr().out)["stats"]["basis_claims"] == 1
    assert cli.main(args + ["stale", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == []
    assert cli.main(args + ["update", source_id, "", "--json"], extractor) == 1
    assert "must not be empty" in capsys.readouterr().err
    assert cli.main(args + ["inspect"]) == 0
    assert len(json.loads(capsys.readouterr().out)["records"]) == 2


def test_opposing_universals_are_vacuously_consistent_until_a_member_exists(tmp_path):
    store = KnowledgeStore(tmp_path)
    rules = [
        claim("unicorn", "flies", "true", s_kind="category", scope="all"),
        claim(
            "unicorn", "flies", "true", s_kind="category", scope="all", polarity=False
        ),
    ]
    result = add_extraction(ExtractionResult(claims=rules), store)
    assert len(result.accepted) == 2
    assert check_knowledge(store).ok
    member = claim("twilight", "instance_of", "unicorn", o_kind="category")
    result = add_extraction(ExtractionResult(claims=[member]), store)
    assert result.quarantined and result.conflicts
    assert check_knowledge(store).ok


def test_duplicate_record_ids_abort_without_corrupting_the_store(tmp_path):
    store = KnowledgeStore(tmp_path)
    add_extraction(
        ExtractionResult(claims=[claim("ada", "breathes", "true", id="fixed")]), store
    )
    before = store.knowledge_path.read_bytes()
    with pytest.raises(ValueError, match="duplicate record IDs"):
        add_extraction(
            ExtractionResult(claims=[claim("bob", "breathes", "true", id="fixed")]),
            store,
        )
    assert store.knowledge_path.read_bytes() == before


def test_inference_limit_aborts_entire_transaction(tmp_path, monkeypatch):
    store = KnowledgeStore(tmp_path)
    monkeypatch.setattr("logical.reasoning.MAX_FACTS", 2)
    with pytest.raises(ValueError, match="fact limit"):
        add_extraction(ExtractionResult(claims=taxonomy()), store)
    assert not store.knowledge_path.exists()


def test_changed_source_reference_requires_explicit_update_before_api_call(tmp_path):
    store = KnowledgeStore(tmp_path)
    old = ingest(
        store, "Ada breathes.", [claim("ada", "breathes", "true")], source_ref="doc:ada"
    )
    extractor = ScriptedExtractor(ExtractionResult())
    with pytest.raises(ValueError, match=f"logical update {old.source_id}"):
        add_knowledge("Different contents.", store, extractor, source_ref="doc:ada")
    assert extractor.calls == 0


def test_constraint_only_source_is_reported_when_stale(tmp_path):
    store = KnowledgeStore(tmp_path)
    extractor = ScriptedExtractor(
        ExtractionResult(
            constraints=[
                ConstraintRecord("functional_for_subject", "ada", "lives_in", "")
            ]
        )
    )
    result = add_knowledge(
        "Ada lives in at most one city.", store, extractor, ttl_days=0
    )
    rows = freshness_report(store)
    assert any(r["id"] == result.source_id and r["freshness"] == "stale" for r in rows)
    assert "functional_for_subject(ada,lives_in)." not in export_prolog(store)


def test_expired_alias_cannot_rebind_future_mentions(tmp_path):
    store = KnowledgeStore(tmp_path)
    extractor = ScriptedExtractor(
        ExtractionResult(
            claims=[claim("ada_lovelace", "breathes", "true")],
            aliases=[AliasRecord("ada_lovelace", "ada")],
        )
    )
    add_knowledge(
        "Ada Lovelace is also called Ada and breathes.", store, extractor, ttl_days=0
    )
    ingest(store, "Ada Lovelace breathes.", [claim("ada_lovelace", "breathes", "true")])
    assert (
        ask_query(QueryIntent("ada_lovelace", "breathes", "true"), store).answer
        == "true"
    )
    assert ask_query(QueryIntent("ada", "breathes", "true"), store).answer == "unknown"


def test_fresh_proof_is_preferred_to_unknown_legacy_assertion(tmp_path):
    store = KnowledgeStore(tmp_path)
    add_extraction(ExtractionResult(claims=[claim("ada", "breathes", "true")]), store)
    ingest(
        store,
        "Ada is a person. All people are mammals. All mammals breathe.",
        taxonomy(),
    )
    result = ask_query(QueryIntent("ada", "breathes", "true"), store)
    assert result.answer == "true"
    assert set(result.freshness.values()) == {"fresh"}
    assert len(result.evidence) == 3


def test_grounded_coreference_is_applied_locally_without_retyping_categories(tmp_path):
    from logical.schema import ReferenceBinding

    store = KnowledgeStore(tmp_path)
    text = "Ada is a mathematician. The mathematician breathes."
    extraction = ExtractionResult(
        claims=[
            claim("ada", "instance_of", "mathematician", o_kind="category"),
            claim(
                "ada",
                "breathes",
                "true",
                evidence=[
                    Evidence(
                        "",
                        "The mathematician breathes.",
                        s_ref=ReferenceBinding("The mathematician", 0),
                    )
                ],
            ),
        ],
        resolutions=[
            {"mention": "The mathematician", "canonical": "ada", "evidence": text}
        ],
    )
    result = add_knowledge(text, store, ScriptedExtractor(extraction))
    assert len(result.accepted) == 2 and not result.invalid
    assert ask_query(QueryIntent("ada", "breathes", "true"), store).answer == "true"
    assert (
        ask_query(QueryIntent("ada", "instance_of", "mathematician"), store).answer
        == "true"
    )
    assert not store.load_aliases()
    assert (
        ask_query(QueryIntent("mathematician", "breathes", "true"), store).answer
        == "unknown"
    )


def test_nonoverlapping_values_do_not_violate_current_functional_constraint(tmp_path):
    store = KnowledgeStore(tmp_path)
    source = SourceRecord(
        "Ada's home city was London and is now Paris. She has at most one home city at a time.",
        observed_at="2025-01-01T00:00:00Z",
        review_after="2030-01-01T00:00:00Z",
    )
    old = claim(
        "ada",
        "home_city",
        "london",
        o_kind="object",
        evidence=[
            Evidence(
                source.id, source.text, "2025-01-01T00:00:00Z", "2026-01-01T00:00:00Z"
            )
        ],
    )
    current = claim(
        "ada",
        "home_city",
        "paris",
        o_kind="object",
        evidence=[Evidence(source.id, source.text, "2026-01-01T00:00:00Z", None)],
    )
    result = add_extraction(
        ExtractionResult(
            claims=[old, current],
            constraints=[
                ConstraintRecord(
                    "functional_for_subject",
                    "ada",
                    "home_city",
                    "",
                    evidence=source.text,
                )
            ],
        ),
        store,
        source=source,
    )
    assert len(result.accepted) == 2 and not result.conflicts
    assert check_knowledge(store).ok


def test_time_activated_functional_conflicts_do_not_produce_unqualified_answers(
    tmp_path,
):
    store = KnowledgeStore(tmp_path)
    source = SourceRecord(
        "Two future home cities are asserted, but only one is allowed.",
        observed_at="2025-01-01T00:00:00Z",
        review_after="2099-01-01T00:00:00Z",
    )
    values = [
        claim(
            "ada",
            "home_city",
            city,
            o_kind="object",
            evidence=[Evidence(source.id, source.text, "2090-01-01T00:00:00Z")],
        )
        for city in ("london", "paris")
    ]
    result = add_extraction(
        ExtractionResult(
            claims=values,
            constraints=[
                ConstraintRecord(
                    "functional_for_subject",
                    "ada",
                    "home_city",
                    "",
                    evidence=source.text,
                )
            ],
        ),
        store,
        source=source,
    )
    assert len(result.accepted) == 2
    answer = ask_query(
        QueryIntent("ada", "home_city", "london"), store, at="2090-01-02T00:00:00Z"
    )
    assert answer.answer == "unknown" and "inconsistent" in answer.reason
    assert len(answer.evidence) == 2
