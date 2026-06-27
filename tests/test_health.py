"""Tests for the protection self-assessment."""
import duckhound.core.permissions as perms
from duckhound.config import Settings
from duckhound.core import health


def _patch_perms(monkeypatch, listen: bool, block: bool):
    monkeypatch.setattr(perms, "listen_access",
                        lambda: (listen, "listen" if listen else "no listen"))
    monkeypatch.setattr(perms, "block_access",
                        lambda: (block, "block" if block else "no block"))


def test_exposed_when_nothing_configured(monkeypatch):
    _patch_perms(monkeypatch, listen=False, block=False)
    s = Settings(lockdown_new_keyboards=False, lock_on_lockdown=False,
                 autostart_monitor=False)
    r = health.assess(False, s)
    assert r.level == "exposed"
    assert r.score < 50
    assert "armed" in {c.key for c in r.failing}


def test_protected_when_all_layers_on(monkeypatch):
    _patch_perms(monkeypatch, listen=True, block=True)
    s = Settings(lockdown_new_keyboards=True, lock_on_lockdown=True,
                 autostart_monitor=True)
    s.trusted_devices.append("05ac:0259")
    r = health.assess(True, s)
    assert r.score == 100
    assert r.level == "protected"
    assert r.failing == []


def test_block_permission_missing_is_flagged(monkeypatch):
    """Can detect but not block → the 'block' layer must fail."""
    _patch_perms(monkeypatch, listen=True, block=False)
    s = Settings(lockdown_new_keyboards=True, lock_on_lockdown=True,
                 autostart_monitor=True)
    s.trusted_devices.append("05ac:0259")
    r = health.assess(True, s)
    assert "block" in {c.key for c in r.failing}
    assert r.level != "protected"


def test_arming_raises_score(monkeypatch):
    _patch_perms(monkeypatch, listen=False, block=False)
    s = Settings()
    assert health.assess(True, s).score > health.assess(False, s).score
