"""Tests for schema_drift.cli module."""

from __future__ import annotations

from pathlib import Path

import pytest

from schema_drift.cli import run

BASELINE_SQL = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255)
);
"""

CURRENT_SQL_NO_DRIFT = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255)
);
"""

CURRENT_SQL_BREAKING = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);
"""


@pytest.fixture()
def sql_files(tmp_path: Path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p

    return _write


def test_exit_code_zero_no_drift(sql_files):
    baseline = sql_files("baseline.sql", BASELINE_SQL)
    current = sql_files("current.sql", CURRENT_SQL_NO_DRIFT)
    code = run([str(baseline), str(current), "--fail-on-error"])
    assert code == 0


def test_exit_code_one_breaking_changes(sql_files):
    baseline = sql_files("baseline.sql", BASELINE_SQL)
    current = sql_files("current.sql", CURRENT_SQL_BREAKING)
    code = run([str(baseline), str(current), "--fail-on-error"])
    assert code == 1


def test_exit_code_zero_without_fail_on_error(sql_files):
    baseline = sql_files("baseline.sql", BASELINE_SQL)
    current = sql_files("current.sql", CURRENT_SQL_BREAKING)
    code = run([str(baseline), str(current)])
    assert code == 0


def test_missing_baseline_returns_2(sql_files, tmp_path):
    current = sql_files("current.sql", CURRENT_SQL_NO_DRIFT)
    code = run([str(tmp_path / "nonexistent.sql"), str(current)])
    assert code == 2


def test_missing_current_returns_2(sql_files, tmp_path):
    baseline = sql_files("baseline.sql", BASELINE_SQL)
    code = run([str(baseline), str(tmp_path / "nonexistent.sql")])
    assert code == 2


def test_json_format_runs_without_error(sql_files, capsys):
    baseline = sql_files("baseline.sql", BASELINE_SQL)
    current = sql_files("current.sql", CURRENT_SQL_NO_DRIFT)
    code = run([str(baseline), str(current), "--format", "json"])
    assert code == 0
    captured = capsys.readouterr()
    import json
    data = json.loads(captured.out)
    assert "summary" in data


def test_quiet_flag_suppresses_output(sql_files, capsys):
    baseline = sql_files("baseline.sql", BASELINE_SQL)
    current = sql_files("current.sql", CURRENT_SQL_NO_DRIFT)
    run([str(baseline), str(current), "--quiet"])
    captured = capsys.readouterr()
    assert captured.out == ""
