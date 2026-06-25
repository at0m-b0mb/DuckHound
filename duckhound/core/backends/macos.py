"""macOS device enumeration.

Primary path is ``ioreg`` over the **IOHIDInterface** class: it's fast (~20ms),
needs no permission, and — unlike ``system_profiler SPUSBDataType`` — reliably
reports HID keyboards on Apple Silicon, classifying them by their HID usage page.
This is what lets DuckHound spot a Rubber Ducky the instant it enumerates.

Falls back to ``system_profiler`` only if ``ioreg`` yields nothing.
"""
from __future__ import annotations

import json
import plistlib
import subprocess

from ..models import Device, DeviceKind
from .base import Backend

# HID Generic-Desktop usage page (0x01) usages we care about.
_KEYBOARD_USAGES = {6, 7}   # keyboard, keypad
_MOUSE_USAGES = {2}         # mouse
_INTERNAL_TRANSPORTS = {"FIFO", "SPI", "SPMI", "IOHIDFIFO"}


class MacBackend(Backend):
    name = "macos/ioreg-hid"
    supported = True

    def enumerate(self) -> list[Device]:
        devices = self._via_ioreg()
        if devices:
            return devices
        return self._via_system_profiler()

    # ------------------------------------------------------------------ #
    def _via_ioreg(self) -> list[Device]:
        try:
            out = subprocess.run(
                ["ioreg", "-a", "-r", "-c", "IOHIDInterface", "-d", "1"],
                capture_output=True, timeout=6)
            entries = plistlib.loads(out.stdout) if out.stdout else []
        except Exception:
            return []

        agg: dict[str, dict] = {}
        for e in entries or []:
            if e.get("PrimaryUsagePage") != 1:
                continue
            usage = e.get("PrimaryUsage")
            if usage not in _KEYBOARD_USAGES and usage not in _MOUSE_USAGES:
                continue
            vid, pid = e.get("VendorID"), e.get("ProductID")
            vidhex = f"{vid:04x}" if isinstance(vid, int) else ""
            pidhex = f"{pid:04x}" if isinstance(pid, int) else ""
            name = e.get("Product") or "Input Device"
            transport = (e.get("Transport") or "").upper()
            key = f"{vidhex}:{pidhex}" if vidhex and pidhex else name
            a = agg.setdefault(key, {
                "name": name, "vid": vidhex, "pid": pidhex,
                "transport": transport, "kbd": False, "mouse": False})
            if usage in _KEYBOARD_USAGES:
                a["kbd"] = True
            if usage in _MOUSE_USAGES:
                a["mouse"] = True

        devices = []
        for key, a in agg.items():
            internal = (a["transport"] in _INTERNAL_TRANSPORTS
                        or a["vid"] == "05ac"
                        or "internal" in a["name"].lower())
            kind = (DeviceKind.KEYBOARD if a["kbd"]
                    else DeviceKind.MOUSE if a["mouse"] else DeviceKind.HID)
            devices.append(Device(
                key=key, name=a["name"], kind=kind,
                vendor_id=a["vid"], product_id=a["pid"], is_internal=internal))
        return devices

    # ------------------------------------------------------------------ #
    def _via_system_profiler(self) -> list[Device]:
        try:
            out = subprocess.run(
                ["system_profiler", "SPUSBDataType", "-json"],
                capture_output=True, text=True, timeout=8)
            data = json.loads(out.stdout or "{}")
        except Exception:
            return []
        devices: list[Device] = []
        self._walk(data.get("SPUSBDataType", []), devices)
        return devices

    def _walk(self, nodes, out: list[Device]) -> None:
        for node in nodes or []:
            name = node.get("_name", "USB Device")
            vid = _hex(node.get("vendor_id"))
            pid = _hex(node.get("product_id"))
            serial = node.get("serial_num", "")
            if vid or pid or serial:
                key = ":".join(p for p in (vid, pid) if p) or name
                out.append(Device(
                    key=key, name=name, kind=_classify(name),
                    vendor_id=vid, product_id=pid, serial=serial,
                    manufacturer=node.get("manufacturer", ""),
                    is_internal="apple" in f"{name}".lower()))
            self._walk(node.get("_items"), out)


def _hex(v) -> str:
    if not v:
        return ""
    s = str(v).strip()
    return s[2:].lower().zfill(4) if s.lower().startswith("0x") else s.lower()


def _classify(name: str) -> DeviceKind:
    n = name.lower()
    if "keyboard" in n or "keypad" in n:
        return DeviceKind.KEYBOARD
    if "mouse" in n or "trackpad" in n:
        return DeviceKind.MOUSE
    if "storage" in n or "flash" in n or "disk" in n:
        return DeviceKind.STORAGE
    if "hub" in n:
        return DeviceKind.HUB
    return DeviceKind.OTHER
