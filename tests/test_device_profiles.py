"""Unit tests for Audio_SpectraCLI.device_profiles."""

import pytest

from Audio_SpectraCLI import device_profiles as device_profile_store


@pytest.fixture
def profiles_home(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIOSPECTRA_CLI_HOME", str(tmp_path))
    return tmp_path


def test_save_load_delete_round_trip(profiles_home):
    directory = device_profile_store.get_profiles_dir()
    device_profile_store.save_profile(directory, "Laptop Mic", "MacBook Pro Microphone", 44100, "mono_mix")

    assert "Laptop Mic" in device_profile_store.list_profiles(directory)
    profile = device_profile_store.load_profile(directory, "Laptop Mic")
    assert profile == {"device_name": "MacBook Pro Microphone", "fs": 44100, "channel_mode": "mono_mix"}

    device_profile_store.delete_profile(directory, "Laptop Mic")
    assert "Laptop Mic" not in device_profile_store.list_profiles(directory)


def test_list_profiles_on_empty_dir_is_empty(profiles_home):
    directory = device_profile_store.get_profiles_dir()
    assert device_profile_store.list_profiles(directory) == []


def test_save_profile_rejects_empty_name(profiles_home):
    directory = device_profile_store.get_profiles_dir()
    with pytest.raises(ValueError):
        device_profile_store.save_profile(directory, "   ", "Some Device", 44100, "mono_mix")


def test_get_profiles_dir_is_idempotent_and_isolated_per_home(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIOSPECTRA_CLI_HOME", str(tmp_path / "home_a"))
    dir_a = device_profile_store.get_profiles_dir()
    device_profile_store.save_profile(dir_a, "A", "Device A", 44100, "mono_mix")

    monkeypatch.setenv("AUDIOSPECTRA_CLI_HOME", str(tmp_path / "home_b"))
    dir_b = device_profile_store.get_profiles_dir()

    assert dir_a != dir_b
    assert device_profile_store.list_profiles(dir_b) == []
