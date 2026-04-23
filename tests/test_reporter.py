"""Tests for schema_drift.reporter module."""

from __future__ import annotations

import json

import pytest

from schema_drift.detector import Severity, SchemaDrift
from schema_drift.reporter import DriftReport, OutputFormat, render, render_json, render_markdown, render_text


def _make_drifts():
    return [
        SchemaDrift(severity=Severity.ERROR, table="users", column="email", message="Column dropped"),
        SchemaDrift(severity=Severity.WARNING, table="orders", column=None, message="Table dropped"),
        SchemaDrift(severity=Severity.INFO, table="products", column="price", message="Type changed"),
    ]


def test_report_summary_counts():
    drifts = _make_drifts()
    report = DriftReport.from_drifts(drifts)
    assert report.total == 3
    assert report.errors == 1
    assert report.warnings == 1
    assert report.infos == 1


def test_report_has_breaking_changes_true():
    drifts = _make_drifts()
    report = DriftReport.from_drifts(drifts)
    assert report.has_breaking_changes is True


def test_report_has_breaking_changes_false():
    drifts = [
        SchemaDrift(severity=Severity.INFO, table="t", column=None, message="New table added"),
    ]
    report = DriftReport.from_drifts(drifts)
    assert report.has_breaking_changes is False


def test_render_text_no_drift():
    report = DriftReport.from_drifts([])
    output = render_text(report)
    assert "No schema drift detected" in output
    assert "Total: 0" in output


def test_render_text_with_drifts():
    report = DriftReport.from_drifts(_make_drifts())
    output = render_text(report)
    assert "users" in output
    assert "orders" in output
    assert "Total: 3" in output


def test_render_json_structure():
    report = DriftReport.from_drifts(_make_drifts())
    output = render_json(report)
    data = json.loads(output)
    assert "summary" in data
    assert data["summary"]["total"] == 3
    assert data["summary"]["has_breaking_changes"] is True
    assert len(data["drifts"]) == 3


def test_render_markdown_table_header():
    report = DriftReport.from_drifts(_make_drifts())
    output = render_markdown(report)
    assert "| Severity |" in output
    assert "`users`" in output


def test_render_markdown_no_drift():
    report = DriftReport.from_drifts([])
    output = render_markdown(report)
    assert "No schema drift detected" in output


def test_render_dispatch():
    report = DriftReport.from_drifts([])
    assert render(report, OutputFormat.TEXT) == render_text(report)
    assert render(report, OutputFormat.JSON) == render_json(report)
    assert render(report, OutputFormat.MARKDOWN) == render_markdown(report)
