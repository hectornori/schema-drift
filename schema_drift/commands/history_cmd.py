"""history_cmd: list and inspect saved baseline snapshots."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from schema_drift.baseline import load_baseline


def add_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "history",
        help="Inspect a saved baseline snapshot file.",
    )
    p.add_argument(
        "baseline",
        help="Path to the baseline JSON file.",
    )
    p.add_argument(
        "--table",
        metavar="TABLE",
        default=None,
        help="Show details for a specific table only.",
    )
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output raw JSON instead of human-readable text.",
    )
    p.set_defaults(func=run_history)


def run_history(args: argparse.Namespace) -> int:
    baseline_path = Path(args.baseline)

    try:
        snapshot = load_baseline(baseline_path)
    except FileNotFoundError:
        print(f"Error: baseline file not found: {baseline_path}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"Error: could not parse baseline file: {exc}", file=sys.stderr)
        return 1

    tables = snapshot.tables
    if args.table:
        if args.table not in tables:
            print(
                f"Error: table '{args.table}' not found in baseline.",
                file=sys.stderr,
            )
            return 1
        tables = {args.table: tables[args.table]}

    if args.as_json:
        from schema_drift.baseline import snapshot_to_dict
        data = snapshot_to_dict(snapshot)
        if args.table:
            data["tables"] = {args.table: data["tables"][args.table]}
        print(json.dumps(data, indent=2))
        return 0

    print(f"Baseline: {baseline_path}")
    print(f"Tables  : {len(tables)}")
    print()
    for table_name, table_def in sorted(tables.items()):
        print(f"  Table: {table_name}")
        for col in table_def.columns:
            nullable = "NULL" if col.nullable else "NOT NULL"
            default = f" DEFAULT {col.default}" if col.default is not None else ""
            print(f"    - {col.name}: {col.col_type} {nullable}{default}")
    return 0
