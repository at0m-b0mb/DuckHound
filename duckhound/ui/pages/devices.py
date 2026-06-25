"""Devices page — every connected device with trust/block controls."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QLabel, QScrollArea, QVBoxLayout, QWidget)

from ..components.device_row import DeviceRow
from ..theme import COLORS


class DevicesPage(QWidget):
    trust_requested = Signal(str)
    block_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(16)

        title = QLabel("Connected Devices")
        title.setProperty("role", "h1")
        self.subtitle = QLabel("Watching the USB bus…")
        self.subtitle.setProperty("role", "muted")
        head = QVBoxLayout()
        head.setSpacing(2)
        head.addWidget(title)
        head.addWidget(self.subtitle)
        root.addLayout(head)

        self.list_box = QVBoxLayout()
        self.list_box.setSpacing(10)
        self.list_box.setAlignment(Qt.AlignTop)

        container = QWidget()
        container.setLayout(self.list_box)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(scroll, 1)

        self.empty = QLabel(
            "No external devices detected yet.\n"
            "Plug something in — DuckHound will profile it instantly.")
        self.empty.setAlignment(Qt.AlignCenter)
        self.empty.setStyleSheet(
            f"color:{COLORS['text_faint']}; font-size:14px; padding:40px;")
        self.list_box.addWidget(self.empty)

    def set_devices(self, devices) -> None:
        # Clear current rows.
        while self.list_box.count():
            item = self.list_box.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if not devices:
            self.list_box.addWidget(self.empty)
            self.subtitle.setText("No external devices detected")
            return

        ext = sum(1 for d in devices if not d.is_internal)
        kbd = sum(1 for d in devices if getattr(d.kind, "value", "") == "keyboard")
        self.subtitle.setText(
            f"{len(devices)} device(s) · {ext} external · {kbd} keyboard(s)")
        for d in devices:
            row = DeviceRow(d)
            row.trust_requested.connect(self.trust_requested.emit)
            row.block_requested.connect(self.block_requested.emit)
            self.list_box.addWidget(row)
