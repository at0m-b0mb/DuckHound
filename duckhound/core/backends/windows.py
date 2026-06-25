"""Windows USB/HID enumeration via PowerShell CIM (no extra deps required).

Uses ``Get-PnpDevice`` over the USB + HID classes. If the optional ``wmi``
package is installed it could be swapped in, but PowerShell ships with Windows
so this works out of the box.
"""
from __future__ import annotations

import json
import re
import subprocess

from ..models import Device, DeviceKind
from .base import Backend

_PS = (
    "Get-PnpDevice -PresentOnly "
    "| Where-Object { $_.InstanceId -match 'USB|HID' } "
    "| Select-Object FriendlyName,Class,InstanceId,Manufacturer "
    "| ConvertTo-Json -Compress"
)


class WindowsBackend(Backend):
    name = "windows/pnp"
    supported = True

    def enumerate(self) -> list[Device]:
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS],
                capture_output=True, text=True, timeout=10,
            )
            raw = json.loads(out.stdout or "[]")
        except Exception:
            return []
        if isinstance(raw, dict):
            raw = [raw]

        devices: list[Device] = []
        for item in raw:
            name = (item.get("FriendlyName") or "USB Device").strip()
            cls = (item.get("Class") or "").strip()
            inst = item.get("InstanceId") or ""
            maker = (item.get("Manufacturer") or "").strip()
            vid, pid = _vidpid(inst)
            key = ":".join(p for p in (vid, pid) if p) or inst or name
            devices.append(Device(
                key=key, name=name, kind=_classify(name, cls),
                vendor_id=vid, product_id=pid, manufacturer=maker,
                is_internal=("ROOT_HUB" in inst.upper()),
            ))
        return devices


def _vidpid(instance_id: str) -> tuple[str, str]:
    vid = re.search(r"VID_([0-9A-Fa-f]{4})", instance_id or "")
    pid = re.search(r"PID_([0-9A-Fa-f]{4})", instance_id or "")
    return (vid.group(1).lower() if vid else "", pid.group(1).lower() if pid else "")


def _classify(name: str, cls: str) -> DeviceKind:
    n = f"{name} {cls}".lower()
    if "keyboard" in n:
        return DeviceKind.KEYBOARD
    if "mouse" in n or "pointing" in n:
        return DeviceKind.MOUSE
    if "disk" in n or "storage" in n:
        return DeviceKind.STORAGE
    if "hub" in n:
        return DeviceKind.HUB
    if "hid" in n:
        return DeviceKind.HID
    return DeviceKind.OTHER
