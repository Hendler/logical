import json

from logical.openai_client import parse_extraction_response, parse_query_response


def test_parse_structured_extraction_response_normalizes_records():
    payload = {
        "claims": [
            {
                "s": "The Sky",
                "p": "Color",
                "o": "Red",
                "polarity": True,
                "confidence": 0.88,
            }
        ],
        "aliases": [{"canonical": "sky", "alias": "the sky"}],
        "constraints": [{"kind": "functional_for_subject", "s": "sky", "p": "color"}],
    }

    result = parse_extraction_response(json.dumps(payload), "The sky is red.")

    assert result.claims[0].s == "sky"
    assert result.claims[0].p == "color"
    assert result.claims[0].o == "red"
    assert result.claims[0].source_text == "The sky is red."
    assert result.aliases[0].alias == "sky"
    assert result.constraints[0].kind == "functional_for_subject"


def test_parse_query_response_normalizes_intent():
    payload = {"s": "The Sky", "p": "Color", "o": "Red", "polarity": True}

    intent = parse_query_response(json.dumps(payload))

    assert intent.s == "sky"
    assert intent.p == "color"
    assert intent.o == "red"
    assert intent.polarity is True
