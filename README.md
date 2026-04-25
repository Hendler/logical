# logical

A triple-backed logic engine for turning natural language knowledge into
RDF-like claims, projecting accepted claims into Prolog, and asking logical
questions over that generated world.

First developed at the [OpenAI emergency hackathon on 3/5/2023](https://twitter.com/nonmayorpete/status/1632456433102098434).

<img alt="Bertrand Russell" src="./russell.png" />

## Install

```bash
brew install swi-prolog
uv sync --dev
cp .env-example .env
```

Set `OPENAI_API_KEY` in `.env` for commands that call OpenAI. The default model
is `gpt-5.5`.

## Usage

```bash
uv run logical add "the sky is red"
uv run logical add "a sky can only be one color"
uv run logical add "the sky is blue"
uv run logical ask "is the sky red?"
uv run logical check
uv run logical export-prolog
```

`logical add` and `logical ask` require `OPENAI_API_KEY` because they use OpenAI
to extract structured triples or query intent. `logical check` and
`logical export-prolog` operate on the local `.logical/` store and do not need an
API key.

Knowledge is stored in `.logical/knowledge.jsonl`. Prolog is generated into
`.logical/world.pl`; it is a projection, not the source of truth.

Invalid or unsupported logic is quarantined instead of projected into Prolog.
Conflicting claims are also quarantined by default. In an interactive terminal,
`logical add --interactive "..."` lets you choose whether to keep existing
knowledge, replace it, or quarantine the new claim.

## Development

```bash
uv run pytest
```

The tests use fake extractors, so they do not require `OPENAI_API_KEY`. The suite
includes a deterministic 100-example coverage pass for valid knowledge, invalid
logic, conflicts, conflict resolution, Prolog projection, and query behavior.
Tests that require SWI-Prolog skip with a clear message when `swipl` is not on
`PATH`.
