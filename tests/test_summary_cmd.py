"""Tests for schema_drift.commands.summary_cmd."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pytest

from schema_drift.baseline import save_baseline
from schema_drift.parser import ColumnDefinition, SchemaSnapshot, TableDefinition
from schema_drift.commands.summary_cmd import run_summary


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _col(name: str, col_type: str = "INTEGER", nullable: bool = True) -> ColumnDefinition:
    return ColumnDefinition(name=name, col_type=col_type, nullable=nullable, default=None)


def _table(name: str, cols: List[ColumnDefinition]) -> TableDefinition:
    return TableDefinition(name=name, columns={c.name: c for c in cols})


def _snap(tables: List[TableDefinition]) -> SchemaSnapshot:
    return SchemaSnapshot(tables={t.name: t for t in tables})


class _Args:
    def __init__(self, baselines, fail_on_breaking=False, output_format="text"):
        self.baselines = baselines
        self.fail_on_breaking = fail_on_breaking
        self.output_format = output_format


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def baseline_files(tmp_path: Path):
    """Return three baseline files: v1 -> v2 (no drift), v2 -> v3 (breaking)."""
    v1 = _snap([_table("users", [_col("id"), _col("name", "TEXT")])])
    v2 = _snap([_table("users", [_col("id"), _col("name", "TEXT")])])
    v3 = _snap([_table("users", [_col("id")])])  # dropped 'name' column – breaking

    p1, p2, p3 = tmp_path / "v1.json", tmp_path / "v2.json", tmp_path / "v3.json"
    save_baseline(v1, p1)
    save_baseline(v2, p2)
    save_baseline(v3, p3)
    return p1, p2, p3


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_summary_exit_zero_no_drift(baseline_files):
    p1, p2, _ = baseline_files
    args = _Args(baselines=[str(p1), str(p2)])
    assert run_summary(args) == 0


def test_summary_exit_zero_breaking_without_flag(baseline_files):
    p1, p2, p3 = baseline_files
    args = _Args(baselines=[str(p1), str(p2), str(p3)])
    assert run_summary(args) == 0


def test_summary_exit_one_breaking_with_flag(baseline_files):
    p1, p2, p3 = baseline_files
    args = _Args(baselines=[str(p1), str(p2), str(p3)], fail_on_breaking=True)
    assert run_summary(args) == 1


def test_summary_missing_file(tmp_path: Path):
    args = _Args(baselines=[str(tmp_path / "nope.json"), str(tmp_path / "also_nope.json")])
    assert run_summary(args) == 2


def test_summary_single_file_error(baseline_files):
    p1, *_ = baseline_files
    args = _Args(baselines=[str(p1)])
    assert run_summary(args) == 2


def test_summary_json_output(baseline_files, capsys):
    p1, p2, p3 = baseline_files
    args = _Args(baselines=[str(p1), str(p2), str(p3)], output_format="json")
    run_summary(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "total_breaking" in data
    assert "comparisons" in data
    assert len(data["comparisons"]) == 2
    assert data["total_breaking"] >= 1


def test_summary_text_output(baseline_files, capsys):
    p1, p2, p3 = baseline_files
    args = _Args(baselines=[str(p1), str(p2), str(p3)], output_format="text")
    run_summary(args)
    captured = capsys.readouterr()
    assert "TOTAL" in captured.out
    assert "breaking" in captured.out
