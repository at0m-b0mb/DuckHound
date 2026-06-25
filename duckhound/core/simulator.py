"""Synthetic attack feed for demos, screenshots and tests.

Lets DuckHound show — and be verified — without an actual Rubber Ducky or any
OS permissions. It mimics the two halves of a real attack: a rogue keyboard
appearing on the bus, then a burst of machine-perfect keystrokes.
"""
from __future__ import annotations

import random
import time

from .models import Device, DeviceKind, DeviceState

# A few well-known BadUSB-capable gadgets, by their real USB IDs.
ROGUE_GADGETS = [
    ("Hak5 Rubber Ducky", "3eb", "2402", DeviceKind.KEYBOARD),
    ("USB Rubber Ducky (Atmel)", "03eb", "2ff9", DeviceKind.KEYBOARD),
    ("Digispark ATTINY85", "16d0", "0753", DeviceKind.KEYBOARD),
    ("Raspberry Pi Pico HID", "2e8a", "0003", DeviceKind.KEYBOARD),
    ("Generic HID Keyboard", "1a2c", "2d23", DeviceKind.KEYBOARD),
    ("Flipper Zero BadUSB", "0483", "5740", DeviceKind.HID),
]

BASELINE_DEVICES = [
    ("Apple Internal Keyboard", "05ac", "0259", DeviceKind.KEYBOARD, True),
    ("USB Receiver", "046d", "c534", DeviceKind.HID, False),
    ("SanDisk Ultra", "0781", "5581", DeviceKind.STORAGE, False),
    ("USB2.0 Hub", "05e3", "0608", DeviceKind.HUB, False),
]


def baseline_devices() -> list[Device]:
    out = []
    for name, vid, pid, kind, internal in BASELINE_DEVICES:
        d = Device(
            key=f"{vid}:{pid}", name=name, kind=kind,
            vendor_id=vid, product_id=pid, manufacturer="",
            is_internal=internal,
            state=DeviceState.TRUSTED if internal else DeviceState.KNOWN,
        )
        out.append(d)
    return out


def make_rogue() -> Device:
    name, vid, pid, kind = random.choice(ROGUE_GADGETS)
    return Device(
        key=f"{vid}:{pid}", name=name, kind=kind,
        vendor_id=vid, product_id=pid, manufacturer="(unknown)",
        is_internal=False, state=DeviceState.NEW,
    )


def injection_intervals(count: int = 60, mean_ms: float = 4.0, jitter: float = 0.6):
    """Yield inter-keystroke intervals (seconds) that look like an injector:
    very fast, very regular — the timing signature DuckHound hunts for."""
    for _ in range(count):
        ms = max(0.4, random.gauss(mean_ms, jitter))
        yield ms / 1000.0


def human_intervals(count: int = 40):
    """Intervals for an ordinary fast human typist: slower and noisy."""
    for _ in range(count):
        ms = max(40.0, random.gauss(140.0, 55.0))
        yield ms / 1000.0
