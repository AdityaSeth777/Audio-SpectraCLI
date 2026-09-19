"""Unit tests for Audio_SpectraCLI.presets: the named-preset CRUD module
backing the GUI's preset manager and the "hardware knob" builtin presets.
"""

import pytest

from Audio_SpectraCLI import presets as preset_store


@pytest.fixture
def presets_home(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIOSPECTRA_CLI_HOME", str(tmp_path))
    return tmp_path


def test_get_presets_dir_seeds_builtins(presets_home):
    directory = preset_store.get_presets_dir()
    names = preset_store.list_presets(directory)
    assert set(preset_store.BUILTIN_PRESETS) == set(names)


def test_get_presets_dir_is_idempotent(presets_home):
    first = preset_store.get_presets_dir()
    preset_store.delete_preset(first, "Balanced (default)")
    second = preset_store.get_presets_dir()
    assert first == second
    # A second call must not re-seed over a preset the user deleted.
    assert "Balanced (default)" not in preset_store.list_presets(second)


def test_save_load_delete_round_trip(presets_home):
    directory = preset_store.get_presets_dir()
    settings = {"block_size": 1024, "fs": 22050}

    preset_store.save_preset(directory, "My Preset", settings)
    assert "My Preset" in preset_store.list_presets(directory)
    assert preset_store.load_preset(directory, "My Preset") == settings

    preset_store.delete_preset(directory, "My Preset")
    assert "My Preset" not in preset_store.list_presets(directory)


def test_rename_preset(presets_home):
    directory = preset_store.get_presets_dir()
    preset_store.save_preset(directory, "Old Name", {"fs": 44100})

    preset_store.rename_preset(directory, "Old Name", "New Name")

    names = preset_store.list_presets(directory)
    assert "New Name" in names
    assert "Old Name" not in names
    assert preset_store.load_preset(directory, "New Name") == {"fs": 44100}


def test_rename_preset_refuses_to_clobber_existing(presets_home):
    directory = preset_store.get_presets_dir()
    preset_store.save_preset(directory, "A", {"fs": 1})
    preset_store.save_preset(directory, "B", {"fs": 2})

    with pytest.raises(FileExistsError):
        preset_store.rename_preset(directory, "A", "B")

    # Neither preset should have been touched by the failed rename.
    assert preset_store.load_preset(directory, "A") == {"fs": 1}
    assert preset_store.load_preset(directory, "B") == {"fs": 2}


def test_save_preset_rejects_empty_or_symbol_only_name(presets_home):
    directory = preset_store.get_presets_dir()
    for bad_name in ("", "   ", "///", "**"):
        with pytest.raises(ValueError):
            preset_store.save_preset(directory, bad_name, {})


def test_list_presets_is_case_insensitive_sorted(presets_home):
    directory = preset_store.get_presets_dir()
    for name in ("zebra", "Alpha", "beta"):
        preset_store.save_preset(directory, name, {})

    names = preset_store.list_presets(directory)
    assert names.index("Alpha") < names.index("beta") < names.index("zebra")


def test_builtin_presets_only_use_keys_apply_settings_dict_understands():
    # Guards against a builtin preset silently doing nothing in the GUI
    # because it uses a key apply_settings_dict() doesn't recognize.
    recognized_keys = {
        "duration", "fs", "block_size", "frequency_range", "color",
        "window_type", "noise_threshold", "channel_mode", "db_scale",
        "view_mode", "peak_hold_enabled", "smoothing_sigma", "smoothing_enabled",
    }
    for name, settings in preset_store.BUILTIN_PRESETS.items():
        assert set(settings).issubset(recognized_keys), name
