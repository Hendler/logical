from __future__ import annotations

import argparse
from typing import Sequence

from logical.openai_client import OpenAIExtractor
from logical.service import add_knowledge, ask_knowledge, check_knowledge, export_prolog
from logical.store import KnowledgeStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="logical")
    parser.add_argument("--store-dir", default=".logical")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("text")
    add_parser.add_argument("--interactive", action="store_true")
    add_parser.add_argument("--noninteractive", action="store_true")

    ask_parser = subparsers.add_parser("ask")
    ask_parser.add_argument("text")

    subparsers.add_parser("check")
    subparsers.add_parser("export-prolog")
    return parser


def main(
    argv: Sequence[str] | None = None,
    extractor: OpenAIExtractor | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    store = KnowledgeStore(args.store_dir)

    if args.command == "add":
        extractor = extractor or OpenAIExtractor()
        interactive = args.interactive and not args.noninteractive
        result = add_knowledge(
            args.text,
            store=store,
            extractor=extractor,
            interactive=interactive,
        )
        for claim in result.accepted:
            print(f"accepted: {claim.s} {claim.p} {claim.o}")
        for claim in result.quarantined:
            print(f"quarantined: {claim.s} {claim.p} {claim.o}")
        for conflict in result.conflicts:
            print(f"conflict: {conflict.message}")
        for issue in result.invalid:
            print(f"invalid: {issue.message}")
        return 2 if result.quarantined or result.invalid else 0

    if args.command == "ask":
        extractor = extractor or OpenAIExtractor()
        result = ask_knowledge(args.text, store=store, extractor=extractor)
        print(result.answer)
        for claim in result.evidence:
            print(f"evidence: {claim.s} {claim.p} {claim.o} ({claim.id})")
        return 0

    if args.command == "check":
        result = check_knowledge(store)
        print(result.message)
        return 0 if result.ok else 1

    if args.command == "export-prolog":
        print(export_prolog(store))
        return 0

    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
