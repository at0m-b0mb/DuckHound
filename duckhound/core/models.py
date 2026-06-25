"""Shared data models for devices and threat events."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        return {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}[self.value]


class DeviceState(str, Enum):
    TRUSTED = "trusted"      # user-approved
    KNOWN = "known"          # seen before, allowed
    NEW = "new"              # just appeared, watching
    SUSPECT = "suspect"      # behaving oddly
    BLOCKED = "blocked"      # neutralized


class DeviceKind(str, Enum):
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    HID = "hid"
    STORAGE = "storage"
    HUB = "hub"
    OTHER = "other"


@dataclass
class Device:
    key: str                          # stable identity (vid:pid:serial or name)
    name: str
    kind: DeviceKind = DeviceKind.OTHER
    vendor_id: str = ""
    product_id: str = ""
    serial: str = ""
    manufacturer: str = ""
    is_internal: bool = False
    state: DeviceState = DeviceState.NEW
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)

    @property
    def vidpid(self) -> str:
        if self.vendor_id and self.product_id:
            return f"{self.vendor_id}:{self.product_id}"
        return "—"

    @property
    def is_input(self) -> bool:
        return self.kind in (DeviceKind.KEYBOARD, DeviceKind.HID)


@dataclass
class ThreatEvent:
    title: str
    detail: str
    severity: Severity = Severity.MEDIUM
    score: int = 0                    # 0-100 confidence
    device_key: str = ""
    device_name: str = ""
    metrics: dict = field(default_factory=dict)  # cps, cv, run_len, etc.
    actions: list[str] = field(default_factory=list)  # responses taken
    timestamp: float = field(default_factory=time.time)

    @property
    def time_str(self) -> str:
        return time.strftime("%H:%M:%S", time.localtime(self.timestamp))
