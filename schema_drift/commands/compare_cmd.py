"""Subcommand: compare two migration SQL files and report drift."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from schema_drift.parser import parse_migration
from schema_drift.detector import detect_drift
from schema_drift.reporter import DriftReport, OutputFormat, from_drifts, render_text, render_json, render_github


def add_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser(
        "compare",
        help="Compare two SQL migration files and detect schema drift.",
    )
    parser.add_argument("before", type=Path, help="SQL file representing the previous schema state.")
    parser.add_argument("after", type=Path, help="SQL file representing the new schema state.")
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        default=False,
        help="Exit with code 1 if breaking changes are detected.",
    )
    parser.set_defaults(func=run_compare)


def run_compare(args: argparse.Namespace) -> int:
    """Execute the compare subcommand. Returns an exit code."""
    before_path: Path = args.before
    after_path: Path = args.after

    for p in (before_path, after_path):
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2

    before_snapshot = parse_migration(before_path.read_text())
    after_snapshot = parse_migration(after_path.read_text())

    drifts = detect_drift(before_snapshot, after_snapshot)
    report: DriftReport = from_drifts(drifts)

    fmt = OutputFormat(args.output_format)
    if fmt == OutputFormat.JSON:
        output = render_json(report)
    elif fmt == OutputFormat.GITHUB:
        output = render_github(report)
    else:
        output = render_text(report)

    print(output)

    if args.fail_on_breaking and report.has_breaking_changes():
        return 1
    return 0
