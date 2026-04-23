"""Tests for schema_drift.commands.baseline_cmd."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from schema_drift.commands.baseline_cmd import run_baseline


SAMPLE_SQL = """
CREATE TABLE users (
    id INTEGER NOT NULL,
    name TEXT
);
CREATE TABLE products (
    id INTEGER NOT NULL,
    price NUMERIC
);
"""


@pytest.fixture()
def sql_file(tmp_path: Path) -> Path:
    p = tmp_path / "migration.sql"
    p.write_text(SAMPLE_SQL, encoding="utf-8")
    return p


def test_run_baseline_creates_file(sql_file: Path, tmp_path: Path):
    output = tmp_path / "baseline.json"
    args = Namespace(migration=str(sql_file), output=str(output))
    exit_code = run_baseline(args)
    assert exit_code == 0
    assert output.exists()


def test_run_baseline_json_content(sql_file: Path, tmp_path: Path):
    output = tmp_path / "baseline.json"
    args = Namespace(migration=str(sql_file), output=str(output))
    run_baseline(args)
    data = json.loads(output.read_text())
    assert "users" in data
    assert "products" in data
    col_names = [c["name"] for c in data["users"]["columns"]]
    assert "id" in col_names


def test_run_baseline_missing_migration(tmp_path: Path):
    output = tmp_path / "baseline.json"
    args = Namespace(migration=str(tmp_path / "nope.sql"), output=str(output))
    exit_code = run_baseline(args)
    assert exit_code == 2
    assert not output.exists()


def test_run_baseline_default_output_name(sql_file: Path, tmp_path: Path, monkeypatch):
    """When --output is the default, the file is created in the cwd."""
    monkeypatch.chdir(tmp_path)
    args = Namespace(migration=str(sql_file), output=".schema_baseline.json")
    exit_code = run_baseline(args)
    assert exit_code == 0
    assert (tmp_path / ".schema_baseline.json").exists()
