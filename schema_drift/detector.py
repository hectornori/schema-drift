"""Detects breaking schema changes between two SchemaSnapshots."""

from dataclasses import dataclass
from enum import Enum
from typing import List

from schema_drift.parser import SchemaSnapshot


class Severity(str, Enum):
    BREAKING = "BREAKING"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class SchemaDrift:
    severity: Severity
    message: str
    table: str
    column: str = ""

    def __str__(self) -> str:
        location = f"{self.table}.{self.column}" if self.column else self.table
        return f"[{self.severity.value}] {location}: {self.message}"


def detect_drift(before: SchemaSnapshot, after: SchemaSnapshot) -> List[SchemaDrift]:
    """Compare two snapshots and return a list of detected drift events."""
    drifts: List[SchemaDrift] = []

    # Detect dropped tables
    for table_name in before.tables:
        if table_name not in after.tables:
            drifts.append(
                SchemaDrift(
                    severity=Severity.BREAKING,
                    message="Table was dropped",
                    table=table_name,
                )
            )

    # Detect added tables
    for table_name in after.tables:
        if table_name not in before.tables:
            drifts.append(
                SchemaDrift(
                    severity=Severity.INFO,
                    message="New table added",
                    table=table_name,
                )
            )

    # Detect column-level changes
    for table_name, before_table in before.tables.items():
        if table_name not in after.tables:
            continue
        after_table = after.tables[table_name]

        for col_name, before_col in before_table.columns.items():
            if col_name not in after_table.columns:
                drifts.append(
                    SchemaDrift(
                        severity=Severity.BREAKING,
                        message="Column was dropped",
                        table=table_name,
                        column=col_name,
                    )
                )
                continue

            after_col = after_table.columns[col_name]

            if before_col.col_type != after_col.col_type:
                drifts.append(
                    SchemaDrift(
                        severity=Severity.BREAKING,
                        message=f"Column type changed from {before_col.col_type} to {after_col.col_type}",
                        table=table_name,
                        column=col_name,
                    )
                )

            if before_col.nullable and not after_col.nullable:
                drifts.append(
                    SchemaDrift(
                        severity=Severity.BREAKING,
                        message="Column changed from nullable to NOT NULL without a default"
                        if after_col.default is None
                        else "Column changed from nullable to NOT NULL (default provided)",
                        table=table_name,
                        column=col_name,
                    )
                )

        for col_name in after_table.columns:
            if col_name not in before_table.columns:
                drifts.append(
                    SchemaDrift(
                        severity=Severity.WARNING,
                        message="New column added",
                        table=table_name,
                        column=col_name,
                    )
                )

    return drifts
