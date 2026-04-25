"""lint_cmd: Check migration SQL files for common style and safety issues."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from schema_drift.parser import parse_migration
from schema_drift.linter import lint_snapshot


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "lint",
        help="Lint a migration SQL file for style and safety issues.",
    )
    p.add_argument("migration", help="Path to the migration SQL file.")
    p.add_argument(
        "--warn-only",
        action="store_true",
        default=False,
        help="Exit 0 even when errors are found.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=run_lint)


def run_lint(args: argparse.Namespace) -> int:
    """Entry point for the lint subcommand.  Returns an exit code."""
    migration_path = Path(args.migration)
    if not migration_path.exists():
        print(f"Error: migration file not found: {migration_path}", file=sys.stderr)
        return 2

    sql = migration_path.read_text(encoding="utf-8")
    snapshot = parse_migration(sql)
    issues = lint_snapshot(snapshot)

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        payload = [
            {
                "level": i.level,
                "table": i.table,
                "column": i.column,
                "message": i.message,
            }
            for i in issues
        ]
        print(json.dumps(payload, indent=2))
    else:
        if not issues:
            print("No lint issues found.")
        else:
            for issue in issues:
                print(str(issue))

    has_errors = any(i.level == "error" for i in issues)
    if has_errors and not getattr(args, "warn_only", False):
        return 1
    return 0
