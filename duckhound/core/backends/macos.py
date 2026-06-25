"""macOS USB enumeration via ``system_profiler``.

No third-party deps: we shell out to ``system_profiler SPUSBDataType -json``,
which every Mac ships with, and walk the device tree.
"""
from __future__ import annotations

import json
import subprocess

from ..models import Device, DeviceKind
from .base import Backend


class MacBackend(Backend):
    name = "macos/system_profiler"
    supported = True

    def enumerate(self) -> list[Device]:
        try:
            out = subprocess.run(
                ["system_profiler", "SPUSBDataType", "-json"],
                capture_output=True, text=True, timeout=8,
            )
            data = json.loads(out.stdout or "{}")
        except Exception:
            return []

        devices: list[Device] = []
        self._walk(data.get("SPUSBDataType", []), devices)
        return devices

    def _walk(self, nodes, out: list[Device], depth: int = 0) -> None:
        for node in nodes or []:
            name = node.get("_name", "USB Device")
            vid = _hex(node.get("vendor_id"))
            pid = _hex(node.get("product_id"))
            serial = node.get("serial_num", "")
            maker = node.get("manufacturer", "")
            # Root hubs / controllers have no vendor id — skip as devices but
            # still descend into their children.
            if vid or pid or serial:
                key = ":".join(p for p in (vid, pid, serial) if p) or name
                devices_kind = _classify(name, node)
                out.append(Device(
                    key=key, name=name, kind=devices_kind,
                    vendor_id=vid, product_id=pid, serial=serial,
                    manufacturer=maker,
                    is_internal=_is_internal(name, maker),
                ))
            self._walk(node.get("_items"), out, depth + 1)


def _hex(v) -> str:
    if not v:
        return ""
    s = str(v).strip()
    if s.lower().startswith("0x"):
        return s[2:].lower().zfill(4)
    return s.lower()


def _classify(name: str, node: dict) -> DeviceKind:
    n = name.lower()
    if any(k in n for k in ("keyboard", "keypad")):
        return DeviceKind.KEYBOARD
    if any(k in n for k in ("mouse", "trackpad", "pointing")):
        return DeviceKind.MOUSE
    if any(k in n for k in ("storage", "disk", "flash", "sd card", "ssd")):
        return DeviceKind.STORAGE
    if "hub" in n:
        return DeviceKind.HUB
    if any(k in n for k in ("hid", "receiver", "input")):
        return DeviceKind.HID
    return DeviceKind.OTHER


def _is_internal(name: str, maker: str) -> bool:
    blob = f"{name} {maker}".lower()
    return "apple" in blob and any(
        k in blob for k in ("internal", "keyboard", "trackpad", "t2", "bridge")
    )
