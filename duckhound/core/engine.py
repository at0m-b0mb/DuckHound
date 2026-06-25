"""DetectionEngine — orchestrates monitoring, scoring and response.

This is the GUI-facing brain. It owns:
  * a KeystrokeAnalyzer fed by a global keyboard hook (pynput),
  * a USB backend polled on a timer to spot devices arriving/leaving,
  * a Responder that fires the user's chosen countermeasures,
and broadcasts everything to the UI over Qt signals so widgets stay decoupled
from the detection logic. A ``demo`` mode replaces the live hooks with a
realistic simulated attack feed — no devices or OS permissions required.
"""
from __future__ import annotations

import random
import time

from PySide6.QtCore import QObject, QTimer, Signal

from ..config import Settings
from . import simulator
from .backends import get_backend
from .keystroke import KeystrokeAnalyzer, Verdict
from .models import Device, DeviceState, Severity, ThreatEvent
from .responder import Responder


class DetectionEngine(QObject):
    monitoring_changed = Signal(bool)
    devices_changed = Signal(list)          # list[Device]
    device_announced = Signal(object, bool)  # (Device, is_new)
    threat_detected = Signal(object)         # ThreatEvent
    activity = Signal(float, float)          # (threat_score 0-100, keys/sec)
    stats_changed = Signal(dict)
    status_text = Signal(str)

    def __init__(self, settings: Settings, demo: bool = False) -> None:
        super().__init__()
        self.settings = settings
        self.demo = demo
        self.analyzer = KeystrokeAnalyzer(
            fast_interval_ms=settings.fast_interval_ms,
            burst_run_length=settings.burst_run_length,
            robotic_cv_threshold=settings.robotic_cv_threshold,
        )
        self.responder = Responder(settings)
        self.backend = get_backend()

        self.devices: dict[str, Device] = {}
        self.events: list[ThreatEvent] = []
        self.monitoring = False
        self._started_at = time.time()
        self._keys_analyzed = 0
        self._threats = 0
        self._blocked = 0
        self._listener = None

        # Timers (parented to self -> live on the GUI thread).
        self._usb_timer = QTimer(self)
        self._usb_timer.setInterval(2500)
        self._usb_timer.timeout.connect(self._poll_usb)

        self._decay_timer = QTimer(self)
        self._decay_timer.setInterval(120)
        self._decay_timer.timeout.connect(self._decay)
        self._level = 0.0

        # Demo machinery.
        self._demo_timer = QTimer(self)
        self._demo_timer.timeout.connect(self._maybe_demo_attack)
        self._burst_timer = QTimer(self)
        self._burst_timer.timeout.connect(self._burst_step)
        self._burst = iter(())
        self._sim_t = 0.0
        self._fired = False
        self._pending_rogue: Device | None = None

        if demo:
            self._seed_demo_history()

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def start(self) -> None:
        if self.monitoring:
            return
        self.monitoring = True
        self._decay_timer.start()
        if self.demo:
            self._demo_timer.start(random.randint(6000, 10000))
            self.status_text.emit("Simulation armed — watching for injected keystrokes")
        else:
            self._poll_usb()
            self._usb_timer.start()
            self._start_keyboard_hook()
            who = self.backend.name if self.backend.supported else "keystroke-only"
            self.status_text.emit(f"Live — monitoring keystrokes + USB ({who})")
        self.monitoring_changed.emit(True)
        self._emit_stats()

    def stop(self) -> None:
        if not self.monitoring:
            return
        self.monitoring = False
        self._usb_timer.stop()
        self._demo_timer.stop()
        self._burst_timer.stop()
        self._decay_timer.stop()
        self._stop_keyboard_hook()
        self.activity.emit(0.0, 0.0)
        self.monitoring_changed.emit(False)
        self.status_text.emit("Monitoring paused")

    def toggle(self) -> None:
        self.stop() if self.monitoring else self.start()

    def apply_settings(self, settings: Settings) -> None:
        self.settings = settings
        self.responder.settings = settings
        self.analyzer.update_thresholds(
            settings.fast_interval_ms,
            settings.burst_run_length,
            settings.robotic_cv_threshold,
        )

    # ------------------------------------------------------------------ #
    # Keyboard hook (live mode)
    # ------------------------------------------------------------------ #
    def _start_keyboard_hook(self) -> None:
        try:
            from pynput import keyboard
        except Exception:
            self.status_text.emit("Live keystroke hook unavailable (pynput missing)")
            return
        try:
            self._listener = keyboard.Listener(on_press=self._on_key)
            self._listener.start()
        except Exception as exc:  # permission denied, headless, etc.
            self._listener = None
            self.status_text.emit(f"Keystroke hook blocked — grant Input Monitoring ({exc})")

    def _stop_keyboard_hook(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def _on_key(self, _key) -> None:
        """Runs on the pynput thread; signals marshal back to the GUI."""
        verdict = self.analyzer.feed()
        self._keys_analyzed += 1
        self._level = max(self._level, float(verdict.score))
        self.activity.emit(float(verdict.score), verdict.cps)
        if verdict.is_attack:
            self._raise_threat(self._suspect_device(), verdict)

    def _suspect_device(self) -> Device | None:
        """Best guess at which device is typing: the most recently added input
        device still inside its grace window."""
        now = time.time()
        recent = [
            d for d in self.devices.values()
            if d.is_input and not d.is_internal
            and (now - d.first_seen) <= self.settings.new_device_grace_s
        ]
        recent.sort(key=lambda d: d.first_seen, reverse=True)
        return recent[0] if recent else None

    # ------------------------------------------------------------------ #
    # USB polling (live mode)
    # ------------------------------------------------------------------ #
    def _poll_usb(self) -> None:
        try:
            current = {d.key: d for d in self.backend.enumerate()}
        except Exception:
            return
        # New arrivals.
        for key, dev in current.items():
            if key not in self.devices:
                if dev.is_internal and self.settings.trust_internal_keyboard:
                    dev.state = DeviceState.TRUSTED
                elif key in self.settings.trusted_devices:
                    dev.state = DeviceState.TRUSTED
                self.devices[key] = dev
                self.analyzer.reset()  # a fresh keyboard restarts the burst clock
                self.device_announced.emit(dev, True)
            else:
                self.devices[key].last_seen = time.time()
        # Departures.
        for key in list(self.devices):
            if key not in current and not self.devices[key].is_internal:
                self.devices.pop(key, None)
        self.devices_changed.emit(self._device_list())
        self._emit_stats()

    # ------------------------------------------------------------------ #
    # Threat handling
    # ------------------------------------------------------------------ #
    def _raise_threat(self, device: Device | None, verdict: Verdict) -> None:
        if device is not None and device.state == DeviceState.TRUSTED:
            return  # user explicitly trusts this keyboard
        sev = _severity(verdict, device)
        if device is not None:
            device.state = DeviceState.SUSPECT
        ev = ThreatEvent(
            title="Keystroke injection detected"
            if device is None else f"BadUSB activity: {device.name}",
            detail=verdict.reason or "Superhuman keystroke timing observed.",
            severity=sev,
            score=verdict.score,
            device_key=device.key if device else "",
            device_name=device.name if device else "Unknown input device",
            metrics={
                "keys_per_sec": round(verdict.cps, 1),
                "mean_interval_ms": round(verdict.mean_ms, 1),
                "jitter_cv": round(verdict.cv, 3),
                "run_length": verdict.run_length,
            },
        )
        # Fire countermeasures.
        if self.demo:
            ev.actions = self._demo_actions()
        else:
            ev.actions = self.responder.respond(ev.title, ev.detail)
        if ev.actions:
            self._blocked += 1
            if device is not None:
                device.state = DeviceState.BLOCKED
        self._threats += 1
        self.events.insert(0, ev)
        self._level = 100.0
        self.analyzer.reset()
        self.threat_detected.emit(ev)
        self.devices_changed.emit(self._device_list())
        self._emit_stats()

    def trust_device(self, key: str) -> None:
        dev = self.devices.get(key)
        if not dev:
            return
        dev.state = DeviceState.TRUSTED
        if key not in self.settings.trusted_devices:
            self.settings.trusted_devices.append(key)
            self.settings.save()
        self.devices_changed.emit(self._device_list())

    def block_device(self, key: str) -> None:
        dev = self.devices.get(key)
        if dev:
            dev.state = DeviceState.BLOCKED
            self.devices_changed.emit(self._device_list())

    # ------------------------------------------------------------------ #
    # Demo / simulation
    # ------------------------------------------------------------------ #
    def _seed_demo_history(self) -> None:
        for dev in simulator.baseline_devices():
            self.devices[dev.key] = dev
        # A couple of resolved events so the log isn't empty on first paint.
        self.events.append(ThreatEvent(
            title="BadUSB activity: USB Rubber Ducky (Atmel)",
            detail="980 keys/s sustained for 42 keystrokes with machine-like timing.",
            severity=Severity.CRITICAL, score=97,
            device_name="USB Rubber Ducky (Atmel)",
            metrics={"keys_per_sec": 980.0, "mean_interval_ms": 1.0, "jitter_cv": 0.04,
                     "run_length": 42},
            actions=["Alerted", "Locked screen"],
            timestamp=time.time() - 2640,
        ))
        self.events.append(ThreatEvent(
            title="New input device connected",
            detail="Digispark ATTINY85 enumerated as a keyboard.",
            severity=Severity.LOW, score=22,
            device_name="Digispark ATTINY85",
            timestamp=time.time() - 5400,
        ))
        self._threats = 1
        self._blocked = 1
        self._keys_analyzed = 18422

    def _maybe_demo_attack(self) -> None:
        self._demo_timer.start(random.randint(9000, 15000))
        if self._burst_timer.isActive():
            return
        rogue = simulator.make_rogue()
        self.devices[rogue.key] = rogue
        self.device_announced.emit(rogue, True)
        self.devices_changed.emit(self._device_list())
        self._pending_rogue = rogue
        self._fired = False
        self.analyzer.reset()
        self._burst = simulator.injection_intervals(
            count=55, mean_ms=random.uniform(2.5, 6.0))
        self._sim_t = time.monotonic()
        self._burst_timer.start(16)

    def _burst_step(self) -> None:
        try:
            iv = next(self._burst)
        except StopIteration:
            self._burst_timer.stop()
            return
        self._sim_t += iv
        verdict = self.analyzer.feed(self._sim_t)
        self._keys_analyzed += 1
        self._level = max(self._level, float(verdict.score))
        self.activity.emit(float(verdict.score), verdict.cps)
        if verdict.is_attack and not self._fired:
            self._fired = True
            self._raise_threat(self._pending_rogue, verdict)

    def _demo_actions(self) -> list[str]:
        out = []
        if self.settings.notify:
            out.append("Alerted")
        if self.settings.lock_screen:
            out.append("Locked screen")
        if self.settings.block_keystrokes:
            out.append("Blocked keystrokes")
        if self.settings.deauthorize_device:
            out.append("Flagged for de-authorization")
        return out or ["Alerted"]

    # ------------------------------------------------------------------ #
    # Housekeeping
    # ------------------------------------------------------------------ #
    def _decay(self) -> None:
        if self._level > 0:
            self._level = max(0.0, self._level - 3.5)
            self.activity.emit(self._level, 0.0)

    def _device_list(self) -> list[Device]:
        return sorted(self.devices.values(),
                      key=lambda d: (d.is_internal, -d.first_seen))

    def device_list(self) -> list[Device]:
        """Public snapshot of currently-known devices."""
        return self._device_list()

    def _emit_stats(self) -> None:
        self.stats_changed.emit(self.snapshot_stats())

    def snapshot_stats(self) -> dict:
        return {
            "devices": len(self.devices),
            "input_devices": sum(1 for d in self.devices.values() if d.is_input),
            "threats": self._threats,
            "blocked": self._blocked,
            "keys_analyzed": self._keys_analyzed,
            "uptime_s": int(time.time() - self._started_at),
            "backend": self.backend.name,
            "backend_ok": self.backend.supported,
            "threat_level": self._level,
        }


def _severity(verdict: Verdict, device: Device | None) -> Severity:
    s = verdict.score
    fresh = device is not None and (time.time() - device.first_seen) < 12
    if s >= 90 or (s >= 75 and fresh):
        return Severity.CRITICAL
    if s >= 75:
        return Severity.HIGH
    if s >= 55:
        return Severity.MEDIUM
    if s >= 30:
        return Severity.LOW
    return Severity.INFO
