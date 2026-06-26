"""Tests for the protection self-assessment."""
import duckhound.core.permissions as perms
from duckhound.config import Settings
from duckhound.core import health


def test_exposed_when_nothing_configured(monkeypatch):
    monkeypatch.setattr(perms, "keystroke_access", lambda: (False, "blocked"))
    s = Settings(lockdown_new_keyboards=False, lock_on_lockdown=False,
                 autostart_monitor=False)
    r = health.assess(False, s)
    assert r.level == "exposed"
    assert r.score < 50
    assert "armed" in {c.key for c in r.failing}


def test_protected_when_all_layers_on(monkeypatch):
    monkeypatch.setattr(perms, "keystroke_access", lambda: (True, "granted"))
    s = Settings(lockdown_new_keyboards=True, lock_on_lockdown=True,
                 autostart_monitor=True)
    s.trusted_devices.append("05ac:0259")
    r = health.assess(True, s)
    assert r.score == 100
    assert r.level == "protected"
    assert r.failing == []


def test_arming_raises_score(monkeypatch):
    monkeypatch.setattr(perms, "keystroke_access", lambda: (False, "blocked"))
    s = Settings()
    assert health.assess(True, s).score > health.assess(False, s).score
