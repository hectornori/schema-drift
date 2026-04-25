"""Unit tests for schema_drift.linter."""
from __future__ import annotations

import pytest

from schema_drift.parser import ColumnDefinition, TableDefinition, SchemaSnapshot
from schema_drift.linter import lint_snapshot, LintIssue


def _make_snapshot(*tables: TableDefinition) -> SchemaSnapshot:
    return SchemaSnapshot(tables={t.name: t for t in tables})


def _col(name: str, col_type: str = "INT", constraints: str = "") -> ColumnDefinition:
    return ColumnDefinition(name=name, col_type=col_type, constraints=constraints)


def _table(name: str, *cols: ColumnDefinition) -> TableDefinition:
    return TableDefinition(name=name, columns={c.name: c for c in cols})


# ---------------------------------------------------------------------------
# _rule_no_primary_key
# ---------------------------------------------------------------------------

def test_no_issues_when_primary_key_present():
    t = _table("users", _col("id", "INT", "PRIMARY KEY"), _col("name", "TEXT"))
    issues = lint_snapshot(_make_snapshot(t))
    pk_issues = [i for i in issues if "primary key" in i.message.lower()]
    assert pk_issues == []


def test_warning_when_no_primary_key():
    t = _table("logs", _col("msg", "TEXT"))
    issues = lint_snapshot(_make_snapshot(t))
    pk_issues = [i for i in issues if "primary key" in i.message.lower()]
    assert len(pk_issues) == 1
    assert pk_issues[0].level == "warning"
    assert pk_issues[0].table == "logs"


# ---------------------------------------------------------------------------
# _rule_nullable_without_default
# ---------------------------------------------------------------------------

def test_warning_not_null_without_default():
    t = _table("orders", _col("id", "INT", "PRIMARY KEY"), _col("status", "TEXT", "NOT NULL"))
    issues = lint_snapshot(_make_snapshot(t))
    nn_issues = [i for i in issues if "NOT NULL" in i.message]
    assert len(nn_issues) == 1
    assert nn_issues[0].column == "status"


def test_no_warning_not_null_with_default():
    t = _table("orders",
               _col("id", "INT", "PRIMARY KEY"),
               _col("status", "TEXT", "NOT NULL DEFAULT 'pending'"))
    issues = lint_snapshot(_make_snapshot(t))
    nn_issues = [i for i in issues if "NOT NULL" in i.message]
    assert nn_issues == []


# ---------------------------------------------------------------------------
# _rule_varchar_without_length
# ---------------------------------------------------------------------------

def test_info_varchar_without_length():
    t = _table("items", _col("id", "INT", "PRIMARY KEY"), _col("label", "VARCHAR"))
    issues = lint_snapshot(_make_snapshot(t))
    vc_issues = [i for i in issues if "VARCHAR" in i.message]
    assert len(vc_issues) == 1
    assert vc_issues[0].level == "info"
    assert vc_issues[0].column == "label"


def test_no_info_varchar_with_length():
    t = _table("items", _col("id", "INT", "PRIMARY KEY"), _col("label", "VARCHAR(255)"))
    issues = lint_snapshot(_make_snapshot(t))
    vc_issues = [i for i in issues if "VARCHAR" in i.message]
    assert vc_issues == []


# ---------------------------------------------------------------------------
# _rule_empty_table
# ---------------------------------------------------------------------------

def test_error_for_empty_table():
    t = TableDefinition(name="empty_tbl", columns={})
    issues = lint_snapshot(_make_snapshot(t))
    err_issues = [i for i in issues if i.level == "error"]
    assert len(err_issues) == 1
    assert err_issues[0].table == "empty_tbl"


# ---------------------------------------------------------------------------
# LintIssue.__str__
# ---------------------------------------------------------------------------

def test_lint_issue_str_with_column():
    issue = LintIssue(level="warning", table="users", column="email", message="some msg")
    assert str(issue) == "[WARNING] users.email: some msg"


def test_lint_issue_str_without_column():
    issue = LintIssue(level="error", table="users", column="", message="no cols")
    assert str(issue) == "[ERROR] users: no cols"
