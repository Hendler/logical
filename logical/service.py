from __future__ import annotations

from dataclasses import dataclass
import sys

from logical.conflicts import Conflict, find_conflicts
from logical.openai_client import OpenAIExtractor
from logical.prolog import (
    project_world,
    query_for_intent,
    run_swipl_query,
    validate_with_swipl,
)
from logical.schema import ClaimRecord, ExtractionResult, KnowledgeStatus, QueryIntent
from logical.store import KnowledgeStore
from logical.validation import ValidationIssue, validate_claim, validate_constraint


@dataclass
class AddResult:
    accepted: list[ClaimRecord]
    quarantined: list[ClaimRecord]
    conflicts: list[Conflict]
    invalid: list[ValidationIssue]


@dataclass
class AskResult:
    answer: str
    evidence: list[ClaimRecord]
    query: QueryIntent


@dataclass
class CheckResult:
    ok: bool
    message: str


def add_knowledge(
    text: str,
    store: KnowledgeStore | None = None,
    extractor: OpenAIExtractor | None = None,
    interactive: bool | None = None,
) -> AddResult:
    store = store or KnowledgeStore()
    extractor = extractor or OpenAIExtractor()
    interactive = sys.stdin.isatty() if interactive is None else interactive

    extraction = extractor.extract_knowledge(text)
    result = add_extraction(extraction, store, interactive=interactive)
    rebuild_world(store)
    return result


def add_extraction(
    extraction: ExtractionResult,
    store: KnowledgeStore,
    interactive: bool = False,
) -> AddResult:
    accepted: list[ClaimRecord] = []
    quarantined: list[ClaimRecord] = []
    conflicts: list[Conflict] = []
    invalid: list[ValidationIssue] = []
    existing_claims = store.load_claims(status=KnowledgeStatus.ACCEPTED)
    valid_constraints = []
    for constraint in extraction.constraints:
        issues = validate_constraint(constraint)
        if issues:
            invalid.extend(issues)
        else:
            valid_constraints.append(constraint)
    constraints = store.load_constraints() + valid_constraints

    for claim in extraction.claims:
        validation_issues = validate_claim(claim)
        if validation_issues:
            claim.status = KnowledgeStatus.QUARANTINED
            quarantined.append(claim)
            invalid.extend(validation_issues)
            continue
        claim_conflicts = find_conflicts(claim, existing_claims + accepted, constraints)
        if claim_conflicts:
            decision = _conflict_decision(claim, claim_conflicts, interactive)
            if decision == "replace":
                replaced_ids = {
                    conflict.existing_claim_id for conflict in claim_conflicts
                }
                _quarantine_existing(
                    store,
                    replaced_ids,
                )
                existing_claims = [
                    existing
                    for existing in existing_claims
                    if existing.id not in replaced_ids
                ]
                accepted.append(claim)
            else:
                claim.status = KnowledgeStatus.QUARANTINED
                quarantined.append(claim)
            conflicts.extend(claim_conflicts)
        else:
            accepted.append(claim)

    store.append_records(
        [*extraction.aliases, *valid_constraints, *accepted, *quarantined]
    )
    return AddResult(
        accepted=accepted,
        quarantined=quarantined,
        conflicts=conflicts,
        invalid=invalid,
    )


def ask_knowledge(
    text: str,
    store: KnowledgeStore | None = None,
    extractor: OpenAIExtractor | None = None,
) -> AskResult:
    store = store or KnowledgeStore()
    extractor = extractor or OpenAIExtractor()
    query = extractor.extract_query(text)
    rebuild_world(store)

    answer = _ask_with_prolog_or_memory(store, query)
    evidence = _evidence_for_query(store, query)
    return AskResult(answer=answer, evidence=evidence, query=query)


def check_knowledge(store: KnowledgeStore | None = None) -> CheckResult:
    store = store or KnowledgeStore()
    world_path = rebuild_world(store)
    result = validate_with_swipl(world_path)
    return CheckResult(ok=result.ok, message=result.message)


def export_prolog(store: KnowledgeStore | None = None) -> str:
    store = store or KnowledgeStore()
    return project_world(
        store.load_claims(status=KnowledgeStatus.ACCEPTED),
        store.load_constraints(),
    )


def rebuild_world(store: KnowledgeStore) -> str:
    prolog_text = export_prolog(store)
    return str(store.write_world(prolog_text))


def _ask_with_prolog_or_memory(store: KnowledgeStore, query: QueryIntent) -> str:
    try:
        if run_swipl_query(store.world_path, query_for_intent(query)):
            return "true"
        negated = QueryIntent(
            s=query.s,
            p=query.p,
            o=query.o,
            polarity=not query.polarity,
        )
        if run_swipl_query(store.world_path, query_for_intent(negated)):
            return "false"
        return "unknown"
    except RuntimeError:
        return _ask_in_memory(store, query)


def _ask_in_memory(store: KnowledgeStore, query: QueryIntent) -> str:
    claims = store.load_claims(status=KnowledgeStatus.ACCEPTED)
    for claim in claims:
        if (claim.s, claim.p, claim.o) == (query.s, query.p, query.o):
            if claim.polarity == query.polarity:
                return "true"
            return "false"
    return "unknown"


def _evidence_for_query(store: KnowledgeStore, query: QueryIntent) -> list[ClaimRecord]:
    return [
        claim
        for claim in store.load_claims(status=KnowledgeStatus.ACCEPTED)
        if (claim.s, claim.p, claim.o) == (query.s, query.p, query.o)
    ]


def _conflict_decision(
    claim: ClaimRecord, conflicts: list[Conflict], interactive: bool
) -> str:
    if not interactive:
        return "quarantine"
    print(f"Conflict for {claim.s} {claim.p} {claim.o}:")
    for conflict in conflicts:
        print(f"- {conflict.message}")
    choice = input("Choose [k]eep existing, [r]eplace existing, [q]uarantine new: ")
    if choice.strip().lower().startswith("r"):
        return "replace"
    return "quarantine"


def _quarantine_existing(store: KnowledgeStore, claim_ids: set[str]) -> None:
    records = store.load_records()
    for record in records:
        if isinstance(record, ClaimRecord) and record.id in claim_ids:
            record.status = KnowledgeStatus.QUARANTINED
    store.rewrite_records(records)
