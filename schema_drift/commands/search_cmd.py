"""search_cmd: search for a column or table across baseline snapshots."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from schema_drift.baseline import load_baseline


def add_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "search",
        help="Search for a table or column name across one or more baseline files.",
    )
    p.add_argument(
        "term",
        help="Name to search for (case-insensitive substring match).",
    )
    p.add_argument(
        "baselines",
        nargs="+",
        metavar="BASELINE",
        help="One or more baseline JSON files to search.",
    )
    p.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Emit results as JSON.",
    )
    p.set_defaults(func=run_search)


def _search_snapshot(snapshot, term: str) -> List[dict]:
    """Return a list of match records for the given snapshot."""
    results = []
    term_lower = term.lower()
    for table_name, table in snapshot.tables.items():
        if term_lower in table_name.lower():
            results.append({"match": "table", "table": table_name, "column": None})
        for col_name in table.columns:
            if term_lower in col_name.lower():
                results.append(
                    {"match": "column", "table": table_name, "column": col_name}
                )
    return results


def run_search(args) -> int:
    term: str = args.term
    all_results: dict[str, List[dict]] = {}

    for baseline_path in args.baselines:
        path = Path(baseline_path)
        if not path.exists():
            print(f"ERROR: baseline file not found: {path}", file=sys.stderr)
            return 1
        snapshot = load_baseline(path)
        matches = _search_snapshot(snapshot, term)
        if matches:
            all_results[str(path)] = matches

    if args.output_json:
        print(json.dumps(all_results, indent=2))
    else:
        if not all_results:
            print(f"No matches found for '{term}'.")
        else:
            for file_path, matches in all_results.items():
                print(f"\n{file_path}:")
                for m in matches:
                    if m["match"] == "table":
                        print(f"  [table]  {m['table']}")
                    else:
                        print(f"  [column] {m['table']}.{m['column']}")

    return 0
