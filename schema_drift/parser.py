"""Parses SQL migration files and extracts schema definitions."""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ColumnDefinition:
    name: str
    col_type: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False


@dataclass
class TableDefinition:
    name: str
    columns: dict[str, ColumnDefinition] = field(default_factory=dict)


@dataclass
class SchemaSnapshot:
    tables: dict[str, TableDefinition] = field(default_factory=dict)


CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?(\w+)[`\"]?\s*\(([^;]+)\)",
    re.IGNORECASE | re.DOTALL,
)
COLUMN_RE = re.compile(
    r"^\s*[`\"]?(\w+)[`\"]?\s+(\w+(?:\(\d+(?:,\s*\d+)?\))?)\s*(.*?)\s*$",
    re.IGNORECASE,
)


def _parse_column(line: str) -> Optional[ColumnDefinition]:
    skip_keywords = {"constraint", "primary", "unique", "index", "key", "check", "foreign"}
    stripped = line.strip().lstrip("`\"")
    if any(stripped.lower().startswith(kw) for kw in skip_keywords):
        return None

    match = COLUMN_RE.match(line)
    if not match:
        return None

    name, col_type, rest = match.group(1), match.group(2), match.group(3).upper()
    nullable = "NOT NULL" not in rest
    primary_key = "PRIMARY KEY" in rest

    default_match = re.search(r"DEFAULT\s+(\S+)", rest, re.IGNORECASE)
    default = default_match.group(1) if default_match else None

    return ColumnDefinition(
        name=name,
        col_type=col_type.upper(),
        nullable=nullable,
        default=default,
        primary_key=primary_key,
    )


def parse_migration(sql: str) -> SchemaSnapshot:
    """Parse a SQL migration string and return a SchemaSnapshot."""
    snapshot = SchemaSnapshot()

    for match in CREATE_TABLE_RE.finditer(sql):
        table_name = match.group(1)
        columns_block = match.group(2)
        table = TableDefinition(name=table_name)

        for raw_line in columns_block.split(","):
            col = _parse_column(raw_line.strip())
            if col:
                table.columns[col.name] = col

        snapshot.tables[table_name] = table

    return snapshot
