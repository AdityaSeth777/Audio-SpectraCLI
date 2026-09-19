"""Unit tests for Audio_SpectraCLI.export_manifest."""

import json
import os

from Audio_SpectraCLI import export_manifest


def _touch(path):
    with open(path, "w") as f:
        f.write("x")


def test_record_and_list_round_trip(tmp_path):
    manifest_path = str(tmp_path / "manifest.jsonl")
    export_manifest.record_export("png", "/tmp/a.png", path=manifest_path)

    exports = export_manifest.list_exports(path=manifest_path)
    assert len(exports) == 1
    assert exports[0]["type"] == "png"
    assert exports[0]["path"] == "/tmp/a.png"


def test_list_exports_returns_newest_first(tmp_path):
    manifest_path = str(tmp_path / "manifest.jsonl")
    export_manifest.record_export("png", "first.png", path=manifest_path)
    export_manifest.record_export("csv", "second.csv", path=manifest_path)

    exports = export_manifest.list_exports(path=manifest_path)
    assert [e["path"] for e in exports] == ["second.csv", "first.png"]


def test_list_exports_skips_malformed_lines(tmp_path):
    manifest_path = tmp_path / "manifest.jsonl"
    manifest_path.write_text("not json\n" + json.dumps({"type": "wav", "path": "ok.wav"}) + "\n")

    exports = export_manifest.list_exports(path=str(manifest_path))
    assert len(exports) == 1
    assert exports[0]["path"] == "ok.wav"


def test_list_exports_only_existing_drops_missing_files(tmp_path):
    manifest_path = str(tmp_path / "manifest.jsonl")
    existing = str(tmp_path / "exists.png")
    _touch(existing)
    export_manifest.record_export("png", existing, path=manifest_path)
    export_manifest.record_export("png", str(tmp_path / "gone.png"), path=manifest_path)

    exports = export_manifest.list_exports(path=manifest_path, only_existing=True)
    assert [e["path"] for e in exports] == [existing]


def test_delete_export_removes_file_and_manifest_entry(tmp_path):
    manifest_path = str(tmp_path / "manifest.jsonl")
    target = str(tmp_path / "delete_me.csv")
    _touch(target)
    export_manifest.record_export("csv", target, path=manifest_path)
    export_manifest.record_export("csv", "keep_me.csv", path=manifest_path)

    removed = export_manifest.delete_export(target, path=manifest_path)

    assert removed is True
    assert not os.path.exists(target)
    remaining = export_manifest.list_exports(path=manifest_path)
    assert [e["path"] for e in remaining] == ["keep_me.csv"]


def test_delete_export_on_missing_file_still_cleans_manifest(tmp_path):
    manifest_path = str(tmp_path / "manifest.jsonl")
    export_manifest.record_export("csv", "already_gone.csv", path=manifest_path)

    removed = export_manifest.delete_export("already_gone.csv", path=manifest_path)

    assert removed is False
    assert export_manifest.list_exports(path=manifest_path) == []
