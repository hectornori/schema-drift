"""Tests for the compare subcommand."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema_drift.commands.compare_cmd import run_compare


SQL_BEFORE = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT
);
"""

SQL_AFTER_NO_CHANGE = SQL_BEFORE

SQL_AFTER_BREAKING = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY
);
"""

SQL_AFTER_NEW_TABLE = SQL_BEFORE + """
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER
);
"""


@pytest.fixture()
def sql_dir(tmp_path: Path):
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def _make_args(before, after, output_format="text", fail_on_breaking=False):
    class Args:
        pass
    a = Args()
    a.before = before
    a.after = after
    a.output_format = output_format
    a.fail_on_breaking = fail_on_breaking
    return a


def test_compare_no_drift_exit_zero(sql_dir):
    before = _write(sql_dir, "before.sql", SQL_BEFORE)
    after = _write(sql_dir, "after.sql", SQL_AFTER_NO_CHANGE)
    code = run_compare(_make_args(before, after))
    assert code == 0


def test_compare_breaking_no_fail_flag_exit_zero(sql_dir):
    before = _write(sql_dir, "before.sql", SQL_BEFORE)
    after = _write(sql_dir, "after.sql", SQL_AFTER_BREAKING)
    code = run_compare(_make_args(before, after, fail_on_breaking=False))
    assert code == 0


def test_compare_breaking_with_fail_flag_exit_one(sql_dir):
    before = _write(sql_dir, "before.sql", SQL_BEFORE)
    after = _write(sql_dir, "after.sql", SQL_AFTER_BREAKING)
    code = run_compare(_make_args(before, after, fail_on_breaking=True))
    assert code == 1


def test_compare_missing_before_returns_two(sql_dir):
    before = sql_dir / "nonexistent.sql"
    after = _write(sql_dir, "after.sql", SQL_AFTER_NO_CHANGE)
    code = run_compare(_make_args(before, after))
    assert code == 2


def test_compare_missing_after_returns_two(sql_dir):
    before = _write(sql_dir, "before.sql", SQL_BEFORE)
    after = sql_dir / "nonexistent.sql"
    code = run_compare(_make_args(before, after))
    assert code == 2


def test_compare_json_output_is_valid_json(sql_dir, capsys):
    before = _write(sql_dir, "before.sql", SQL_BEFORE)
    after = _write(sql_dir, "after.sql", SQL_AFTER_BREAKING)
    run_compare(_make_args(before, after, output_format="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "breaking" in data
    assert "warning" in data


def test_compare_json_output_no_drift_empty_lists(sql_dir, capsys):
    """JSON output for an unchanged schema should report no breaking or warning changes."""
    before = _write(sql_dir, "before.sql", SQL_BEFORE)
    after = _write(sql_dir, "after.sql", SQL_AFTER_NO_CHANGE)
    run_compare(_make_args(before, after, output_format="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["breaking"] == []
    assert data["warning"] == []


def test_compare_new_table_non_breaking_exit_zero(sql_dir):
    before = _write(sql_dir, "before.sql", SQL_BEFORE)
    after = _write(sql_dir, "after.sql", SQL_AFTER_NEW_TABLE)
    code = run_compare(_make_args(before, after, fail_on_breaking=True))
    assert code == 0
