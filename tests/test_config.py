"""Tests for settings persistence."""
import duckhound.config as cfg
from duckhound.config import Settings


def test_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "CONFIG_PATH", tmp_path / "config.json")
    s = Settings(fast_interval_ms=22, lock_screen=True, burst_run_length=14)
    s.trusted_devices.append("03eb:2ff9")
    s.save()

    loaded = Settings.load()
    assert loaded.fast_interval_ms == 22
    assert loaded.lock_screen is True
    assert loaded.burst_run_length == 14
    assert "03eb:2ff9" in loaded.trusted_devices


def test_defaults_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "CONFIG_PATH", tmp_path / "nope.json")
    s = Settings.load()
    assert s.fast_interval_ms == 30
    assert s.notify is True
    assert s.lock_screen is False


def test_unknown_keys_ignored(tmp_path, monkeypatch):
    p = tmp_path / "config.json"
    p.write_text('{"fast_interval_ms": 19, "obsolete_flag": true}')
    monkeypatch.setattr(cfg, "CONFIG_PATH", p)
    s = Settings.load()
    assert s.fast_interval_ms == 19
    assert not hasattr(s, "obsolete_flag")


def test_trusted_devices_not_shared():
    """Mutable default must not leak across instances."""
    a, b = Settings(), Settings()
    a.trusted_devices.append("x")
    assert b.trusted_devices == []
