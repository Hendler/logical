"""Finite, monotone entailment with premise IDs; no closed-world negation."""

from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict, deque

from logical.schema import ClaimRecord, ConstraintRecord, KnowledgeStatus, QueryIntent

Fact = tuple[str, str, str, bool]
MAX_FACTS = 50_000


@dataclass
class World:
    proofs: dict[Fact, frozenset[str]]

    def answer(self, query: QueryIntent) -> tuple[str, frozenset[str]]:
        positive = self.proofs.get((query.s, query.p, query.o, query.polarity))
        negative = self.proofs.get((query.s, query.p, query.o, not query.polarity))
        if positive is not None and negative is not None:
            return "both", positive | negative
        if positive is not None:
            return "true", positive
        if negative is not None:
            return "false", negative
        return "unknown", frozenset()


def infer(claims: list[ClaimRecord]) -> World:
    proofs: dict[Fact, frozenset[str]] = {}
    claims = [c for c in claims if c.status is KnowledgeStatus.ACCEPTED]
    rules: dict[str, list[ClaimRecord]] = defaultdict(list)
    for claim in claims:
        if claim.scope == "all":
            rules[claim.s].append(claim)
    pending: deque[Fact] = deque()
    parents: dict[str, list[tuple[str, frozenset[str]]]] = defaultdict(list)
    children: dict[str, list[tuple[str, frozenset[str]]]] = defaultdict(list)
    members: dict[str, list[tuple[str, frozenset[str]]]] = defaultdict(list)

    def add(fact: Fact, support: frozenset[str]) -> bool:
        if fact in proofs:
            return False
        if len(proofs) >= MAX_FACTS:
            raise ValueError(
                f"Inference exceeds the {MAX_FACTS} fact limit; split this knowledgebase"
            )
        proofs[fact] = support
        pending.append(fact)
        return True

    for c in claims:
        if c.scope == "fact":
            add((c.s, c.p, c.o, c.polarity), frozenset({c.id}))
    while pending:
        fact = pending.popleft()
        s, p, o, polarity = fact
        support = proofs[fact]
        if not polarity:
            continue
        if p == "subclass_of":
            parents[s].append((o, support))
            children[o].append((s, support))
            for ancestor, ids in parents[o]:
                add((s, p, ancestor, True), support | ids)
            for descendant, ids in children[s]:
                add((descendant, p, o, True), support | ids)
            for member, ids in members[s]:
                add((member, "instance_of", o, True), support | ids)
        elif p == "instance_of":
            members[o].append((s, support))
            for ancestor, ids in parents[o]:
                add((s, p, ancestor, True), support | ids)
            for rule in rules[o]:
                add((s, rule.p, rule.o, rule.polarity), support | {rule.id})
    return World(proofs)


def inconsistencies(
    world: World, constraints: list[ConstraintRecord]
) -> list[tuple[str, frozenset[str]]]:
    issues: list[tuple[str, frozenset[str]]] = []
    for (s, p, o, polarity), ids in world.proofs.items():
        if polarity and (s, p, o, False) in world.proofs:
            issues.append(
                (f"contradiction: {s} {p} {o}", ids | world.proofs[(s, p, o, False)])
            )
    for constraint in constraints:
        matches = [
            (f, ids)
            for f, ids in world.proofs.items()
            if f[:2] == (constraint.s, constraint.p) and f[3]
        ]
        if len(matches) > 1:
            issues.append(
                (
                    f"functional conflict: {constraint.s} {constraint.p}",
                    frozenset().union(*(ids for _, ids in matches)),
                )
            )
    return issues


def compact_basis(
    claims: list[ClaimRecord],
) -> tuple[list[ClaimRecord], dict[str, list[str]]]:
    """Greedy irredundant basis, verified against the final basis. Never invent rules."""
    basis = list(claims)
    removed: list[ClaimRecord] = []
    for claim in sorted(claims, key=lambda c: c.key):
        if claim.scope != "fact":
            continue
        candidate = [c for c in basis if c.id != claim.id]
        if (claim.s, claim.p, claim.o, claim.polarity) in infer(candidate).proofs:
            basis = candidate
            removed.append(claim)
    world = infer(basis)
    proofs = {c.id: sorted(world.proofs[(c.s, c.p, c.o, c.polarity)]) for c in removed}
    return basis, proofs
