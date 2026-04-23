"""Baseline snapshot management for schema-drift.

Allows saving and loading a SchemaSnapshot to/from a JSON file so that
CI workflows can compare the current migration state against a stored
baseline rather than always diffing two live SQL files.
"""

from __future__ import annotations

import json
from pathlib import Path

from schema_drift.parser import ColumnDefinition, SchemaSnapshot, TableDefinition


def snapshot_to_dict(snapshot: SchemaSnapshot) -> dict:
    """Serialize a SchemaSnapshot to a plain dictionary."""
    return {
        table_name: {
            "columns": [
                {"name": col.name, "col_type": col.col_type, "nullable": col.nullable}
                for col in table.columns
            ]
        }
        for table_name, table in snapshot.tables.items()
    }


def snapshot_from_dict(data: dict) -> SchemaSnapshot:
    """Deserialize a SchemaSnapshot from a plain dictionary."""
    tables: dict[str, TableDefinition] = {}
    for table_name, table_data in data.items():
        columns = [
            ColumnDefinition(
                name=col["name"],
                col_type=col["col_type"],
                nullable=col["nullable"],
            )
            for col in table_data["columns"]
        ]
        tables[table_name] = TableDefinition(name=table_name, columns=columns)
    return SchemaSnapshot(tables=tables)


def save_baseline(snapshot: SchemaSnapshot, path: Path) -> None:
    """Write *snapshot* as JSON to *path*, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot_to_dict(snapshot), indent=2), encoding="utf-8")


def load_baseline(path: Path) -> SchemaSnapshot:
    """Load and return a SchemaSnapshot from the JSON file at *path*.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Baseline file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return snapshot_from_dict(data)
