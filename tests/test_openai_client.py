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


from types import SimpleNamespace

import pytest

from logical.openai_client import DEFAULT_MODEL, OpenAIExtractor, _response_text


def structured_payload():
    return {
        "claims": [
            {
                "s": "ada",
                "p": "instance_of",
                "o": "person",
                "s_kind": "object",
                "o_kind": "category",
                "scope": "fact",
                "polarity": True,
                "confidence": 0.99,
                "evidence": "Ada is a person.",
                "valid_from": None,
                "valid_until": None,
            }
        ],
        "aliases": [],
        "constraints": [],
        "resolutions": [],
        "unresolved": [],
    }


class FakeResponses:
    def __init__(self, output):
        self.output = output
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(status="completed", output_text=json.dumps(self.output))


def test_astra_request_uses_context_strict_schema_and_supported_parameters(monkeypatch):
    monkeypatch.delenv("LOGICAL_MODEL", raising=False)
    monkeypatch.delenv("OPEN_AI_MODEL_TYPE", raising=False)
    responses = FakeResponses(structured_payload())
    extractor = OpenAIExtractor(client=SimpleNamespace(responses=responses))
    result = extractor.extract_knowledge_with_context(
        "Ada is a person.", {"terms": {"ada": "object"}}
    )
    call = responses.calls[0]
    assert call["model"] == DEFAULT_MODEL == "gpt-6-astra"
    assert call["reasoning"] == {"effort": "high"}
    assert call["text"]["format"]["strict"] is True
    assert call["store"] is False
    assert "temperature" not in call and "top_p" not in call
    assert json.loads(call["input"][1]["content"])["context"]["terms"] == {
        "ada": "object"
    }
    assert result.claims[0].evidence[0].quote == "Ada is a person."


def test_model_override_precedence_preserves_explicit_choice(monkeypatch):
    client = SimpleNamespace()
    monkeypatch.setenv("OPEN_AI_MODEL_TYPE", "legacy-model")
    monkeypatch.setenv("LOGICAL_MODEL", "configured-model")
    assert OpenAIExtractor(client=client).model == "configured-model"
    assert (
        OpenAIExtractor(model="explicit-model", client=client).model == "explicit-model"
    )
    monkeypatch.delenv("LOGICAL_MODEL")
    assert OpenAIExtractor(client=client).model == "legacy-model"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p["claims"][0].update(polarity="false"),
        lambda p: p["claims"][0].update(confidence=float("nan")),
        lambda p: p["claims"][0].pop("evidence"),
        lambda p: p.pop("unresolved"),
        lambda p: p.update(unexpected="overwrite the world"),
    ],
)
def test_malformed_structured_output_is_rejected_before_ingestion(mutate):
    payload = structured_payload()
    mutate(payload)
    extractor = OpenAIExtractor(
        client=SimpleNamespace(responses=FakeResponses(payload))
    )
    with pytest.raises(ValueError):
        extractor.extract_knowledge("Ada is a person.")


@pytest.mark.parametrize(
    "response",
    [
        {"status": "incomplete", "output_text": '{"claims":[]}'},
        {"status": "failed", "output_text": '{"claims":[]}'},
        {
            "status": "completed",
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "refusal", "refusal": "declined"}],
                }
            ],
        },
        {"status": "completed", "output": []},
    ],
)
def test_partial_refused_and_empty_responses_cannot_be_accepted(response):
    with pytest.raises(ValueError):
        _response_text(response)


def test_response_reader_skips_reasoning_items():
    response = SimpleNamespace(
        status="completed",
        output=[
            SimpleNamespace(type="reasoning", summary=[]),
            SimpleNamespace(
                type="message",
                content=[SimpleNamespace(type="output_text", text='{"claims":[]}')],
            ),
        ],
    )
    assert _response_text(response) == '{"claims":[]}'


def test_query_boolean_strings_are_not_coerced_to_true():
    with pytest.raises(ValueError, match="boolean"):
        parse_query_response(
            {"s": "ada", "p": "breathes", "o": "true", "polarity": "false"}
        )
