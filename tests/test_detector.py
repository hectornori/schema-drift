"""Tests for schema drift detection between migration snapshots."""

import pytest

from schema_drift.detector import Severity, detect_drift
from schema_drift.parser import parse_migration


BASE_MIGRATION = """
CREATE TABLE users (
    id INT NOT NULL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP
);
"""


def test_no_drift_identical_schemas():
    before = parse_migration(BASE_MIGRATION)
    after = parse_migration(BASE_MIGRATION)
    drifts = detect_drift(before, after)
    assert drifts == []


def test_detect_dropped_table():
    before = parse_migration(BASE_MIGRATION)
    after = parse_migration("")
    drifts = detect_drift(before, after)
    assert any(d.severity == Severity.BREAKING and "dropped" in d.message for d in drifts)


def test_detect_new_table():
    before = parse_migration("")
    after = parse_migration(BASE_MIGRATION)
    drifts = detect_drift(before, after)
    assert any(d.severity == Severity.INFO and d.table == "users" for d in drifts)


def test_detect_dropped_column():
    after_sql = """
    CREATE TABLE users (
        id INT NOT NULL PRIMARY KEY,
        email VARCHAR(255) NOT NULL
    );
    """
    before = parse_migration(BASE_MIGRATION)
    after = parse_migration(after_sql)
    drifts = detect_drift(before, after)
    breaking = [d for d in drifts if d.severity == Severity.BREAKING]
    assert any(d.column == "name" for d in breaking)
    assert any(d.column == "created_at" for d in breaking)


def test_detect_column_type_change():
    after_sql = """
    CREATE TABLE users (
        id INT NOT NULL PRIMARY KEY,
        email TEXT NOT NULL,
        name VARCHAR(100),
        created_at TIMESTAMP
    );
    """
    before = parse_migration(BASE_MIGRATION)
    after = parse_migration(after_sql)
    drifts = detect_drift(before, after)
    type_changes = [
        d for d in drifts
        if d.severity == Severity.BREAKING and "type changed" in d.message
    ]
    assert len(type_changes) == 1
    assert type_changes[0].column == "email"


def test_detect_nullable_to_not_null():
    after_sql = """
    CREATE TABLE users (
        id INT NOT NULL PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        name VARCHAR(100) NOT NULL,
        created_at TIMESTAMP
    );
    """
    before = parse_migration(BASE_MIGRATION)
    after = parse_migration(after_sql)
    drifts = detect_drift(before, after)
    breaking = [d for d in drifts if d.severity == Severity.BREAKING]
    assert any(d.column == "name" and "NOT NULL" in d.message for d in breaking)


def test_detect_new_column_is_warning():
    after_sql = """
    CREATE TABLE users (
        id INT NOT NULL PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        name VARCHAR(100),
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    );
    """
    before = parse_migration(BASE_MIGRATION)
    after = parse_migration(after_sql)
    drifts = detect_drift(before, after)
    warnings = [d for d in drifts if d.severity == Severity.WARNING]
    assert any(d.column == "updated_at" for d in warnings)


def test_drift_str_representation():
    before = parse_migration(BASE_MIGRATION)
    after = parse_migration("")
    drifts = detect_drift(before, after)
    assert any("BREAKING" in str(d) for d in drifts)
