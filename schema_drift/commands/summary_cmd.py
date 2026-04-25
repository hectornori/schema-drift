"""summary command – prints an aggregated overview of drift across multiple baseline files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from schema_drift.baseline import load_baseline
from schema_drift.detector import detect_drift, Severity
from schema_drift.reporter import DriftReport, from_drifts


def add_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "summary",
        help="Summarise drift across one or more baseline snapshot files.",
    )
    p.add_argument(
        "baselines",
        nargs="+",
        metavar="BASELINE",
        help="Baseline JSON files to compare in order (oldest … newest).",
    )
    p.add_argument(
        "--fail-on-breaking",
        action="store_true",
        default=False,
        help="Exit with code 1 if any breaking changes are found.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text).",
    )
    p.set_defaults(func=run_summary)


def run_summary(args: argparse.Namespace) -> int:
    paths: List[Path] = [Path(b) for b in args.baselines]

    for p in paths:
        if not p.exists():
            print(f"error: baseline file not found: {p}", file=sys.stderr)
            return 2

    if len(paths) < 2:
        print("error: at least two baseline files are required.", file=sys.stderr)
        return 2

    snapshots = [load_baseline(p) for p in paths]

    total_breaking = 0
    total_warning = 0
    total_info = 0
    reports: List[DriftReport] = []

    for prev, curr in zip(snapshots, snapshots[1:]):
        drifts = detect_drift(prev, curr)
        report = from_drifts(drifts)
        reports.append(report)
        total_breaking += report.breaking
        total_warning += report.warning
        total_info += report.info

    _print_summary(paths, reports, args.output_format, total_breaking, total_warning, total_info)

    if args.fail_on_breaking and total_breaking > 0:
        return 1
    return 0


def _print_summary(
    paths: List[Path],
    reports: List[DriftReport],
    fmt: str,
    total_breaking: int,
    total_warning: int,
    total_info: int,
) -> None:
    if fmt == "json":
        import json

        out = {
            "total_breaking": total_breaking,
            "total_warning": total_warning,
            "total_info": total_info,
            "comparisons": [
                {
                    "from": str(paths[i]),
                    "to": str(paths[i + 1]),
                    "breaking": r.breaking,
                    "warning": r.warning,
                    "info": r.info,
                }
                for i, r in enumerate(reports)
            ],
        }
        print(json.dumps(out, indent=2))
    else:
        print(f"Schema Drift Summary ({len(reports)} comparison(s))")
        print("=" * 50)
        for i, r in enumerate(reports):
            label = f"  {paths[i].name} -> {paths[i + 1].name}"
            print(f"{label}")
            print(f"    breaking={r.breaking}  warning={r.warning}  info={r.info}")
        print("-" * 50)
        print(f"  TOTAL  breaking={total_breaking}  warning={total_warning}  info={total_info}")
