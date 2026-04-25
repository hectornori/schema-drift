"""validate_cmd: Validate a migration SQL file for common schema issues."""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from schema_drift.parser import parse_migration


@dataclass
class ValidationIssue:
    level: str  # "error" | "warning"
    message: str

    def __str__(self) -> str:
        return f"[{self.level.upper()}] {self.message}"


def validate_snapshot(sql: str) -> List[ValidationIssue]:
    """Parse *sql* and apply heuristic validation rules."""
    issues: List[ValidationIssue] = []
    snapshot = parse_migration(sql)

    for table in snapshot.tables.values():
        has_pk = any(
            "primary key" in (col.constraints or "").lower()
            for col in table.columns.values()
        )
        if not has_pk:
            issues.append(
                ValidationIssue(
                    "warning",
                    f"Table '{table.name}' has no PRIMARY KEY column.",
                )
            )

        for col in table.columns.values():
            if col.col_type.upper() in ("TEXT", "BLOB") and not (
                col.constraints and "not null" in col.constraints.lower()
            ):
                issues.append(
                    ValidationIssue(
                        "warning",
                        f"Column '{table.name}.{col.name}' is {col.col_type} "
                        "without NOT NULL constraint.",
                    )
                )

    if not snapshot.tables:
        issues.append(
            ValidationIssue("error", "Migration contains no CREATE TABLE statements.")
        )

    return issues


def add_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "validate",
        help="Validate a migration SQL file for common schema issues.",
    )
    p.add_argument("migration", help="Path to the migration SQL file.")
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 on warnings as well as errors.",
    )
    p.set_defaults(func=run_validate)


def run_validate(args: argparse.Namespace) -> int:
    path = Path(args.migration)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    sql = path.read_text(encoding="utf-8")
    issues = validate_snapshot(sql)

    if not issues:
        print("Validation passed — no issues found.")
        return 0

    for issue in issues:
        print(issue)

    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s).")

    if errors or (args.strict and warnings):
        return 1
    return 0
