"""A single device entry with kind icon, identity and trust/block actions."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout)

from .. import icons
from ..theme import COLORS, STATE_COLOR, rgba
from .badge import state_badge

_KIND_ICON = {
    "keyboard": "chip", "mouse": "activity", "hid": "usb",
    "storage": "chip", "hub": "usb", "other": "usb",
}


class DeviceRow(QFrame):
    trust_requested = Signal(str)
    block_requested = Signal(str)
    untrust_requested = Signal(str)

    def __init__(self, device, parent=None) -> None:
        super().__init__(parent)
        self.device = device
        self.setProperty("card", "soft")
        self.setMinimumHeight(66)

        state = getattr(device.state, "value", "known")
        accent = STATE_COLOR.get(state, COLORS["accent"])

        icon = QLabel()
        icon.setPixmap(icons.pixmap(_KIND_ICON.get(
            getattr(device.kind, "value", "other"), "usb"), accent, 20))
        icon.setFixedSize(40, 40)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            f"background: {rgba(accent, 0.10)}; border: 1px solid {rgba(accent, 0.22)};"
            f"border-radius: 11px;")

        name = QLabel(device.name)
        name.setStyleSheet("font-size: 14px; font-weight: 700;")
        kind_txt = getattr(device.kind, "value", "device").title()
        meta = QLabel(f"{kind_txt}  ·  ID {device.vidpid}"
                      + (f"  ·  SN {device.serial[:10]}" if device.serial else ""))
        meta.setProperty("role", "muted")
        meta.setStyleSheet(f"color: {COLORS['text_faint']}; font-size: 12px;")

        info = QVBoxLayout()
        info.setSpacing(2)
        info.addWidget(name)
        info.addWidget(meta)

        self.badge = state_badge(state)

        self.trust_btn = QPushButton("Trust")
        self.trust_btn.setProperty("ghost", "true")
        self.trust_btn.setCursor(Qt.PointingHandCursor)
        self.trust_btn.clicked.connect(lambda: self.trust_requested.emit(device.key))

        self.block_btn = QPushButton("Block")
        self.block_btn.setProperty("danger", "true")
        self.block_btn.setCursor(Qt.PointingHandCursor)
        self.block_btn.clicked.connect(lambda: self.block_requested.emit(device.key))

        self.revoke_btn = QPushButton("Revoke trust")
        self.revoke_btn.setProperty("ghost", "true")
        self.revoke_btn.setCursor(Qt.PointingHandCursor)
        self.revoke_btn.clicked.connect(lambda: self.untrust_requested.emit(device.key))

        # Trusted devices show only "Revoke"; blocked show only "Trust";
        # everything else gets the usual Trust / Block pair.
        if state == "trusted":
            self.trust_btn.setVisible(False)
            self.block_btn.setVisible(False)
        elif state == "blocked":
            self.block_btn.setVisible(False)
            self.revoke_btn.setVisible(False)
        else:
            self.revoke_btn.setVisible(False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(12)
        lay.addWidget(icon)
        lay.addLayout(info, 1)
        lay.addWidget(self.badge)
        lay.addSpacing(4)
        lay.addWidget(self.trust_btn)
        lay.addWidget(self.block_btn)
        lay.addWidget(self.revoke_btn)
