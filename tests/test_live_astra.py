"""Opt-in paid API checks. Synthetic sources only; no user knowledge is touched."""

from __future__ import annotations

import os

import pytest

from logical.openai_client import DEFAULT_MODEL, OpenAIExtractor
from logical.schema import QueryIntent
from logical.service import (
    add_knowledge,
    ask_knowledge,
    ask_query,
    check_knowledge,
    compress_knowledge,
    freshness_report,
)
from logical.store import KnowledgeStore

pytestmark = pytest.mark.skipif(
    os.getenv("LOGICAL_LIVE_TESTS") != "1",
    reason="Set LOGICAL_LIVE_TESTS=1 to run paid Astra API checks",
)


def test_live_astra_translates_resolves_proves_and_updates(tmp_path):
    store = KnowledgeStore(tmp_path)
    extractor = OpenAIExtractor(model=DEFAULT_MODEL)
    text = "Ada Lovelace, also known as Ada, is a person. Every person is a mammal. All mammals breathe. Her home city is London. Ada Lovelace has at most one home city at a time."
    added = add_knowledge(
        text, store, extractor, interactive=False, source_ref="synthetic:ada"
    )
    assert added.accepted and not (
        added.invalid or added.quarantined or added.unresolved
    )
    answer = ask_knowledge("Does Ada breathe?", store, extractor)
    assert answer.answer == "true" and len(answer.evidence) == 3
    old_city = next(c for c in store.load_claims() if c.o == "london")
    updated = add_knowledge(
        text.replace("London", "Paris"),
        store,
        extractor,
        interactive=False,
        replaces=added.source_id,
    )
    assert not (updated.invalid or updated.quarantined or updated.unresolved)
    assert (
        ask_query(QueryIntent(old_city.s, old_city.p, "london"), store).answer
        == "unknown"
    )
    assert (
        ask_query(QueryIntent(old_city.s, old_city.p, "paris"), store).answer == "true"
    )
    assert any(
        r["o"] == "london" and r["freshness"] == "stale"
        for r in freshness_report(store)
    )
    assert check_knowledge(store).ok
    assert compress_knowledge(store)["stats"]["basis_claims"] >= 3


def test_live_astra_preserves_ambiguous_coreference_for_review(tmp_path):
    store = KnowledgeStore(tmp_path)
    text = "Alice met Beth. She won the prize."
    result = add_knowledge(
        text, store, OpenAIExtractor(model=DEFAULT_MODEL), interactive=False
    )
    assert result.unresolved, "Ambiguous pronoun must be retained for review"
    source = store.load_sources()[0]
    assert not any(r["mention"].lower() == "she" for r in source.resolutions)
    assert not any(a.alias == "she" for a in store.load_aliases())
    assert not any(
        c.s in {"alice", "beth"} and ("won" in c.p or "win" in c.p)
        for c in result.accepted
    )
