from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Sequence

from openai import OpenAIError

from logical.openai_client import OpenAIExtractor
from logical.schema import QueryIntent, record_to_dict
from logical.service import (
    add_knowledge,
    ask_knowledge,
    ask_query,
    check_knowledge,
    compress_knowledge,
    export_prolog,
    freshness_report,
)
from logical.store import KnowledgeStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logical",
        description="Source-backed knowledge with typed logic, proofs and freshness.",
    )
    parser.add_argument("--store-dir", default=".logical")
    parser.add_argument(
        "--model", help="translation model (default: LOGICAL_MODEL or gpt-6-astra)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("add", "update"):
        add_parser = subparsers.add_parser(
            command,
            help="ingest a source"
            if command == "add"
            else "atomically replace a source after validating its new contents",
        )
        if command == "update":
            add_parser.add_argument("source_id")
        add_parser.add_argument("text", nargs="?")
        add_parser.add_argument(
            "--file", type=Path, help="read source text from a UTF-8 file"
        )
        add_parser.add_argument(
            "--source-ref",
            default="",
            help="citation URL or document identifier (not fetched)",
        )
        add_parser.add_argument(
            "--observed-at",
            help="when the source was observed (ISO timestamp with timezone)",
        )
        add_parser.add_argument(
            "--ttl-days",
            type=float,
            default=30,
            help="review interval from observation (default: 30 days)",
        )
        mode = add_parser.add_mutually_exclusive_group()
        mode.add_argument("--interactive", action="store_true")
        mode.add_argument("--noninteractive", action="store_true")
        add_parser.add_argument("--json", action="store_true")
    ask_parser = subparsers.add_parser("ask")
    ask_parser.add_argument("text")
    ask_parser.add_argument("--json", action="store_true")
    query_parser = subparsers.add_parser(
        "query", help="query a canonical triple without an API call"
    )
    query_parser.add_argument("s")
    query_parser.add_argument("p")
    query_parser.add_argument("o")
    query_parser.add_argument("--negative", action="store_true")
    query_parser.add_argument("--json", action="store_true")
    subparsers.add_parser("check")
    subparsers.add_parser("export-prolog")
    stale_parser = subparsers.add_parser(
        "stale", help="list expired evidence and unknown freshness"
    )
    stale_parser.add_argument("--json", action="store_true")
    subparsers.add_parser(
        "inspect",
        help="inspect all records, sources, resolutions and quarantine reasons as JSON",
    )
    subparsers.add_parser(
        "compress",
        help="export an irredundant logical basis with proof and provenance sidecars",
    )
    return parser


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))


def main(
    argv: Sequence[str] | None = None, extractor: OpenAIExtractor | None = None
) -> int:
    args = build_parser().parse_args(argv)
    store = KnowledgeStore(args.store_dir)
    try:
        if args.command in {"add", "update"}:
            if (args.text is None) == (args.file is None):
                raise ValueError("provide exactly one source: text or --file")
            text = args.file.read_text(encoding="utf-8") if args.file else args.text
            # Lazily construct the API client, allowing duplicate ingestion without an API key.
            if extractor is None and args.model:
                extractor = OpenAIExtractor(model=args.model)
            result = add_knowledge(
                text,
                store,
                extractor,
                interactive=args.interactive,
                source_ref=args.source_ref
                or (str(args.file.resolve()) if args.file else ""),
                file_path=str(args.file.resolve()) if args.file else "",
                observed_at=args.observed_at,
                ttl_days=args.ttl_days,
                replaces=args.source_id if args.command == "update" else None,
            )
            if args.json:
                _json(asdict(result))
            else:
                print(f"source: {result.source_id}")
                for claim in result.accepted:
                    print(f"accepted: {claim.s} {claim.p} {claim.o}")
                for claim in result.quarantined:
                    print(f"quarantined: {claim.s} {claim.p} {claim.o}")
                for duplicate in result.duplicates:
                    print(
                        f"duplicate: {duplicate} (evidence retained; existing review deadlines preserved)"
                    )
                for conflict in result.conflicts:
                    print(f"conflict: {conflict.message}")
                for issue in result.invalid:
                    print(f"invalid: {issue.message}")
                for unresolved in result.unresolved:
                    print(f"unresolved: {unresolved['text']} — {unresolved['reason']}")
                for warning in result.warnings:
                    print(f"warning: {warning}", file=sys.stderr)
            return 2 if result.quarantined or result.invalid or result.unresolved else 0
        if args.command in {"ask", "query"}:
            if args.command == "ask":
                result = ask_knowledge(
                    args.text, store, extractor or OpenAIExtractor(model=args.model)
                )
            else:
                result = ask_query(
                    QueryIntent(args.s, args.p, args.o, not args.negative), store
                )
            if args.json:
                _json(asdict(result))
            else:
                print(result.answer)
                print(f"evaluated at: {result.evaluated_at}")
                if result.reason:
                    print(result.reason)
                sources = {s.id: s for s in result.sources}
                for claim in result.evidence:
                    print(
                        f"evidence: {claim.s} {claim.p} {claim.o} ({claim.id}; {result.freshness[claim.id]})"
                    )
                    for evidence in claim.evidence:
                        source = sources.get(evidence.source_id)
                        print(
                            f"  {source.reference or source.id if source else evidence.source_id}: {evidence.quote}"
                        )
                for alias in result.identity_evidence:
                    print(
                        f"identity: {alias.alias} = {alias.canonical} ({alias.source_id}): {alias.evidence}"
                    )
                for constraint in result.constraint_evidence:
                    print(
                        f"constraint: {constraint.kind} {constraint.s} {constraint.p} ({constraint.source_id}): {constraint.evidence}"
                    )
            return 0
        if args.command == "check":
            result = check_knowledge(store)
            print(result.message)
            return 0 if result.ok else 1
        if args.command == "export-prolog":
            print(export_prolog(store))
            return 0
        if args.command == "inspect":
            _json(
                {
                    "records": [record_to_dict(r) for r in store.load_records()],
                    "freshness": freshness_report(store),
                }
            )
            return 0
        if args.command == "compress":
            _json(compress_knowledge(store))
            return 0
        if args.command == "stale":
            entries = [r for r in freshness_report(store) if r["freshness"] != "fresh"]
            if args.json:
                _json(entries)
            elif not entries:
                print("No stale, future or unknown-freshness claims.")
            else:
                for entry in entries:
                    print(
                        f"{entry['freshness']}: {entry['s']} {entry['p']} {entry['o']} ({entry['id']}): {'; '.join(entry['reasons'])}"
                    )
            return 0
    except OpenAIError as exc:
        # SDK errors can embed request data. Keep credentials/source text out of diagnostics.
        print(
            f"error: OpenAI {type(exc).__name__}; translation failed. Check model access, credentials and connectivity.",
            file=sys.stderr,
        )
        return 1
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
