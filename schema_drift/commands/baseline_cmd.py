"""Subcommand: generate a baseline snapshot from a migration SQL file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from schema_drift.parser import parse_migration
from schema_drift.baseline import save_baseline, snapshot_to_dict

_DEFAULT_OUTPUT = "schema_baseline.json"


def add_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser(
        "baseline",
        help="Generate a baseline snapshot JSON from a SQL migration file.",
    )
    parser.add_argument(
        "migration",
        type=Path,
        help="Path to the SQL migration file to snapshot.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help=f"Destination path for the baseline JSON (default: {_DEFAULT_OUTPUT}).",
    )
    parser.set_defaults(func=run_baseline)


def run_baseline(args: argparse.Namespace) -> int:
    """Execute the baseline subcommand. Returns an exit code."""
    migration_path: Path = args.migration

    if not migration_path.exists():
        print(f"error: migration file not found: {migration_path}", file=sys.stderr)
        return 2

    output_path: Path = args.output if args.output is not None else Path(_DEFAULT_OUTPUT)

    sql = migration_path.read_text()
    snapshot = parse_migration(sql)
    save_baseline(snapshot, output_path)

    table_count = len(snapshot.tables)
    print(f"Baseline saved to {output_path} ({table_count} table(s) captured).")
    return 0
