"""Linux USB enumeration via sysfs (``/sys/bus/usb/devices``).

Pure sysfs reads — no root, no pyudev required (though pyudev, if present, can
drive real-time hotplug events in a future revision). Returns one Device per
USB node that advertises a vendor id.
"""
from __future__ import annotations

from pathlib import Path

from ..models import Device, DeviceKind
from .base import Backend

SYS_USB = Path("/sys/bus/usb/devices")


class LinuxBackend(Backend):
    name = "linux/sysfs"
    supported = True

    def enumerate(self) -> list[Device]:
        if not SYS_USB.exists():
            return []
        devices: list[Device] = []
        for node in sorted(SYS_USB.iterdir()):
            vid = _read(node / "idVendor")
            pid = _read(node / "idProduct")
            if not vid and not pid:
                continue
            name = _read(node / "product") or f"USB {vid}:{pid}"
            serial = _read(node / "serial")
            maker = _read(node / "manufacturer")
            key = ":".join(p for p in (vid, pid, serial) if p) or node.name
            devices.append(Device(
                key=key, name=name, kind=_classify(node, name),
                vendor_id=vid, product_id=pid, serial=serial, manufacturer=maker,
                is_internal=("usb1" in node.name or "1-0" in node.name),
            ))
        return devices


def _read(p: Path) -> str:
    try:
        return p.read_text().strip()
    except Exception:
        return ""


def _classify(node: Path, name: str) -> DeviceKind:
    n = name.lower()
    # Inspect interface descriptors for HID / keyboard protocol.
    try:
        for iface in node.glob(f"{node.name}:*"):
            cls = _read(iface / "bInterfaceClass")
            proto = _read(iface / "bInterfaceProtocol")
            if cls == "03":  # HID
                if proto == "01":
                    return DeviceKind.KEYBOARD
                if proto == "02":
                    return DeviceKind.MOUSE
                return DeviceKind.HID
            if cls == "08":  # Mass storage
                return DeviceKind.STORAGE
            if cls == "09":  # Hub
                return DeviceKind.HUB
    except Exception:
        pass
    if "keyboard" in n:
        return DeviceKind.KEYBOARD
    if "mouse" in n:
        return DeviceKind.MOUSE
    if "hub" in n:
        return DeviceKind.HUB
    return DeviceKind.OTHER
