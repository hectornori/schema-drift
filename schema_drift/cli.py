"""Command-line interface for schema-drift."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from schema_drift.detector import detect_drift
from schema_drift.parser import parse_migration
from schema_drift.reporter import DriftReport, OutputFormat, render


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="schema-drift",
        description="Detect breaking schema changes between two SQL migration files.",
    )
    p.add_argument("baseline", type=Path, help="Path to the baseline migration SQL file.")
    p.add_argument("current", type=Path, help="Path to the current migration SQL file.")
    p.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        dest="fmt",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--fail-on-error",
        action="store_true",
        default=False,
        help="Exit with code 1 if breaking changes are detected.",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress output; only use exit code.",
    )
    return p


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    baseline_path: Path = args.baseline
    current_path: Path = args.current

    if not baseline_path.exists():
        print(f"Error: baseline file not found: {baseline_path}", file=sys.stderr)
        return 2
    if not current_path.exists():
        print(f"Error: current file not found: {current_path}", file=sys.stderr)
        return 2

    baseline_sql = baseline_path.read_text(encoding="utf-8")
    current_sql = current_path.read_text(encoding="utf-8")

    baseline_snapshot = parse_migration(baseline_sql)
    current_snapshot = parse_migration(current_sql)

    drifts = detect_drift(baseline_snapshot, current_snapshot)
    report = DriftReport.from_drifts(drifts)

    if not args.quiet:
        print(render(report, OutputFormat(args.fmt)))

    if args.fail_on_error and report.has_breaking_changes:
        return 1
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
