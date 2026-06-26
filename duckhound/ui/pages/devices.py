"""Devices page — connected devices + the persistent allow-list."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from .. import icons
from ..components.card import Card
from ..components.device_row import DeviceRow
from ..theme import COLORS, rgba


class DevicesPage(QWidget):
    trust_requested = Signal(str)
    block_requested = Signal(str)
    untrust_requested = Signal(str)
    trust_all_requested = Signal()

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

        # --- Allow-list card -------------------------------------------- #
        self.allow_card = Card("Allow-list", "shield", "ok")
        trust_all = QPushButton("  Trust all connected")
        trust_all.setProperty("accent", "true")
        trust_all.setCursor(Qt.PointingHandCursor)
        trust_all.setIcon(icons.icon("check", "#04222B", 16))
        trust_all.clicked.connect(self.trust_all_requested.emit)
        self.allow_card.add_header_widget(trust_all)

        self.allow_box = QVBoxLayout()
        self.allow_box.setSpacing(8)
        self.allow_card.add(self.allow_box)
        root.addWidget(self.allow_card)
        self.set_allowlist([])

        # --- Connected devices list ------------------------------------- #
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

    # ------------------------------------------------------------------ #
    def set_allowlist(self, items) -> None:
        while self.allow_box.count():
            it = self.allow_box.takeAt(0)
            if it.widget():
                it.widget().setParent(None)
        if not items:
            hint = QLabel(
                "No devices trusted yet. Approve your real keyboards once so "
                "only unknown devices ever trigger a lock.")
            hint.setWordWrap(True)
            hint.setStyleSheet(f"color:{COLORS['text_faint']}; font-size:12px;")
            self.allow_box.addWidget(hint)
            return
        for key, label in items:
            self.allow_box.addWidget(self._allow_row(key, label))

    def _allow_row(self, key: str, label: str) -> QFrame:
        ok = COLORS["ok"]
        row = QFrame()
        row.setStyleSheet(
            f"background:{rgba(ok, 0.07)}; border:1px solid {rgba(ok, 0.22)};"
            f"border-radius:10px;")
        dot = QLabel("✓")
        dot.setStyleSheet(f"color:{ok}; font-weight:800;")
        name = QLabel(label)
        name.setStyleSheet("font-size:13px; font-weight:700;")
        kid = QLabel(key)
        kid.setStyleSheet(f"color:{COLORS['text_faint']}; font-size:11px;")
        txt = QVBoxLayout()
        txt.setSpacing(0)
        txt.addWidget(name)
        txt.addWidget(kid)
        revoke = QPushButton("Revoke")
        revoke.setProperty("ghost", "true")
        revoke.setCursor(Qt.PointingHandCursor)
        revoke.clicked.connect(lambda: self.untrust_requested.emit(key))
        lay = QHBoxLayout(row)
        lay.setContentsMargins(12, 7, 10, 7)
        lay.setSpacing(10)
        lay.addWidget(dot)
        lay.addLayout(txt, 1)
        lay.addWidget(revoke)
        return row

    def set_devices(self, devices) -> None:
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
            row.untrust_requested.connect(self.untrust_requested.emit)
            self.list_box.addWidget(row)
