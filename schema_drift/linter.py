"""linter: Rules that inspect a SchemaSnapshot for style and safety issues."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from schema_drift.parser import SchemaSnapshot


@dataclass
class LintIssue:
    level: str  # "error" | "warning" | "info"
    table: str
    column: str  # empty string when issue is table-level
    message: str

    def __str__(self) -> str:
        location = self.table
        if self.column:
            location = f"{self.table}.{self.column}"
        return f"[{self.level.upper()}] {location}: {self.message}"


# ---------------------------------------------------------------------------
# Individual rule functions
# ---------------------------------------------------------------------------

def _rule_no_primary_key(snapshot: SchemaSnapshot) -> List[LintIssue]:
    issues: List[LintIssue] = []
    for table in snapshot.tables.values():
        has_pk = any(
            "primary key" in (c.constraints or "").lower()
            for c in table.columns.values()
        )
        if not has_pk:
            issues.append(LintIssue(
                level="warning",
                table=table.name,
                column="",
                message="Table has no primary key column.",
            ))
    return issues


def _rule_nullable_without_default(snapshot: SchemaSnapshot) -> List[LintIssue]:
    issues: List[LintIssue] = []
    for table in snapshot.tables.values():
        for col in table.columns.values():
            constraints = (col.constraints or "").lower()
            if "not null" in constraints and "default" not in constraints:
                issues.append(LintIssue(
                    level="warning",
                    table=table.name,
                    column=col.name,
                    message="NOT NULL column has no DEFAULT — adding it to existing tables is unsafe.",
                ))
    return issues


def _rule_varchar_without_length(snapshot: SchemaSnapshot) -> List[LintIssue]:
    issues: List[LintIssue] = []
    for table in snapshot.tables.values():
        for col in table.columns.values():
            if col.col_type.lower().startswith("varchar") and "(" not in col.col_type:
                issues.append(LintIssue(
                    level="info",
                    table=table.name,
                    column=col.name,
                    message="VARCHAR column declared without an explicit length.",
                ))
    return issues


def _rule_empty_table(snapshot: SchemaSnapshot) -> List[LintIssue]:
    issues: List[LintIssue] = []
    for table in snapshot.tables.values():
        if not table.columns:
            issues.append(LintIssue(
                level="error",
                table=table.name,
                column="",
                message="Table has no columns defined.",
            ))
    return issues


_RULES = [
    _rule_no_primary_key,
    _rule_nullable_without_default,
    _rule_varchar_without_length,
    _rule_empty_table,
]


def lint_snapshot(snapshot: SchemaSnapshot) -> List[LintIssue]:
    """Run all lint rules against *snapshot* and return a flat list of issues."""
    issues: List[LintIssue] = []
    for rule in _RULES:
        issues.extend(rule(snapshot))
    return issues
