"""Command-line interface for the multi-agent RAG system.

Usage:
    python -m src.cli                       # interactive REPL
    python -m src.cli -q "What is our security policy?"   # one-shot query
"""
from __future__ import annotations

import argparse
import sys

from tabulate import tabulate

from src.agents.manager_agent import ManagerAgent, ManagerResponse


def format_response(response: ManagerResponse) -> str:
    lines = [f"\n[{response.query_type.upper()}] {response.query}", "-" * 60, response.answer]

    if response.qualitative and response.qualitative.citations:
        lines.append("\nSources:")
        for c in response.qualitative.citations:
            lines.append(f"  - {c.source} ({c.chunk_id}), similarity={c.similarity}")

    if response.quantitative:
        lines.append(f"\nSQL: {response.quantitative.sql}")
        if response.quantitative.rows:
            lines.append(tabulate(response.quantitative.rows, headers="keys", tablefmt="simple"))

    return "\n".join(lines)


def run_repl(manager: ManagerAgent) -> None:
    print("Multi-Agent Enterprise Documentation System")
    print("Type a question, or 'exit' to quit.\n")
    while True:
        try:
            query = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query:
            continue
        if query.lower() in {"exit", "quit"}:
            break
        response = manager.handle_query(query)
        print(format_response(response))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Multi-Agent RAG CLI")
    parser.add_argument("-q", "--query", help="Run a single query and exit")
    args = parser.parse_args(argv)

    manager = ManagerAgent()

    if args.query:
        response = manager.handle_query(args.query)
        print(format_response(response))
        return 0

    run_repl(manager)
    return 0


if __name__ == "__main__":
    sys.exit(main())
