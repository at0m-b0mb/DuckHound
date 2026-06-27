"""Protection self-assessment — turns DuckHound's state into a score + checklist.

This is what lets the app *prove* it will stop a Rubber Ducky / Flipper instead
of just claiming to. Each layer of defence is a weighted check; the UI shows the
score, the failing items, and a one-click fix for each.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import permissions


@dataclass
class Check:
    key: str
    label: str
    ok: bool
    detail: str
    weight: int = 1
    fixable: bool = True


@dataclass
class ProtectionReport:
    checks: list[Check] = field(default_factory=list)

    @property
    def score(self) -> int:
        total = sum(c.weight for c in self.checks)
        got = sum(c.weight for c in self.checks if c.ok)
        return int(round(100 * got / total)) if total else 0

    @property
    def level(self) -> str:
        s = self.score
        return "protected" if s >= 85 else "at_risk" if s >= 50 else "exposed"

    @property
    def passing(self) -> int:
        return sum(1 for c in self.checks if c.ok)

    @property
    def failing(self) -> list[Check]:
        return [c for c in self.checks if not c.ok]


def assess(monitoring: bool, settings) -> ProtectionReport:
    perm_ok, perm_detail = permissions.listen_access()
    block_ok, block_detail = permissions.block_access()
    checks = [
        Check("armed", "Monitoring is armed", monitoring,
              "DuckHound is actively watching the keyboard + USB bus."
              if monitoring else "Arm monitoring so DuckHound can react.",
              weight=2),
        Check("lockdown", "Lockdown on new keyboards",
              settings.lockdown_new_keyboards,
              "A newly-plugged keyboard is challenged instantly."
              if settings.lockdown_new_keyboards
              else "Enable Lockdown so a rogue keyboard is stopped on sight.",
              weight=2),
        Check("lock", "Auto screen-lock response", settings.lock_on_lockdown,
              "The screen locks the moment a rogue keyboard appears — no "
              "special permission needed." if settings.lock_on_lockdown
              else "Turn on screen-lock so injected keystrokes hit a locked screen.",
              weight=1),
        Check("perm", "Keystroke-monitoring permission", perm_ok, perm_detail,
              weight=2),
        Check("block", "Keystroke-blocking permission", block_ok,
              "DuckHound can freeze a rogue keyboard's input." if block_ok
              else block_detail + " — required to actually STOP an attack.",
              weight=2),
        Check("baseline", "Trusted-keyboard baseline", bool(settings.trusted_devices),
              "Your real keyboards are allow-listed, so only unknown devices "
              "trigger a lock." if settings.trusted_devices
              else "Trust your real keyboards once so they don't false-alarm.",
              weight=1),
        Check("autostart", "Arms automatically on launch",
              settings.autostart_monitor,
              "Protection turns on by itself." if settings.autostart_monitor
              else "Enable auto-arm for always-on, set-and-forget protection.",
              weight=1),
    ]
    return ProtectionReport(checks)
