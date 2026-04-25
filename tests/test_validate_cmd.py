"""Tests for schema_drift.commands.validate_cmd."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from schema_drift.commands.validate_cmd import (
    ValidationIssue,
    add_subparser,
    run_validate,
    validate_snapshot,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SQL_WITH_PK = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
"""

SQL_WITHOUT_PK = """
CREATE TABLE logs (
    message TEXT
);
"""

SQL_EMPTY = "-- no tables here"


def _make_args(migration: str, strict: bool = False) -> argparse.Namespace:
    return argparse.Namespace(migration=migration, strict=strict)


# ---------------------------------------------------------------------------
# Unit tests for validate_snapshot
# ---------------------------------------------------------------------------


def test_no_issues_for_valid_schema():
    issues = validate_snapshot(SQL_WITH_PK)
    assert issues == []


def test_warning_for_missing_primary_key():
    issues = validate_snapshot(SQL_WITHOUT_PK)
    levels = [i.level for i in issues]
    assert "warning" in levels
    messages = " ".join(i.message for i in issues)
    assert "PRIMARY KEY" in messages


def test_error_for_empty_migration():
    issues = validate_snapshot(SQL_EMPTY)
    errors = [i for i in issues if i.level == "error"]
    assert len(errors) == 1
    assert "no CREATE TABLE" in errors[0].message


def test_warning_text_without_not_null():
    sql = """
    CREATE TABLE docs (
        id INTEGER PRIMARY KEY,
        body TEXT
    );
    """
    issues = validate_snapshot(sql)
    assert any("NOT NULL" in i.message for i in issues)


def test_validation_issue_str():
    issue = ValidationIssue("error", "Something broke")
    assert str(issue) == "[ERROR] Something broke"


# ---------------------------------------------------------------------------
# Integration tests via run_validate
# ---------------------------------------------------------------------------


def test_run_validate_exit_zero_clean(tmp_path: Path):
    f = tmp_path / "clean.sql"
    f.write_text(SQL_WITH_PK)
    assert run_validate(_make_args(str(f))) == 0


def test_run_validate_exit_zero_warnings_non_strict(tmp_path: Path):
    f = tmp_path / "warn.sql"
    f.write_text(SQL_WITHOUT_PK)
    assert run_validate(_make_args(str(f), strict=False)) == 0


def test_run_validate_exit_one_warnings_strict(tmp_path: Path):
    f = tmp_path / "warn.sql"
    f.write_text(SQL_WITHOUT_PK)
    assert run_validate(_make_args(str(f), strict=True)) == 1


def test_run_validate_exit_two_missing_file(tmp_path: Path):
    missing = str(tmp_path / "nonexistent.sql")
    assert run_validate(_make_args(missing)) == 2


def test_add_subparser_registers_validate():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_subparser(sub)
    args = parser.parse_args(["validate", "some_file.sql"])
    assert hasattr(args, "func")
    assert args.func is run_validate
