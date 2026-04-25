"""Export drift report to various output formats (JSON, text, Markdown)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from schema_drift.baseline import load_baseline
from schema_drift.detector import detect_drift
from schema_drift.reporter import DriftReport, OutputFormat, from_drifts, render_json, render_markdown, render_text


def add_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser(
        "export",
        help="Export a drift report between two baseline snapshots.",
    )
    parser.add_argument("baseline", help="Path to the previous baseline JSON file.")
    parser.add_argument("current", help="Path to the current baseline JSON file.")
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--output",
        "-o",
        dest="output_file",
        default=None,
        help="Write output to this file instead of stdout.",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        default=False,
        help="Exit with code 1 if breaking changes are detected.",
    )
    parser.set_defaults(func=run_export)


def run_export(args: argparse.Namespace) -> int:
    """Run the export subcommand. Returns an exit code."""
    try:
        previous = load_baseline(args.baseline)
    except FileNotFoundError:
        print(f"error: baseline file not found: {args.baseline}", file=sys.stderr)
        return 2

    try:
        current = load_baseline(args.current)
    except FileNotFoundError:
        print(f"error: current file not found: {args.current}", file=sys.stderr)
        return 2

    drifts = detect_drift(previous, current)
    report: DriftReport = from_drifts(drifts)

    fmt = OutputFormat(args.output_format)
    if fmt == OutputFormat.JSON:
        rendered = render_json(report)
    elif fmt == OutputFormat.MARKDOWN:
        rendered = render_markdown(report)
    else:
        rendered = render_text(report)

    if args.output_file:
        Path(args.output_file).write_text(rendered, encoding="utf-8")
    else:
        print(rendered)

    if args.fail_on_breaking and report.has_breaking_changes():
        return 1
    return 0
