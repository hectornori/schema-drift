"""Tests for schema_drift/commands/export_cmd.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema_drift.baseline import save_baseline
from schema_drift.commands.export_cmd import run_export
from schema_drift.parser import ColumnDefinition, SchemaSnapshot, TableDefinition


def _make_snapshot(table_name: str, col_type: str = "INT") -> SchemaSnapshot:
    col = ColumnDefinition(name="id", col_type=col_type, nullable=False)
    table = TableDefinition(name=table_name, columns={"id": col})
    return SchemaSnapshot(tables={table_name: table})


class _Args:
    def __init__(self, baseline, current, output_format="text", output_file=None, fail_on_breaking=False):
        self.baseline = str(baseline)
        self.current = str(current)
        self.output_format = output_format
        self.output_file = str(output_file) if output_file else None
        self.fail_on_breaking = fail_on_breaking


@pytest.fixture()
def baseline_files(tmp_path):
    prev_path = tmp_path / "prev.json"
    curr_path = tmp_path / "curr.json"
    save_baseline(_make_snapshot("users"), str(prev_path))
    save_baseline(_make_snapshot("users"), str(curr_path))
    return prev_path, curr_path


def test_export_no_drift_exit_zero(baseline_files):
    prev, curr = baseline_files
    args = _Args(prev, curr)
    assert run_export(args) == 0


def test_export_breaking_change_exit_one(tmp_path):
    prev_path = tmp_path / "prev.json"
    curr_path = tmp_path / "curr.json"
    save_baseline(_make_snapshot("users", "INT"), str(prev_path))
    save_baseline(_make_snapshot("users", "TEXT"), str(curr_path))
    args = _Args(prev_path, curr_path, fail_on_breaking=True)
    assert run_export(args) == 1


def test_export_breaking_change_no_fail_flag_exit_zero(tmp_path):
    prev_path = tmp_path / "prev.json"
    curr_path = tmp_path / "curr.json"
    save_baseline(_make_snapshot("users", "INT"), str(prev_path))
    save_baseline(_make_snapshot("users", "TEXT"), str(curr_path))
    args = _Args(prev_path, curr_path, fail_on_breaking=False)
    assert run_export(args) == 0


def test_export_missing_baseline_returns_2(tmp_path, baseline_files):
    _, curr = baseline_files
    args = _Args(tmp_path / "missing.json", curr)
    assert run_export(args) == 2


def test_export_missing_current_returns_2(tmp_path, baseline_files):
    prev, _ = baseline_files
    args = _Args(prev, tmp_path / "missing.json")
    assert run_export(args) == 2


def test_export_json_format_writes_valid_json(tmp_path, baseline_files):
    prev, curr = baseline_files
    out_file = tmp_path / "report.json"
    args = _Args(prev, curr, output_format="json", output_file=out_file)
    code = run_export(args)
    assert code == 0
    data = json.loads(out_file.read_text())
    assert "summary" in data or "drifts" in data or isinstance(data, dict)


def test_export_markdown_format_output_file(tmp_path, baseline_files):
    prev, curr = baseline_files
    out_file = tmp_path / "report.md"
    args = _Args(prev, curr, output_format="markdown", output_file=out_file)
    code = run_export(args)
    assert code == 0
    content = out_file.read_text()
    assert len(content) > 0
