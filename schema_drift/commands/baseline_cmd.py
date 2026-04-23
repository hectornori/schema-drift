"""CLI sub-command: ``schema-drift baseline``

Captures the current schema from a SQL migration file and writes it as a
JSON baseline that future runs can diff against.

Usage example
-------------
    schema-drift baseline migrations/current.sql --output .schema_baseline.json
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from schema_drift.baseline import save_baseline
from schema_drift.parser import parse_migration


def add_subparser(subparsers) -> None:  # type: ignore[type-arg]
    """Register the *baseline* sub-command on *subparsers*."""
    p: ArgumentParser = subparsers.add_parser(
        "baseline",
        help="Capture a schema snapshot from a SQL file and save it as a baseline.",
    )
    p.add_argument(
        "migration",
        metavar="MIGRATION_SQL",
        help="Path to the SQL migration file to snapshot.",
    )
    p.add_argument(
        "--output",
        "-o",
        default=".schema_baseline.json",
        metavar="PATH",
        help="Destination path for the baseline JSON (default: .schema_baseline.json).",
    )
    p.set_defaults(func=run_baseline)


def run_baseline(args: Namespace) -> int:
    """Execute the baseline command; returns an exit code."""
    sql_path = Path(args.migration)
    if not sql_path.exists():
        print(f"error: migration file not found: {sql_path}", file=sys.stderr)
        return 2

    sql = sql_path.read_text(encoding="utf-8")
    snapshot = parse_migration(sql)
    output_path = Path(args.output)
    save_baseline(snapshot, output_path)

    table_count = len(snapshot.tables)
    print(f"Baseline saved to {output_path} ({table_count} table(s) captured).")
    return 0
