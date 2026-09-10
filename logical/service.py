from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import timedelta
import math
import sys
from typing import Any

from logical.conflicts import Conflict, find_conflicts
from logical.freshness import claim_state, evaluation_time, source_index, source_state
from logical.openai_client import OpenAIExtractor
from logical.prolog import project_world, validate_with_swipl
from logical.reasoning import compact_basis, infer, inconsistencies
from logical.resolution import PRONOUNS, alias_index, canonical, term_kinds
from logical.schema import (
    AliasRecord,
    ClaimRecord,
    ConstraintRecord,
    Evidence,
    ExtractionResult,
    KnowledgeStatus,
    QueryIntent,
    Record,
    SourceRecord,
    TermKind,
    normalize_term,
    parse_time,
    record_to_dict,
    utc_now,
)
from logical.store import KnowledgeStore
from logical.validation import ValidationIssue, validate_claim, validate_constraint


@dataclass
class AddResult:
    accepted: list[ClaimRecord] = field(default_factory=list)
    quarantined: list[ClaimRecord] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    invalid: list[ValidationIssue] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    source_id: str = ""
    unresolved: list[dict[str, str]] = field(default_factory=list)


@dataclass
class AskResult:
    answer: str
    evidence: list[ClaimRecord]
    query: QueryIntent
    freshness: dict[str, str] = field(default_factory=dict)
    sources: list[SourceRecord] = field(default_factory=list)
    reason: str = ""


@dataclass
class CheckResult:
    ok: bool
    message: str


class KnowledgeView:
    def __init__(self, records: list[Record], at: str | None = None) -> None:
        self.at = evaluation_time(at)
        self.sources = source_index(records)
        self.claims = [r for r in records if isinstance(r, ClaimRecord)]
        self.active = [
            c
            for c in self.claims
            if c.status is KnowledgeStatus.ACCEPTED
            and claim_state(c, self.sources, self.at)[0] in {"fresh", "unknown"}
        ]
        self.aliases = [
            r for r in records if isinstance(r, AliasRecord) and self.metadata_active(r)
        ]
        self.constraints = [
            r
            for r in records
            if isinstance(r, ConstraintRecord) and self.metadata_active(r)
        ]

    def metadata_active(self, record: AliasRecord | ConstraintRecord) -> bool:
        if not record.source_id:
            # Old constraints already affected reasoning; old aliases never did.
            return isinstance(record, ConstraintRecord)
        source = self.sources.get(record.source_id)
        return source is not None and source_state(source, self.at)[0] in {
            "fresh",
            "unknown",
        }

    def context(self) -> dict[str, Any]:
        aliases = alias_index(self.aliases)
        return {
            "terms": {
                term: kind.value
                for term, kind in sorted(term_kinds(self.active).items())
            },
            "aliases": aliases,
            "claims": [
                {"s": c.s, "p": c.p, "o": c.o, "polarity": c.polarity, "scope": c.scope}
                for c in self.active
            ],
        }


def add_knowledge(
    text: str,
    store: KnowledgeStore | None = None,
    extractor: OpenAIExtractor | None = None,
    interactive: bool | None = None,
    *,
    source_ref: str = "",
    observed_at: str | None = None,
    ttl_days: float = 30,
    replaces: str | None = None,
    file_path: str = "",
) -> AddResult:
    if not text.strip():
        raise ValueError("source text must not be empty")
    if not math.isfinite(ttl_days) or not 0 <= ttl_days <= 36500:
        raise ValueError("ttl_days must be between 0 and 36500")
    store = store or KnowledgeStore()
    revision = store.revision()
    records = store.load_records()
    sources = source_index(records)
    previous = sources.get(replaces or "")
    if replaces and (previous is None or previous.superseded_by):
        raise ValueError(
            "update requires an existing source that has not already been superseded"
        )
    observed = parse_time(observed_at or utc_now())
    if observed > evaluation_time():
        raise ValueError("observed_at cannot be in the future")
    if previous and observed < parse_time(previous.observed_at):
        raise ValueError("an update cannot predate the source it replaces")
    source = SourceRecord(
        text=text,
        reference=source_ref or (previous.reference if previous else ""),
        file_path=file_path,
        observed_at=observed.isoformat(),
        review_after=(observed + timedelta(days=ttl_days)).isoformat(),
        supersedes=replaces or "",
    )
    if not replaces:
        for existing in sources.values():
            if (
                not existing.superseded_by
                and existing.content_hash == source.content_hash
                and existing.reference == source.reference
                and existing.file_path == source.file_path
            ):
                # Retrying ingestion must not extend the life of old evidence.
                claims = [
                    c
                    for c in records
                    if isinstance(c, ClaimRecord)
                    and any(e.source_id == existing.id for e in c.evidence)
                ]
                return AddResult(
                    source_id=existing.id,
                    duplicates=[
                        c.id for c in claims if c.status is KnowledgeStatus.ACCEPTED
                    ],
                    quarantined=[
                        c for c in claims if c.status is KnowledgeStatus.QUARANTINED
                    ],
                    unresolved=existing.unresolved,
                )
            if not existing.superseded_by and (
                (source.reference and existing.reference == source.reference)
                or (source.file_path and existing.file_path == source.file_path)
            ):
                raise ValueError(
                    f"Source already exists with different contents; use logical update {existing.id}"
                )
    extractor = extractor or OpenAIExtractor()
    source.model = getattr(extractor, "model", type(extractor).__name__)
    interactive = sys.stdin.isatty() if interactive is None else interactive
    context_method = getattr(extractor, "extract_knowledge_with_context", None)
    context = KnowledgeView(records).context()
    extraction = (
        context_method(text, context)
        if context_method
        else extractor.extract_knowledge(text)
    )
    if not (
        extraction.claims
        or extraction.aliases
        or extraction.constraints
        or extraction.unresolved
    ):
        extraction.unresolved.append(
            {"text": text, "reason": "source produced no supported assertions"}
        )
    source.resolutions = extraction.resolutions
    source.unresolved = list(extraction.unresolved)
    result = add_extraction(
        extraction,
        store,
        interactive,
        source=source,
        expected_revision=revision,
        expected_context=context,
    )
    rebuild_world(store)
    return result


def add_extraction(
    extraction: ExtractionResult,
    store: KnowledgeStore,
    interactive: bool = False,
    *,
    source: SourceRecord | None = None,
    expected_revision: str | None = None,
    expected_context: dict[str, Any] | None = None,
) -> AddResult:
    result = AddResult(
        source_id=source.id if source else "", unresolved=list(extraction.unresolved)
    )
    with store.transaction() as records:
        if expected_revision is not None and store.revision() != expected_revision:
            raise ValueError(
                "Knowledge changed during translation; retry against the new context"
            )
        if (
            expected_context is not None
            and KnowledgeView(records).context() != expected_context
        ):
            raise ValueError(
                "Evidence freshness changed during translation; retry against the new context"
            )
        known_ids = {
            r.id for r in records if isinstance(r, (ClaimRecord, SourceRecord))
        }
        incoming_ids = [c.id for c in extraction.claims] + (
            [source.id] if source else []
        )
        if len(incoming_ids) != len(set(incoming_ids)) or known_ids.intersection(
            incoming_ids
        ):
            raise ValueError("duplicate record IDs; no changes committed")
        if source:
            if source.supersedes:
                previous = source_index(records).get(source.supersedes)
                if previous is None or previous.superseded_by:
                    raise ValueError(
                        "The source to update is missing or already superseded"
                    )
                previous.superseded_by = source.id
                previous.superseded_at = source.observed_at
            records.append(source)
        view = KnowledgeView(records)
        existing = list(view.active)
        constraints = list(view.constraints)
        if inconsistencies(infer(existing), constraints):
            raise ValueError(
                "Existing active knowledge is inconsistent; run logical check before adding claims"
            )
        aliases = alias_index(view.aliases)
        metadata_issues: list[ValidationIssue] = []
        pending_aliases = []
        occupied = {t for c in existing for t in (c.s, c.o)}
        for alias in extraction.aliases:
            if source:
                alias.source_id = source.id
                alias.evidence = alias.evidence or source.text
                if alias.evidence not in source.text:
                    metadata_issues.append(
                        ValidationIssue(
                            "unsupported_alias",
                            source.id,
                            "alias evidence is not in the source",
                        )
                    )
            if alias.alias in occupied and canonical(alias.alias, aliases) != canonical(
                alias.canonical, aliases
            ):
                metadata_issues.append(
                    ValidationIssue(
                        "identity_collision",
                        "",
                        f"{alias.alias} is already a distinct known term; cannot silently merge identities",
                    )
                )
            pending_aliases.append(alias)
        try:
            proposed_aliases = alias_index(view.aliases + pending_aliases)
        except ValueError as exc:
            metadata_issues.append(ValidationIssue("ambiguous_alias", "", str(exc)))
            proposed_aliases = aliases
        targets = occupied | {t for c in extraction.claims for t in (c.s, c.o)}
        local_targets: dict[str, set[str]] = {}
        for resolution in extraction.resolutions:
            mention = resolution["mention"]
            quote = resolution["evidence"]
            target = normalize_term(resolution["canonical"])
            if (
                not source
                or not quote
                or quote not in source.text
                or mention.casefold() not in quote.casefold()
                or target in PRONOUNS
                or canonical(target, proposed_aliases)
                not in {canonical(t, proposed_aliases) for t in targets}
            ):
                metadata_issues.append(
                    ValidationIssue(
                        "unsupported_resolution",
                        source.id if source else "",
                        f"cannot ground resolution of {mention}",
                    )
                )
            else:
                local_targets.setdefault(normalize_term(mention), set()).add(
                    canonical(target, proposed_aliases)
                )
        result.invalid.extend(metadata_issues)
        if not metadata_issues:
            aliases = proposed_aliases
            records.extend(a for a in pending_aliases if a.alias != a.canonical)
        else:
            result.unresolved.extend(
                {"text": source.text if source else "", "reason": issue.message}
                for issue in metadata_issues
            )
        # Repeated pronouns can denote different objects in different sentences.
        # Only a unique mapping can repair an unresolved term; otherwise the model
        # must already have supplied canonical terms for each individual claim.
        local_names = (
            {
                mention: next(iter(values))
                for mention, values in local_targets.items()
                if len(values) == 1
            }
            if not metadata_issues
            else {}
        )
        for constraint in extraction.constraints:
            constraint.s = canonical(
                local_names.get(constraint.s, constraint.s), aliases
            )
            issues = validate_constraint(constraint)
            if source:
                constraint.source_id = source.id
                constraint.evidence = constraint.evidence or source.text
                if constraint.evidence not in source.text:
                    issues.append(
                        ValidationIssue(
                            "unsupported_constraint",
                            source.id,
                            "constraint evidence is not in the source",
                        )
                    )
            if term_kinds(existing).get(constraint.s) is TermKind.CATEGORY:
                issues.append(
                    ValidationIssue(
                        "category_error",
                        "",
                        "functional_for_subject needs an object, not a category",
                    )
                )
            if (
                not issues
                and view.metadata_active(constraint)
                and inconsistencies(infer(existing), constraints + [constraint])
            ):
                issues.append(
                    ValidationIssue(
                        "conflicting_constraint",
                        "",
                        f"new constraint contradicts existing facts for {constraint.s} {constraint.p}",
                    )
                )
            if issues:
                result.invalid.extend(issues)
            elif not metadata_issues:
                records.append(constraint)
                if view.metadata_active(constraint):
                    constraints.append(constraint)
        for claim in extraction.claims:
            if claim.s_kind is TermKind.OBJECT:
                claim.s = local_names.get(claim.s, claim.s)
            if claim.o_kind is TermKind.OBJECT:
                claim.o = local_names.get(claim.o, claim.o)
            claim.s = canonical(claim.s, aliases)
            claim.o = canonical(claim.o, aliases)
            if source:
                if not claim.evidence:
                    claim.evidence = [
                        Evidence(source.id, claim.source_text or source.text)
                    ]
                for evidence in claim.evidence:
                    evidence.source_id = source.id
            issues = validate_claim(claim) + metadata_issues
            if source:
                if any(
                    not e.quote.strip() or e.quote not in source.text
                    for e in claim.evidence
                ):
                    issues.append(
                        ValidationIssue(
                            "unsupported_evidence",
                            claim.id,
                            "claim quote is not an exact source excerpt",
                        )
                    )
                if claim.confidence < 0.8:
                    issues.append(
                        ValidationIssue(
                            "uncertain_translation",
                            claim.id,
                            "translation confidence is below 0.8",
                        )
                    )
            try:
                term_kinds(existing + [claim])
            except ValueError as exc:
                issues.append(ValidationIssue("category_error", claim.id, str(exc)))
            if any(
                c.s == claim.s and claim.s_kind is TermKind.CATEGORY
                for c in constraints
            ):
                issues.append(
                    ValidationIssue(
                        "category_error",
                        claim.id,
                        "a category cannot be the subject of a functional_for_subject constraint",
                    )
                )
            if issues:
                _quarantine(claim, [i.message for i in issues], result)
                result.invalid.extend(i for i in issues if i not in result.invalid)
                records.append(claim)
                if source:
                    claim.source_text = ""
                continue
            if claim.status is KnowledgeStatus.QUARANTINED:
                _quarantine(claim, ["provided as quarantined"], result)
            candidate_is_active = (
                claim.status is KnowledgeStatus.ACCEPTED
                and claim_state(claim, view.sources, view.at)[0] in {"fresh", "unknown"}
            )
            claim_conflicts = (
                find_conflicts(claim, existing, constraints)
                if candidate_is_active
                else []
            )
            logical_issues = (
                inconsistencies(infer(existing + [claim]), constraints)
                if candidate_is_active
                else []
            )
            if logical_issues and not claim_conflicts:
                claim_conflicts = [
                    Conflict("inferred_contradiction", claim.id, other, message)
                    for message, ids in logical_issues
                    for other in sorted(ids - {claim.id})
                ]
                if not claim_conflicts:
                    issues = [
                        ValidationIssue("inconsistent_claim", claim.id, m)
                        for m, _ in logical_issues
                    ]
                    result.invalid.extend(issues)
                    _quarantine(claim, [i.message for i in issues], result)
            if claim_conflicts:
                result.conflicts.extend(claim_conflicts)
                if _conflict_decision(claim, claim_conflicts, interactive) == "replace":
                    replaced_ids = {c.existing_claim_id for c in claim_conflicts}
                    for record in records:
                        if (
                            isinstance(record, ClaimRecord)
                            and record.id in replaced_ids
                        ):
                            record.status = KnowledgeStatus.QUARANTINED
                            record.issues.append(f"replaced by {claim.id}")
                    existing = [c for c in existing if c.id not in replaced_ids]
                    result.accepted = [
                        c for c in result.accepted if c.id not in replaced_ids
                    ]
                    if inconsistencies(infer(existing + [claim]), constraints):
                        raise ValueError(
                            "Replacement would leave inconsistent knowledge; no changes committed"
                        )
                else:
                    _quarantine(claim, [c.message for c in claim_conflicts], result)
            if claim.status is KnowledgeStatus.ACCEPTED:
                duplicate = next(
                    (
                        c
                        for c in records
                        if isinstance(c, ClaimRecord)
                        and c.status is KnowledgeStatus.ACCEPTED
                        and c.key == claim.key
                        and c.s_kind == claim.s_kind
                        and c.o_kind == claim.o_kind
                    ),
                    None,
                )
                if duplicate:
                    _merge_evidence(duplicate, claim, records)
                    result.duplicates.append(duplicate.id)
                    if candidate_is_active and duplicate not in existing:
                        existing.append(duplicate)
                    continue
                result.accepted.append(claim)
                if candidate_is_active:
                    existing.append(claim)
            records.append(claim)
            if source:
                claim.source_text = ""
        if source:
            source.unresolved = result.unresolved
            if source.supersedes and (
                result.invalid
                or result.quarantined
                or result.unresolved
                or not (
                    extraction.claims or extraction.constraints or extraction.aliases
                )
            ):
                raise ValueError(
                    "Update was not fully supported and consistent; previous source preserved. "
                    + "; ".join(
                        [i.message for i in result.invalid]
                        + [u["reason"] for u in result.unresolved]
                        + [c.message for c in result.conflicts]
                    )
                )
    return result


def _merge_evidence(
    existing: ClaimRecord, candidate: ClaimRecord, records: list[Record]
) -> None:
    for claim in (existing, candidate):
        if not claim.evidence and claim.source_text:
            source = SourceRecord(text=claim.source_text, observed_at=claim.created_at)
            records.append(source)
            claim.evidence.append(Evidence(source.id, claim.source_text))
            claim.source_text = ""
    for evidence in candidate.evidence:
        if evidence not in existing.evidence:
            existing.evidence.append(evidence)


def _quarantine(claim: ClaimRecord, reasons: list[str], result: AddResult) -> None:
    claim.status = KnowledgeStatus.QUARANTINED
    claim.issues.extend(reasons)
    if claim not in result.quarantined:
        result.quarantined.append(claim)


def ask_knowledge(
    text: str,
    store: KnowledgeStore | None = None,
    extractor: OpenAIExtractor | None = None,
) -> AskResult:
    store = store or KnowledgeStore()
    extractor = extractor or OpenAIExtractor()
    view = KnowledgeView(store.load_records())
    context_method = getattr(extractor, "extract_query_with_context", None)
    query = (
        context_method(text, view.context())
        if context_method
        else extractor.extract_query(text)
    )
    return ask_query(query, store)


def ask_query(
    query: QueryIntent, store: KnowledgeStore, *, at: str | None = None
) -> AskResult:
    view = KnowledgeView(store.load_records(), at)
    aliases = alias_index(view.aliases)
    query = QueryIntent(
        canonical(query.s, aliases),
        query.p,
        canonical(query.o, aliases),
        query.polarity,
        query.unresolved,
    )
    if (
        query.unresolved
        or query.s in PRONOUNS
        or query.o in PRONOUNS
        or "unknown" in (query.s, query.p, query.o)
    ):
        return AskResult(
            "unknown",
            [],
            query,
            reason=query.unresolved or "unresolved query reference",
        )
    world = infer(view.active)
    answer, ids = world.answer(query)
    problems = inconsistencies(world, view.constraints)
    consistency_reason = ""
    if problems and answer != "both":
        # Time can activate previously future evidence. Never give an unqualified
        # answer from a snapshot that now violates an integrity constraint.
        answer = "unknown"
        ids = frozenset().union(*(support for _, support in problems))
        consistency_reason = "active knowledge is inconsistent: " + "; ".join(
            message for message, _ in problems
        )
    if answer in {"true", "false"}:
        fresh = [
            c
            for c in view.active
            if claim_state(c, view.sources, view.at)[0] == "fresh"
        ]
        fresh_answer, fresh_ids = infer(fresh).answer(query)
        if fresh_answer == answer:
            ids = fresh_ids
    evidence = [c for c in view.active if c.id in ids]
    evidence_sources = {e.source_id for c in evidence for e in c.evidence}
    return AskResult(
        answer,
        evidence,
        query,
        freshness={c.id: claim_state(c, view.sources, view.at)[0] for c in evidence},
        sources=[s for s in view.sources.values() if s.id in evidence_sources],
        reason=consistency_reason or "no current supporting or opposing proof"
        if answer == "unknown"
        else "entailed from accepted evidence; source accuracy is not independently verified",
    )


def check_knowledge(store: KnowledgeStore | None = None) -> CheckResult:
    store = store or KnowledgeStore()
    try:
        records = store.load_records()
        view = KnowledgeView(records)
        problems = [i.message for c in view.active for i in validate_claim(c)]
        term_kinds(view.active)
        alias_index(view.aliases)
        ids = [r.id for r in records if isinstance(r, (ClaimRecord, SourceRecord))]
        if len(ids) != len(set(ids)):
            problems.append("duplicate record IDs")
        for claim in view.claims:
            if claim.status is KnowledgeStatus.ACCEPTED:
                for evidence in claim.evidence:
                    source = view.sources.get(evidence.source_id)
                    if (
                        not source
                        or not evidence.quote
                        or evidence.quote not in source.text
                    ):
                        problems.append(f"unsupported provenance for {claim.id}")
        for constraint in view.constraints:
            problems.extend(i.message for i in validate_constraint(constraint))
        for record in records:
            if isinstance(record, (AliasRecord, ConstraintRecord)) and record.source_id:
                source = view.sources.get(record.source_id)
                if (
                    not source
                    or not record.evidence
                    or record.evidence not in source.text
                ):
                    problems.append(f"unsupported provenance for {record.type.value}")
        for source in view.sources.values():
            if source.superseded_by:
                replacement = view.sources.get(source.superseded_by)
                if (
                    not replacement
                    or replacement.supersedes != source.id
                    or source.superseded_at != replacement.observed_at
                ):
                    problems.append(f"broken source replacement link for {source.id}")
            if source.supersedes:
                previous = view.sources.get(source.supersedes)
                if not previous or previous.superseded_by != source.id:
                    problems.append(f"broken source history for {source.id}")
        problems.extend(
            message
            for message, _ in inconsistencies(infer(view.active), view.constraints)
        )
        if problems:
            return CheckResult(False, "\n".join(problems))
        world_path = store.write_world(project_world(view.active, view.constraints))
        result = validate_with_swipl(world_path)
        return CheckResult(result.ok, result.message)
    except (ValueError, TypeError, KeyError) as exc:
        return CheckResult(False, str(exc))


def export_prolog(store: KnowledgeStore | None = None) -> str:
    view = KnowledgeView((store or KnowledgeStore()).load_records())
    return project_world(view.active, view.constraints)


def rebuild_world(store: KnowledgeStore) -> str:
    return str(store.write_world(export_prolog(store)))


def freshness_report(
    store: KnowledgeStore, *, at: str | None = None
) -> list[dict[str, Any]]:
    view = KnowledgeView(store.load_records(), at)
    result = []
    for claim in view.claims:
        if claim.status is KnowledgeStatus.ACCEPTED:
            state, reasons = claim_state(claim, view.sources, view.at)
            result.append(
                {
                    "id": claim.id,
                    "record_type": "claim",
                    "s": claim.s,
                    "p": claim.p,
                    "o": claim.o,
                    "freshness": state,
                    "reasons": reasons,
                }
            )
    for source in view.sources.values():
        state, reason = source_state(source, view.at)
        result.append(
            {
                "id": source.id,
                "record_type": "source",
                "s": source.reference or source.id,
                "p": "source",
                "o": source.id,
                "freshness": state,
                "reasons": [reason],
            }
        )
    return result


def compress_knowledge(store: KnowledgeStore) -> dict[str, Any]:
    records = store.load_records()
    view = KnowledgeView(records)
    problems = inconsistencies(infer(view.active), view.constraints)
    if problems:
        raise ValueError(
            "Cannot compress inconsistent knowledge: "
            + "; ".join(m for m, _ in problems)
        )
    basis, entailed = compact_basis(view.active)
    supports = sum(max(1, len(c.evidence)) for c in view.active)
    return {
        "schema_version": 1,
        "basis": [
            {
                "id": c.id,
                "s": c.s,
                "p": c.p,
                "o": c.o,
                "polarity": c.polarity,
                "scope": c.scope,
                "s_kind": c.s_kind.value,
                "o_kind": c.o_kind.value,
            }
            for c in basis
        ],
        "entailed": entailed,
        "entailed_claims": {
            c.id: {
                "s": c.s,
                "p": c.p,
                "o": c.o,
                "polarity": c.polarity,
                "s_kind": c.s_kind.value,
                "o_kind": c.o_kind.value,
            }
            for c in view.active
            if c.id in entailed
        },
        "provenance": {
            c.id: {
                "evidence": [asdict(e) for e in c.evidence],
                "legacy_source_text": c.source_text,
            }
            for c in view.active
        },
        "sources": [record_to_dict(s) for s in view.sources.values()],
        "aliases": [record_to_dict(a) for a in view.aliases],
        "constraints": [record_to_dict(c) for c in view.constraints],
        "stats": {
            "evidence_assertions": supports,
            "active_claims": len(view.active),
            "basis_claims": len(basis),
            "entailed_removed": len(entailed),
            "derived_facts": len(infer(view.active).proofs),
            "assertions_per_basis_claim": supports / len(basis) if basis else 0,
        },
    }


def _conflict_decision(
    claim: ClaimRecord, conflicts: list[Conflict], interactive: bool
) -> str:
    if not interactive:
        return "quarantine"
    print(f"Conflict for {claim.s} {claim.p} {claim.o}:")
    for conflict in conflicts:
        print(f"- {conflict.message} (premise {conflict.existing_claim_id})")
    choice = input(
        "Choose [k]eep existing, [r]eplace conflicting premises, [q]uarantine new: "
    )
    return "replace" if choice.strip().lower().startswith("r") else "quarantine"
