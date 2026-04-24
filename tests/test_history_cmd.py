"""Tests for schema_drift/commands/history_cmd.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema_drift.baseline import save_baseline
from schema_drift.parser import ColumnDefinition, SchemaSnapshot, TableDefinition
from schema_drift.commands.history_cmd import run_history


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Args:
    def __init__(self, baseline, table=None, as_json=False):
        self.baseline = str(baseline)
        self.table = table
        self.as_json = as_json


def _make_snapshot() -> SchemaSnapshot:
    cols_users = [
        ColumnDefinition("id", "INTEGER", False, None),
        ColumnDefinition("email", "VARCHAR(255)", False, None),
    ]
    cols_posts = [
        ColumnDefinition("id", "INTEGER", False, None),
        ColumnDefinition("title", "TEXT", True, None),
    ]
    return SchemaSnapshot(
        tables={
            "users": TableDefinition("users", cols_users),
            "posts": TableDefinition("posts", cols_posts),
        }
    )


@pytest.fixture()
def baseline_file(tmp_path: Path) -> Path:
    path = tmp_path / "baseline.json"
    save_baseline(_make_snapshot(), path)
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_run_history_exit_zero(baseline_file, capsys):
    rc = run_history(_Args(baseline_file))
    assert rc == 0


def test_run_history_lists_tables(baseline_file, capsys):
    run_history(_Args(baseline_file))
    out = capsys.readouterr().out
    assert "users" in out
    assert "posts" in out


def test_run_history_lists_columns(baseline_file, capsys):
    run_history(_Args(baseline_file))
    out = capsys.readouterr().out
    assert "email" in out
    assert "VARCHAR(255)" in out


def test_run_history_filter_table(baseline_file, capsys):
    rc = run_history(_Args(baseline_file, table="users"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "users" in out
    assert "posts" not in out


def test_run_history_filter_missing_table(baseline_file, capsys):
    rc = run_history(_Args(baseline_file, table="nonexistent"))
    assert rc == 1
    err = capsys.readouterr().err
    assert "nonexistent" in err


def test_run_history_json_output(baseline_file, capsys):
    rc = run_history(_Args(baseline_file, as_json=True))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "tables" in data
    assert "users" in data["tables"]


def test_run_history_missing_file(tmp_path, capsys):
    rc = run_history(_Args(tmp_path / "nope.json"))
    assert rc == 1
    err = capsys.readouterr().err
    assert "not found" in err
