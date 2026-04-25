"""Integration tests for the lint subcommand."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from schema_drift.commands.lint_cmd import run_lint


@pytest.fixture()
def sql_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return p


class _Args:
    def __init__(self, migration: str, warn_only: bool = False, format: str = "text"):
        self.migration = migration
        self.warn_only = warn_only
        self.format = format


# ---------------------------------------------------------------------------

def test_lint_exit_zero_clean_migration(sql_dir: Path):
    p = _write(sql_dir, "clean.sql",
               "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));")
    rc = run_lint(_Args(str(p)))
    assert rc == 0


def test_lint_exit_one_on_error(sql_dir: Path):
    # Empty table triggers error rule
    p = _write(sql_dir, "bad.sql", "CREATE TABLE ghost ();")
    rc = run_lint(_Args(str(p)))
    assert rc == 1


def test_lint_warn_only_still_exits_zero(sql_dir: Path):
    p = _write(sql_dir, "bad.sql", "CREATE TABLE ghost ();")
    rc = run_lint(_Args(str(p), warn_only=True))
    assert rc == 0


def test_lint_missing_file_exits_two(sql_dir: Path):
    rc = run_lint(_Args(str(sql_dir / "nonexistent.sql")))
    assert rc == 2


def test_lint_json_output_structure(sql_dir: Path, capsys):
    p = _write(sql_dir, "schema.sql",
               "CREATE TABLE orders (id INT PRIMARY KEY, status VARCHAR);")
    rc = run_lint(_Args(str(p), format="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    for item in data:
        assert "level" in item
        assert "message" in item


def test_lint_text_output_no_issues(sql_dir: Path, capsys):
    p = _write(sql_dir, "ok.sql",
               "CREATE TABLE products (id INT PRIMARY KEY, price INT NOT NULL DEFAULT 0);")
    run_lint(_Args(str(p)))
    captured = capsys.readouterr()
    assert "No lint issues found" in captured.out


def test_lint_text_output_shows_issues(sql_dir: Path, capsys):
    p = _write(sql_dir, "warn.sql",
               "CREATE TABLE logs (msg TEXT);")
    run_lint(_Args(str(p)))
    captured = capsys.readouterr()
    assert "WARNING" in captured.out or "INFO" in captured.out or "ERROR" in captured.out
