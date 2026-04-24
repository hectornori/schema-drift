"""diff subcommand — compare two migration SQL files and report schema drift.

Unlike `compare`, which works against a saved baseline, `diff` takes two
explicit SQL files and streams the drift report directly to stdout.  This
is handy for quick ad-hoc comparisons during local development.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from schema_drift.parser import parse_migration
from schema_drift.detector import detect_drift
from schema_drift.reporter import DriftReport, OutputFormat


def add_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *diff* subcommand on *subparsers*."""
    parser = subparsers.add_parser(
        "diff",
        help="Compare two SQL migration files and report schema drift.",
        description=(
            "Parse FROM_SQL and TO_SQL, detect schema changes between them, "
            "and print a drift report.  Exits with code 1 when breaking "
            "changes are found (unless --no-fail is supplied)."
        ),
    )
    parser.add_argument(
        "from_sql",
        metavar="FROM_SQL",
        help="Path to the earlier (baseline) migration SQL file.",
    )
    parser.add_argument(
        "to_sql",
        metavar="TO_SQL",
        help="Path to the newer migration SQL file.",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--no-fail",
        dest="no_fail",
        action="store_true",
        default=False,
        help="Exit 0 even when breaking changes are detected.",
    )
    parser.set_defaults(func=run_diff)


def run_diff(args: argparse.Namespace) -> int:
    """Execute the diff subcommand.

    Parameters
    ----------
    args:
        Parsed CLI arguments produced by :func:`add_subparser`.

    Returns
    -------
    int
        Exit code: ``0`` for success / no breaking changes,
        ``1`` if breaking changes were found (and ``--no-fail`` was not set),
        ``2`` for usage / IO errors.
    """
    from_path = Path(args.from_sql)
    to_path = Path(args.to_sql)

    for path in (from_path, to_path):
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 2
        if not path.is_file():
            print(f"error: not a file: {path}", file=sys.stderr)
            return 2

    try:
        from_sql = from_path.read_text(encoding="utf-8")
        to_sql = to_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: could not read file: {exc}", file=sys.stderr)
        return 2

    from_snapshot = parse_migration(from_sql)
    to_snapshot = parse_migration(to_sql)

    drifts = detect_drift(from_snapshot, to_snapshot)
    fmt = OutputFormat(args.output_format)
    report = DriftReport.from_drifts(drifts, output_format=fmt)

    print(report.render())

    if report.has_breaking_changes() and not args.no_fail:
        return 1
    return 0
