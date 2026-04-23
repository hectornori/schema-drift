"""Formats and outputs schema drift reports in multiple formats."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import List

from schema_drift.detector import SchemaDrift, Severity


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass
class DriftReport:
    total: int
    errors: int
    warnings: int
    infos: int
    drifts: List[SchemaDrift]

    @classmethod
    def from_drifts(cls, drifts: List[SchemaDrift]) -> "DriftReport":
        return cls(
            total=len(drifts),
            errors=sum(1 for d in drifts if d.severity == Severity.ERROR),
            warnings=sum(1 for d in drifts if d.severity == Severity.WARNING),
            infos=sum(1 for d in drifts if d.severity == Severity.INFO),
            drifts=drifts,
        )

    @property
    def has_breaking_changes(self) -> bool:
        return self.errors > 0


def render_text(report: DriftReport) -> str:
    lines = ["Schema Drift Report", "=" * 40]
    if not report.drifts:
        lines.append("No schema drift detected.")
    else:
        for drift in report.drifts:
            lines.append(str(drift))
    lines.append("=" * 40)
    lines.append(
        f"Total: {report.total}  Errors: {report.errors}  "
        f"Warnings: {report.warnings}  Info: {report.infos}"
    )
    return "\n".join(lines)


def render_json(report: DriftReport) -> str:
    data = {
        "summary": {
            "total": report.total,
            "errors": report.errors,
            "warnings": report.warnings,
            "infos": report.infos,
            "has_breaking_changes": report.has_breaking_changes,
        },
        "drifts": [
            {
                "severity": d.severity.value,
                "table": d.table,
                "column": d.column,
                "message": d.message,
            }
            for d in report.drifts
        ],
    }
    return json.dumps(data, indent=2)


def render_markdown(report: DriftReport) -> str:
    lines = ["## Schema Drift Report", ""]
    if not report.drifts:
        lines.append("_No schema drift detected._")
    else:
        lines.append("| Severity | Table | Column | Message |")
        lines.append("|----------|-------|--------|---------|")
        for d in report.drifts:
            col = d.column or "-"
            lines.append(f"| {d.severity.value.upper()} | `{d.table}` | `{col}` | {d.message} |")
    lines.append("")
    lines.append(
        f"**Total:** {report.total} | **Errors:** {report.errors} | "
        f"**Warnings:** {report.warnings} | **Info:** {report.infos}"
    )
    return "\n".join(lines)


def render(report: DriftReport, fmt: OutputFormat = OutputFormat.TEXT) -> str:
    if fmt == OutputFormat.JSON:
        return render_json(report)
    if fmt == OutputFormat.MARKDOWN:
        return render_markdown(report)
    return render_text(report)
