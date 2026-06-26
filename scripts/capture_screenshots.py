"""Render real DuckHound screenshots offscreen for the README.

Run:  QT_QPA_PLATFORM=offscreen QT_SCALE_FACTOR=2 python scripts/capture_screenshots.py
Builds the live app, stages a rich (but realistic) state, then grabs each page.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from duckhound.config import Settings                       # noqa: E402
from duckhound.core.models import (Device, DeviceKind, DeviceState,  # noqa: E402
                                   Severity, ThreatEvent)
from duckhound.ui.main_window import build_window           # noqa: E402

OUT = ROOT / "assets" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def stage(win) -> None:
    """Freeze the app on a realistic, populated frame."""
    eng = win.engine
    eng.stop()  # halt timers so the frame is stable

    # Add a freshly-plugged rogue keyboard + a quarantined one.
    rogue = Device(key="03eb:2ff9", name="USB Rubber Ducky (Atmel)",
                   kind=DeviceKind.KEYBOARD, vendor_id="03eb", product_id="2ff9",
                   manufacturer="(unknown)", state=DeviceState.SUSPECT)
    rogue.first_seen = time.time() - 3
    pico = Device(key="2e8a:0003", name="Raspberry Pi Pico HID",
                  kind=DeviceKind.HID, vendor_id="2e8a", product_id="0003",
                  state=DeviceState.BLOCKED)
    eng.devices[rogue.key] = rogue
    eng.devices[pico.key] = pico

    # A richer threat log.
    eng.events.insert(0, ThreatEvent(
        title="BadUSB activity: USB Rubber Ducky (Atmel)",
        detail="Sustained 980 keys/s for 42 keystrokes with machine-perfect "
               "timing — a classic keystroke-injection payload.",
        severity=Severity.CRITICAL, score=97, device_name="USB Rubber Ducky (Atmel)",
        metrics={"keys_per_sec": 980, "mean_interval_ms": 1.0, "jitter_cv": 0.04,
                 "run_length": 42},
        actions=["Alerted", "Locked screen"]))
    eng.events.append(ThreatEvent(
        title="New input device connected",
        detail="Raspberry Pi Pico enumerated as a HID keyboard within 2s of "
               "insertion — placed under watch.",
        severity=Severity.MEDIUM, score=48, device_name="Raspberry Pi Pico HID",
        metrics={"keys_per_sec": 0, "run_length": 0},
        actions=["Alerted"], timestamp=time.time() - 900))
    eng._threats, eng._blocked, eng._keys_analyzed = 3, 2, 41877
    eng._started_at = time.time() - (2 * 3600 + 14 * 60)  # ~2h 14m uptime

    # Dashboard live readouts (set both value+target so no easing needed).
    win.dashboard.set_stats(eng.snapshot_stats())
    win.dashboard.set_devices(eng.device_list())
    win.dashboard.set_monitoring(True)
    win.dashboard.set_status("Live — monitoring keystrokes + USB (macos/system_profiler)")
    m = win.dashboard.meter
    m._value = m._target = 78.0
    r = win.dashboard.radar
    r._level = 78.0
    r._angle = 48.0
    r.set_devices(eng.device_list())
    r.ping(True)
    r._pings[-1]["t"] = time.monotonic() - 0.5
    win.dashboard.signal_lbl.setText("980 keys/sec")
    for ev in reversed(eng.events[:3]):
        win.dashboard.on_threat(ev)

    win.devices.set_devices(eng.device_list())
    win.devices.set_allowlist([("05ac:0259", "Apple Internal Keyboard"),
                               ("046d:c534", "Logitech Unifying Receiver")])
    win.threats.set_events(list(eng.events))


def grab(win, index: int, name: str) -> None:
    win.sidebar.select(index)
    win.stack.setCurrentIndex(index)
    QApplication.processEvents()
    QApplication.processEvents()
    path = OUT / f"{name}.png"
    win.grab().save(str(path))
    print(f"  saved {path.relative_to(ROOT)}  ({win.grab().width()}px)")


def main() -> int:
    app = QApplication(sys.argv)
    from duckhound.ui.theme import build_qss
    app.setStyleSheet(build_qss())
    settings = Settings()
    settings.autostart_monitor = False
    win = build_window(settings, demo=True)
    win.resize(1280, 820)
    win.show()
    QApplication.processEvents()
    stage(win)
    for idx, name in enumerate(("dashboard", "devices", "threats", "settings")):
        grab(win, idx, name)
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
