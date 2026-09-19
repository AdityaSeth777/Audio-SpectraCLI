"""Unit tests for Audio_SpectraCLI.session_history."""

import json

import pytest

from Audio_SpectraCLI import session_history


@pytest.fixture
def history_path(tmp_path):
    return str(tmp_path / "session_history.jsonl")


def test_append_and_list_round_trip(history_path):
    session_history.append_session(12.5, device_name="Built-in Mic", avg_bpm=120.4, path=history_path)

    sessions = session_history.list_sessions(path=history_path)
    assert len(sessions) == 1
    assert sessions[0]["duration_seconds"] == 12.5
    assert sessions[0]["device_name"] == "Built-in Mic"
    assert sessions[0]["avg_bpm"] == 120.4


def test_list_sessions_returns_newest_first(history_path):
    session_history.append_session(1, device_name="first", path=history_path)
    session_history.append_session(2, device_name="second", path=history_path)

    sessions = session_history.list_sessions(path=history_path)
    assert [s["device_name"] for s in sessions] == ["second", "first"]


def test_list_sessions_respects_limit(history_path):
    for i in range(5):
        session_history.append_session(i, device_name=str(i), path=history_path)

    assert len(session_history.list_sessions(limit=2, path=history_path)) == 2


def test_list_sessions_on_missing_file_is_empty(history_path):
    assert session_history.list_sessions(path=history_path) == []


def test_list_sessions_skips_malformed_lines(history_path):
    with open(history_path, "w") as f:
        f.write("not json\n")
        f.write(json.dumps({"duration_seconds": 3, "device_name": "ok"}) + "\n")

    sessions = session_history.list_sessions(path=history_path)
    assert len(sessions) == 1
    assert sessions[0]["device_name"] == "ok"


def test_clear_history_removes_the_file(history_path):
    session_history.append_session(1, path=history_path)
    session_history.clear_history(path=history_path)
    assert session_history.list_sessions(path=history_path) == []


def test_clear_history_on_missing_file_does_not_raise(history_path):
    session_history.clear_history(path=history_path)  # must not raise
