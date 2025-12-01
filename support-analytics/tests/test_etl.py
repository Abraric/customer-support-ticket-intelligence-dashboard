from pathlib import Path

import pandas as pd

from etl.ticket_etl import sanitize_text, synthesize_ticket_rows
from etl.telemetry_etl import synthesize_telemetry_rows


def test_sanitize_text_removes_extra_spaces():
    assert sanitize_text("backup   failure\\n alert") == "backup failure alert"


def test_ticket_synthesis_output(tmp_path, monkeypatch):
    monkeypatch.setenv("TICKET_RAW_PATH", str(tmp_path / "tickets.csv"))
    df = synthesize_ticket_rows(record_count=10, seed=1)
    assert len(df) == 10
    assert {"ticket_id", "issue_description", "severity"}.issubset(df.columns)


def test_telemetry_synthesis_output(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEMETRY_RAW_PATH", str(tmp_path / "telemetry.csv"))
    df = synthesize_telemetry_rows(record_count=20, seed=1)
    assert len(df) == 20
    assert {"event_id", "node_id", "event_type"}.issubset(df.columns)

