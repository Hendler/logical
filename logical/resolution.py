"""Only explicit, unambiguous aliases are global. Pronouns stay in source context."""

from __future__ import annotations

import re

from logical.schema import (
    AliasDependency,
    AliasRecord,
    ClaimRecord,
    Evidence,
    SourceRecord,
    TermKind,
    normalize_term,
)

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


def identity_path(term: str, aliases: list[AliasRecord]) -> list[AliasDependency]:
    """Keep each identity premise, including alternative sources for the same hop."""
    alias_index(aliases)  # Reject ambiguity and cycles before following a path.
    paths: list[AliasDependency] = []
    term = normalize_term(term)
    while True:
        matches = [a for a in aliases if a.alias == term and a.canonical != term]
        if not matches:
            return paths
        target = matches[0].canonical
        paths.append(
            AliasDependency(
                term, target, sorted({a.source_id for a in matches if a.source_id})
            )
        )
        term = target


def mentioned_aliases(text: str, target: str, aliases: list[AliasRecord]) -> list[str]:
    """Conservative fallback for old extractors without explicit surface bindings."""
    passage = "_" + normalize_term(text) + "_"
    return [
        name
        for name, resolved in alias_index(aliases).items()
        if resolved == target and "_" + name + "_" in passage
    ]


def bind_identity(
    claim: ClaimRecord,
    evidence: Evidence,
    source: SourceRecord | None,
    aliases: list[AliasRecord],
) -> None:
    """Verify an explicit mention binding; never rewrite an unrelated canonical ID."""
    index = alias_index(aliases)
    dependencies: list[AliasDependency] = []
    for side in ("s", "o"):
        term = getattr(claim, side)
        binding = getattr(evidence, side + "_ref")
        reference = term
        if binding is None:
            for mention in mentioned_aliases(
                evidence.quote, canonical(term, index), aliases
            ):
                for dependency in identity_path(mention, aliases):
                    if dependency not in dependencies:
                        dependencies.append(dependency)
        if binding is not None:
            occurrences = len(
                re.findall(
                    r"(?<!\w)" + re.escape(binding.mention) + r"(?!\w)", evidence.quote
                )
            )
            if not occurrences:
                raise ValueError("reference mention is not in its claim quote")
            reference = normalize_term(binding.mention)
            if binding.resolution is not None:
                if (
                    source is None
                    or type(binding.resolution) is not int
                    or not 0 <= binding.resolution < len(source.resolutions)
                ):
                    raise ValueError("reference has an invalid resolution index")
                if occurrences != 1:
                    raise ValueError(
                        "reference quote must identify one occurrence of the resolved mention"
                    )
                resolution = source.resolutions[binding.resolution]
                passage = resolution["evidence"]
                if (
                    resolution["mention"] != binding.mention
                    or evidence.quote not in passage
                    or passage not in source.text
                    or source.text.count(passage) != 1
                    or passage.count(evidence.quote) != 1
                ):
                    raise ValueError(
                        "reference is outside its uniquely identified resolution passage"
                    )
                reference = normalize_term(resolution["canonical"])
                if canonical(reference, index) != canonical(term, index):
                    raise ValueError(
                        "reference resolution does not confirm the claim's canonical term"
                    )
                antecedent = resolution.get("antecedent")
                if antecedent is not None:
                    if (
                        not antecedent.strip()
                        or not re.search(
                            r"(?<!\w)" + re.escape(antecedent) + r"(?!\w)", passage
                        )
                        or canonical(antecedent, index) != canonical(term, index)
                    ):
                        raise ValueError(
                            "resolution antecedent does not identify the claim's canonical term"
                        )
                    antecedents = [antecedent]
                else:
                    antecedents = mentioned_aliases(
                        passage, canonical(term, index), aliases
                    )
                for antecedent in antecedents:
                    for dependency in identity_path(antecedent, aliases):
                        if dependency not in dependencies:
                            dependencies.append(dependency)
            elif reference in PRONOUNS:
                raise ValueError("pronoun reference requires a source-local resolution")
            elif canonical(reference, index) != canonical(term, index):
                raise ValueError(
                    "reference alias does not identify the claim's canonical term"
                )
        for dependency in identity_path(reference, aliases) + identity_path(
            term, aliases
        ):
            if dependency not in dependencies:
                dependencies.append(dependency)
    evidence.identity_dependencies = dependencies


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
