"""Tests for schema_drift/commands/search_cmd.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema_drift.baseline import save_baseline
from schema_drift.parser import ColumnDefinition, SchemaSnapshot, TableDefinition
from schema_drift.commands.search_cmd import run_search


def _col(name: str, col_type: str = "TEXT") -> ColumnDefinition:
    return ColumnDefinition(name=name, col_type=col_type, nullable=True, default=None)


def _make_snapshot() -> SchemaSnapshot:
    tables = {
        "users": TableDefinition(
            name="users",
            columns={
                "id": _col("id", "INTEGER"),
                "email": _col("email", "VARCHAR(255)"),
            },
        ),
        "orders": TableDefinition(
            name="orders",
            columns={
                "id": _col("id", "INTEGER"),
                "user_id": _col("user_id", "INTEGER"),
                "total": _col("total", "NUMERIC"),
            },
        ),
    }
    return SchemaSnapshot(tables=tables)


@pytest.fixture()
def baseline_file(tmp_path: Path) -> Path:
    p = tmp_path / "baseline.json"
    save_baseline(_make_snapshot(), p)
    return p


class _Args:
    def __init__(self, term: str, baselines, output_json: bool = False):
        self.term = term
        self.baselines = baselines
        self.output_json = output_json


def test_search_finds_table(baseline_file: Path):
    args = _Args("users", [str(baseline_file)])
    rc = run_search(args)
    assert rc == 0


def test_search_finds_column(baseline_file: Path):
    args = _Args("email", [str(baseline_file)])
    rc = run_search(args)
    assert rc == 0


def test_search_no_match_returns_zero(baseline_file: Path, capsys):
    args = _Args("nonexistent_xyz", [str(baseline_file)])
    rc = run_search(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "No matches found" in captured.out


def test_search_json_output(baseline_file: Path, capsys):
    args = _Args("user", [str(baseline_file)], output_json=True)
    rc = run_search(args)
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert str(baseline_file) in data
    match_types = {m["match"] for m in data[str(baseline_file)]}
    assert "table" in match_types or "column" in match_types


def test_search_missing_baseline_returns_error(tmp_path: Path, capsys):
    missing = str(tmp_path / "does_not_exist.json")
    args = _Args("users", [missing])
    rc = run_search(args)
    assert rc == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_search_case_insensitive(baseline_file: Path, capsys):
    args = _Args("ORDERS", [str(baseline_file)], output_json=True)
    rc = run_search(args)
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    matches = data.get(str(baseline_file), [])
    assert any(m["table"] == "orders" for m in matches)
