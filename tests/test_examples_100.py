from __future__ import annotations

from dataclasses import dataclass

from logical.schema import ClaimRecord, ConstraintRecord, ExtractionResult, QueryIntent
from logical.service import add_knowledge, ask_knowledge, export_prolog
from logical.store import KnowledgeStore


@dataclass(frozen=True)
class ExampleCase:
    text: str
    extraction: ExtractionResult
    expected: str


class ExampleExtractor:
    def __init__(self, examples: list[ExampleCase]):
        self.examples = {example.text: example.extraction for example in examples}

    def extract_knowledge(self, text: str) -> ExtractionResult:
        return self.examples[text]

    def extract_query(self, text: str) -> QueryIntent:
        if text == "is object 0 red?":
            return QueryIntent(s="object_0", p="color", o="red")
        if text == "is invalid 0 observed?":
            return QueryIntent(s="invalid_0", p="observed", o="true")
        if text == "is creature 0 tagged?":
            return QueryIntent(s="creature_0", p="tag", o="tag_0")
        if text == "is sample entity 76 blocked?":
            return QueryIntent(s="sample_entity_76", p="blocked", o="true")
        raise AssertionError(f"Unexpected query: {text}")


def build_100_examples() -> list[ExampleCase]:
    examples: list[ExampleCase] = []
    for index in range(80):
        if index < 6:
            text = f"object {index} is red and can have only one color"
            extraction = ExtractionResult(
                claims=[
                    ClaimRecord(
                        id=f"valid-color-{index}",
                        s=f"object {index}",
                        p="color",
                        o="red",
                        source_text=text,
                    )
                ],
                constraints=[
                    ConstraintRecord(
                        kind="functional_for_subject",
                        s=f"object {index}",
                        p="color",
                        source_claim_id=f"constraint-color-{index}",
                    )
                ],
            )
        elif index < 12:
            text = f"creature {index - 6} has tag {index - 6}"
            extraction = ExtractionResult(
                claims=[
                    ClaimRecord(
                        id=f"valid-creature-{index - 6}",
                        s=f"creature {index - 6}",
                        p="tag",
                        o=f"tag {index - 6}",
                        source_text=text,
                    )
                ]
            )
        elif index < 76:
            text = f"sample entity {index} has property value {index}"
            extraction = ExtractionResult(
                claims=[
                    ClaimRecord(
                        id=f"valid-sample-{index}",
                        s=f"sample entity {index}",
                        p="property",
                        o=f"value {index}",
                        source_text=text,
                    )
                ]
            )
        else:
            text = f"sample entity {index} is not blocked"
            extraction = ExtractionResult(
                claims=[
                    ClaimRecord(
                        id=f"valid-negative-{index}",
                        s=f"sample entity {index}",
                        p="blocked",
                        o="true",
                        polarity=False,
                        source_text=text,
                    )
                ]
            )
        examples.append(ExampleCase(text=text, extraction=extraction, expected="accepted"))

    for index in range(8):
        text = f"invalid example {index} is missing enough logical structure"
        extraction = ExtractionResult(
            claims=[
                ClaimRecord(
                    id=f"invalid-{index}",
                    s="" if index % 2 == 0 else f"invalid {index}",
                    p="observed",
                    o="true",
                    source_text="" if index % 2 else text,
                    confidence=1.2 if index % 3 == 0 else 0.5,
                )
            ]
        )
        examples.append(ExampleCase(text=text, extraction=extraction, expected="invalid"))

    for index in range(6):
        text = f"creature {index} does not have tag {index}"
        extraction = ExtractionResult(
            claims=[
                ClaimRecord(
                    id=f"direct-conflict-{index}",
                    s=f"creature {index}",
                    p="tag",
                    o=f"tag {index}",
                    polarity=False,
                    source_text=text,
                )
            ]
        )
        examples.append(ExampleCase(text=text, extraction=extraction, expected="conflict"))

    for index in range(6):
        text = f"object {index} is blue"
        extraction = ExtractionResult(
            claims=[
                ClaimRecord(
                    id=f"functional-conflict-{index}",
                    s=f"object {index}",
                    p="color",
                    o="blue",
                    source_text=text,
                )
            ]
        )
        examples.append(ExampleCase(text=text, extraction=extraction, expected="conflict"))

    assert len(examples) == 100
    return examples


def test_100_examples_cover_valid_invalid_conflict_and_queries(tmp_path):
    examples = build_100_examples()
    store = KnowledgeStore(tmp_path)
    extractor = ExampleExtractor(examples)
    counts = {"accepted": 0, "invalid": 0, "conflict": 0}

    for example in examples:
        result = add_knowledge(
            example.text,
            store=store,
            extractor=extractor,
            interactive=False,
        )
        if example.expected == "accepted":
            assert len(result.accepted) == 1
            assert not result.quarantined
            counts["accepted"] += 1
        elif example.expected == "invalid":
            assert len(result.quarantined) == 1
            assert result.invalid
            counts["invalid"] += 1
        else:
            assert len(result.quarantined) == 1
            assert result.conflicts
            counts["conflict"] += 1

    assert counts == {"accepted": 80, "invalid": 8, "conflict": 12}
    assert len(store.load_claims()) == 100
    assert len(store.load_claims(status=None)) == 100

    prolog = export_prolog(store)
    assert "triple(object_0,color,red)." in prolog
    assert "triple(object_0,color,blue)." not in prolog
    assert "neg_triple(sample_entity_76,blocked,true)." in prolog
    assert "triple(invalid_0,observed,true)." not in prolog

    assert ask_knowledge("is object 0 red?", store, extractor).answer == "true"
    assert ask_knowledge("is invalid 0 observed?", store, extractor).answer == "unknown"
    assert ask_knowledge("is creature 0 tagged?", store, extractor).answer == "true"
    assert ask_knowledge("is sample entity 76 blocked?", store, extractor).answer == "false"
