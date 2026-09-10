"""Only explicit, unambiguous aliases are global. Pronouns stay in source context."""

from __future__ import annotations

from logical.schema import AliasRecord, ClaimRecord, TermKind, normalize_term

PRONOUNS = {
    "he",
    "she",
    "it",
    "they",
    "him",
    "her",
    "them",
    "his",
    "hers",
    "its",
    "their",
    "theirs",
    "this",
    "that",
    "these",
    "those",
    "we",
    "us",
    "i",
    "you",
    "someone",
    "something",
}


def alias_index(aliases: list[AliasRecord]) -> dict[str, str]:
    targets: dict[str, set[str]] = {}
    for alias in aliases:
        if "unknown" in {alias.alias, alias.canonical}:
            raise ValueError("Alias is missing a canonical term or name")
        if alias.alias == alias.canonical:
            continue
        if alias.alias in PRONOUNS or alias.canonical in PRONOUNS:
            raise ValueError(f"Pronoun {alias.alias} cannot be a global alias")
        targets.setdefault(alias.alias, set()).add(alias.canonical)
    if any(len(values) > 1 for values in targets.values()):
        ambiguous = sorted(key for key, values in targets.items() if len(values) > 1)
        raise ValueError(f"Ambiguous aliases: {', '.join(ambiguous)}")
    direct = {key: next(iter(values)) for key, values in targets.items()}
    resolved: dict[str, str] = {}
    for name in direct:
        seen = {name}
        target = direct[name]
        while target in direct:
            if target in seen:
                raise ValueError(f"Alias cycle involving {name}")
            seen.add(target)
            target = direct[target]
        resolved[name] = target
    return resolved


def canonical(term: str, aliases: dict[str, str]) -> str:
    term = normalize_term(term)
    return aliases.get(term, term)


def term_kinds(claims: list[ClaimRecord]) -> dict[str, TermKind]:
    kinds: dict[str, TermKind] = {}
    for claim in claims:
        for term, kind in ((claim.s, claim.s_kind), (claim.o, claim.o_kind)):
            if kind is TermKind.UNKNOWN:
                continue
            if term in kinds and kinds[term] is not kind:
                raise ValueError(f"{term} is both {kinds[term].value} and {kind.value}")
            kinds[term] = kind
    return kinds
