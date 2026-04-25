from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

from logical.schema import (
    AliasRecord,
    ClaimRecord,
    ConstraintRecord,
    ExtractionResult,
    QueryIntent,
)


DEFAULT_MODEL = "gpt-5.5"

load_dotenv(find_dotenv())


EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["claims", "aliases", "constraints"],
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["s", "p", "o", "polarity", "confidence"],
                "properties": {
                    "s": {"type": "string"},
                    "p": {"type": "string"},
                    "o": {"type": "string"},
                    "polarity": {"type": "boolean"},
                    "confidence": {"type": "number"},
                },
            },
        },
        "aliases": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["canonical", "alias"],
                "properties": {
                    "canonical": {"type": "string"},
                    "alias": {"type": "string"},
                },
            },
        },
        "constraints": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["kind", "s", "p"],
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": ["functional_for_subject"],
                    },
                    "s": {"type": "string"},
                    "p": {"type": "string"},
                },
            },
        },
    },
}


QUERY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["s", "p", "o", "polarity"],
    "properties": {
        "s": {"type": "string"},
        "p": {"type": "string"},
        "o": {"type": "string"},
        "polarity": {"type": "boolean"},
    },
}


class OpenAIExtractor:
    def __init__(self, model: str | None = None, client: OpenAI | None = None) -> None:
        self.model = model or os.getenv("OPEN_AI_MODEL_TYPE") or DEFAULT_MODEL
        self.client = client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def extract_knowledge(self, text: str) -> ExtractionResult:
        system = (
            "Extract RDF-like logical knowledge. Return only structured JSON. "
            "Use concise canonical terms. Represent unary facts as s=subject, "
            "p=predicate, o=true. For functional constraints such as one color, "
            "emit kind=functional_for_subject for the subject and predicate."
        )
        response = self._responses_json(
            system,
            text,
            "logical_knowledge",
            EXTRACTION_SCHEMA,
        )
        return parse_extraction_response(response, text)

    def extract_query(self, text: str) -> QueryIntent:
        system = (
            "Convert the user question into one RDF-like triple query. Return only "
            "structured JSON with s, p, o, and polarity."
        )
        response = self._responses_json(system, text, "logical_query", QUERY_SCHEMA)
        return parse_query_response(response)

    def _responses_json(
        self, system: str, user: str, schema_name: str, schema: dict[str, Any]
    ) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                }
            },
        )
        return _response_text(response)


def parse_extraction_response(
    raw: str | dict[str, Any], source_text: str
) -> ExtractionResult:
    payload = _loads_json(raw)
    claims = [
        ClaimRecord(
            s=item.get("s", ""),
            p=item.get("p", ""),
            o=item.get("o", ""),
            polarity=bool(item.get("polarity", True)),
            confidence=float(item.get("confidence", 1.0)),
            source_text=source_text,
        )
        for item in payload.get("claims", [])
    ]
    aliases = [
        AliasRecord(
            canonical=item.get("canonical", ""),
            alias=item.get("alias", ""),
        )
        for item in payload.get("aliases", [])
    ]
    constraints = [
        ConstraintRecord(
            kind=item.get("kind", ""),
            s=item.get("s", ""),
            p=item.get("p", ""),
            source_claim_id="",
        )
        for item in payload.get("constraints", [])
    ]
    return ExtractionResult(claims=claims, aliases=aliases, constraints=constraints)


def parse_query_response(raw: str | dict[str, Any]) -> QueryIntent:
    payload = _loads_json(raw)
    return QueryIntent(
        s=payload.get("s", ""),
        p=payload.get("p", ""),
        o=payload.get("o", ""),
        polarity=bool(payload.get("polarity", True)),
    )


def _loads_json(raw: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    text = raw.strip()
    fenced = re.match(r"```(?:json)?\s*(.*?)\s*```$", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1)
    return json.loads(text)


def _response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text
    if isinstance(response, dict) and response.get("output_text"):
        return response["output_text"]
    output = getattr(response, "output", None) or (
        response.get("output") if isinstance(response, dict) else None
    )
    if output:
        first = output[0]
        content = getattr(first, "content", None) or first.get("content")
        text_part = content[0]
        return getattr(text_part, "text", None) or text_part.get("text")
    raise ValueError("Could not read text from OpenAI response")
