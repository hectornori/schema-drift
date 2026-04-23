"""Tests for schema_drift.baseline — snapshot serialization round-trips."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from schema_drift.baseline import (
    load_baseline,
    save_baseline,
    snapshot_from_dict,
    snapshot_to_dict,
)
from schema_drift.parser import ColumnDefinition, SchemaSnapshot, TableDefinition


def _make_snapshot() -> SchemaSnapshot:
    return SchemaSnapshot(
        tables={
            "users": TableDefinition(
                name="users",
                columns=[
                    ColumnDefinition(name="id", col_type="INTEGER", nullable=False),
                    ColumnDefinition(name="email", col_type="TEXT", nullable=True),
                ],
            ),
            "orders": TableDefinition(
                name="orders",
                columns=[
                    ColumnDefinition(name="id", col_type="INTEGER", nullable=False),
                    ColumnDefinition(name="total", col_type="NUMERIC", nullable=True),
                ],
            ),
        }
    )


def test_snapshot_to_dict_structure():
    snap = _make_snapshot()
    d = snapshot_to_dict(snap)
    assert set(d.keys()) == {"users", "orders"}
    assert d["users"]["columns"][0] == {
        "name": "id",
        "col_type": "INTEGER",
        "nullable": False,
    }


def test_snapshot_round_trip_via_dict():
    original = _make_snapshot()
    restored = snapshot_from_dict(snapshot_to_dict(original))
    assert set(restored.tables.keys()) == set(original.tables.keys())
    for name, table in original.tables.items():
        restored_table = restored.tables[name]
        assert [(c.name, c.col_type, c.nullable) for c in restored_table.columns] == [
            (c.name, c.col_type, c.nullable) for c in table.columns
        ]


def test_save_and_load_baseline(tmp_path: Path):
    snap = _make_snapshot()
    baseline_path = tmp_path / "baselines" / "schema.json"
    save_baseline(snap, baseline_path)

    assert baseline_path.exists()
    raw = json.loads(baseline_path.read_text())
    assert "users" in raw

    loaded = load_baseline(baseline_path)
    assert set(loaded.tables.keys()) == {"users", "orders"}
    assert loaded.tables["users"].columns[1].col_type == "TEXT"


def test_load_baseline_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Baseline file not found"):
        load_baseline(tmp_path / "nonexistent.json")


def test_save_baseline_creates_parents(tmp_path: Path):
    snap = _make_snapshot()
    deep_path = tmp_path / "a" / "b" / "c" / "schema.json"
    save_baseline(snap, deep_path)
    assert deep_path.exists()
