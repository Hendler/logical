# logical

Turn source documents into a compact knowledgebase of typed claims, then answer
questions with checkable proofs and citations. GPT-6 Astra translates the text;
a finite logic engine and SWI-Prolog check its logical consequences. Sources,
ambiguous references, conflicting claims, and old versions remain inspectable.

First developed at the [OpenAI emergency hackathon on 3/5/2023](https://twitter.com/nonmayorpete/status/1632456433102098434).

## Install

Python 3.11+ on macOS or Linux:

```bash
brew install swi-prolog                 # Debian/Ubuntu: apt install swi-prolog-nox
uv sync --locked --dev
cp .env-example .env
```

Set `OPENAI_API_KEY` in `.env`. The default translation and query model is
[`gpt-6-astra`](https://developers.openai.com/api/docs/models/gpt-6-astra), using
the Responses API with strict structured outputs and high reasoning effort.
Model precedence: `--model`, `LOGICAL_MODEL`, legacy `OPEN_AI_MODEL_TYPE`, then
Astra. For an existing installation, set `LOGICAL_MODEL=gpt-6-astra` to override
an old `.env` model selection. `LOGICAL_REASONING_EFFORT` is configurable.
Model access errors fail visibly; there is no silent model fallback.

The dependency bounds and `uv.lock` were refreshed against stable PyPI releases
on September 10, 2026: OpenAI SDK 3.13.0, python-dotenv 1.2.3, pytest 9.1.1, and
hatchling 1.32.0. Use `uv lock --upgrade` followed by `uv sync --locked --dev` to
refresh later, and rerun the tests before adopting the new lockfile.

## A complete journey

These are **synthetic premises**, not biographical assertions:

```bash
uv run logical add \
  "Ada Lovelace, also known as Ada, is a person. Every person is a mammal. All mammals breathe. Her home city is London. Ada Lovelace has at most one home city at a time." \
  --source-ref demo:ada --ttl-days 30

uv run logical ask "Does Ada breathe?"
uv run logical query ada breathes true --json
uv run logical check
uv run logical compress > compressed.json
uv run logical inspect
```

The intended translation stores four premises and one constraint. It distinguishes
Ada (an object) from person and mammal (categories), records the alias “Ada,”
and resolves “Her” inside this source. The breathing answer has a three-premise
proof: membership, subclass inclusion, and an explicit universal rule. Model
translation is nondeterministic; inspect its citations and unresolved output.

`add` prints a source ID. Replace that document using its ID and the **complete
replacement text**:

```bash
uv run logical update SOURCE_ID \
  "Ada Lovelace, also known as Ada, is a person. Every person is a mammal. All mammals breathe. Her home city is Paris. Ada Lovelace has at most one home city at a time."

uv run logical stale
uv run logical query ada home_city london
uv run logical query ada home_city paris
```

The old London assertion becomes stale and stops supporting current answers.
Unchanged premises share canonical claims while retaining evidence from both
versions. Other independent, current sources still count. A replacement with
ambiguous references, invalid claims, or contradictions leaves the previous
source intact. Omitted claims lose that source's support only after a successful
update. Plain `add` with changed contents for an existing source reference asks
you to use `update`.

Use `--store-dir PATH` before the command to isolate knowledgebases. Use
`--file notes.txt` instead of inline text to ingest a UTF-8 document; its absolute
path becomes the default citation reference. Changes to or removal of that file
make its evidence stale immediately. Update it with
`logical update SOURCE_ID --file notes.txt`.

`add`, `update`, and `ask` call OpenAI and send the supplied text plus the current
canonical knowledge context. The other commands work offline. Requests disable
provider response storage with `store=False`; the provider's applicable data
policies still govern processing. There is no automatic URL fetching. A
`--source-ref` URL is a citation label for the text you supplied.

## What the logic means

| Representation | Meaning |
| --- | --- |
| `ada instance_of person` | Ada is a particular member of the person category. |
| `person subclass_of mammal` | Every person is a mammal. |
| `mammal breathes true`, `scope=all` | Every mammal breathes. Requires an explicit universal assertion. |
| `mammal widespread true`, `scope=fact` | A statement about the category itself; it does not apply to each mammal. |
| `polarity=false` | Explicit negative evidence, not a missing positive fact. |

Terms have kinds `object`, `category`, or `value`. A term cannot simultaneously
be an object and a category in active knowledge. New model output must declare
these types. Reusing a familiar name alone is insufficient evidence of identity.
Stable, explicit aliases are applied during ingestion and querying; collisions,
cycles, and pronoun aliases are rejected. Source-local coreference resolutions
bind specific quoted mentions to canonical IDs and retain their antecedents.
Resolving “the apple” to a particular fruit cannot rewrite an independent mention
of Apple the company. Repeated pronouns have separate bindings. Unresolved
passages remain in source records for review.

Identity is part of the proof: an assertion about Bob translated to Robert retains
the evidence for Bob = Robert, including alias chains and pronoun antecedents.
This applies to category aliases and constraint subjects too. Expiry or correction
of that identity evidence stops the dependent assertion from supporting current
answers; independent evidence for the same identity can keep it current.

Inference supports subclass transitivity, inherited membership, and explicit
universal properties. It never invents a universal rule from examples, applies
collective properties to individuals, takes a converse or contrapositive, or
uses missing evidence as negation. There are no arbitrary executable rules.
The engine limits closure to 50,000 facts and fails if that limit is exceeded.

Answers are `true`, `false`, `unknown`, or `both` (a contradiction in an externally
modified store). Every positive or negative answer includes its supporting
premise IDs, source quotes, and freshness. Unknown means no current proof in
either direction. Unsupported questions return unknown with a reason. Direct
queries also return unknown for inconsistent type/constraint snapshots; natural
language translation refuses an invalid context. Translation and evaluation use one captured
snapshot, identified by `evaluated_at`; later source or file changes apply to the
next query. Answers cite the identity evidence used by their premises and query.
`check` validates provenance and logical consistency, then independently checks
the generated Prolog. It reports explicitly when SWI-Prolog is unavailable.

Logical acceptance establishes consistency with accepted premises and traceable
source support. **It does not independently establish that a source is true.**
A faithful quotation can still support an incorrect extraction; review important
translations. Hedges, ambiguous quantifiers, disjunctions, and unsupported time
expressions are retained as unresolved instead of being turned into facts.

## Freshness and compression

Freshness is separate from acceptance. Each source records its content hash,
observation time, review deadline, translator model, and replacement history.
The default review interval is 30 days from observation; use `--observed-at`
(a timezone-aware ISO timestamp) and `--ttl-days` for your source policy.
“Fresh” means within that policy, not independently fact-checked or fetched.

Explicit claim validity intervals are also enforced (`valid_until` is exclusive).
Expired, superseded, changed-file, or missing-source evidence cannot support
current inference. A claim stays current if another current source still supports
it. Derived answers are recomputed from eligible premises, so stale dependencies
invalidate their conclusions. `stale` reports claims and sources, including
constraint-only sources. Repeating identical ingestion does not reset deadlines
or call the model; an explicit `update` can record a new observation.

Python callers can pass a timezone-aware `at=` timestamp to `ask_query`,
`check_knowledge`, `export_prolog`, `compress_knowledge`, and `freshness_report`.
These explicit as-of reads use recorded source versions and validity intervals.
They do not compare historical evidence with today's filesystem. Current reads
without `at` check files once when capturing the snapshot. Time-activated type
conflicts fail integrity checks and cannot be exported as verified knowledge.

Identical canonical claims are stored once with multiple evidence entries.
`compress` exports a deterministic, irredundant basis: it removes a ground claim
only when the remaining premises entail it, and includes a proof using the final
basis. It preserves source and provenance sidecars and reports evidence counts,
basis size, and derived fact counts. The canonical store is untouched. This is a
snapshot of current knowledge; regenerate it after updates or expiry. It is not
a guarantee of a globally shortest encoding, a token compression ratio, or a
license to generalize away exceptions.

## Storage and compatibility

`.logical/knowledge.jsonl` is the source of truth; `.logical/world.pl` is generated.
Writes use a process lock, an fsynced temporary file, and atomic replacement.
Translation runs outside the lock; changed knowledge or context prevents a stale
translation from committing. A failed update cannot leave a partial replacement.
If the canonical transaction succeeds but rebuilding `world.pl` fails, ingestion
returns the committed source ID and a projection warning. Repair the reported
projection problem and run `logical check` to rebuild; do not replay the update.

Existing JSONL claim and constraint records remain readable. Legacy claims retain
unknown types and **unknown freshness** and remain queryable for compatibility;
`stale` flags them for re-ingestion with provenance and a review policy. Legacy
aliases had no effect in the old engine and remain inactive until re-ingested.
Source records from the earlier version of this branch lack complete identity
provenance. They remain inspectable, but are marked stale until explicitly
retranslated with `update`; identity dependencies cannot safely be reconstructed
from their canonical triples alone. New source records use `translation_version=2`.

Quarantined claims, constraints, and their reasons are visible through `inspect`.
Source validation failures are retained, so retrying a rejected source reports
the same failure without another model call. If accepted facts establish that a
constraint's subject is a category, the invalid object-only constraint is
quarantined and its originating source audit is updated. Rejected claims cannot
disable a valid constraint. A valid source update that retires an older invalid
constraint succeeds with a warning. Conflicts are quarantined by default;
`add --interactive` can replace the explicitly listed
conflicting premises. These changes remain in the audit history.

## Development and verification

```bash
uv run --locked pytest
uv build
```

Tests preserve the original regression suite and exercise typed inference,
coreference safeguards, expiry, updates, proof-preserving compression, corrupt
provenance, concurrent writes, and failure recovery. API requests are mocked in
the default suite. SWI-Prolog tests skip explicitly when it is missing.

To also run the paid, synthetic Astra translation/coreference/update checks with
your configured API key:

```bash
LOGICAL_LIVE_TESTS=1 uv run --locked pytest tests/test_live_astra.py -v
```
