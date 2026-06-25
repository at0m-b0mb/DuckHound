"""Compact metric card: icon chip beside a big number + caption."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from .. import icons
from ..theme import COLORS, rgba


class StatCard(QFrame):
    def __init__(self, title: str, icon_name: str, accent: str = "accent",
                 parent=None) -> None:
        super().__init__(parent)
        self.setProperty("card", "soft")
        self.setMinimumHeight(96)
        accent_hex = COLORS.get(accent, accent)

        chip = QLabel()
        chip.setPixmap(icons.pixmap(icon_name, accent_hex, 22))
        chip.setFixedSize(46, 46)
        chip.setAlignment(Qt.AlignCenter)
        chip.setStyleSheet(
            f"background: {rgba(accent_hex, 0.10)}; border-radius: 13px;"
            f"border: 1px solid {rgba(accent_hex, 0.22)};")

        self.value_lbl = QLabel("—")
        self.value_lbl.setStyleSheet(
            f"color: {accent_hex}; font-size: 27px; font-weight: 800;")

        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet(
            f"color: {COLORS['text_dim']}; font-size: 11px; font-weight: 800;"
            f"letter-spacing: 1px;")

        self.sub_lbl = QLabel("")
        self.sub_lbl.setStyleSheet(
            f"color: {COLORS['text_faint']}; font-size: 11px;")

        text = QVBoxLayout()
        text.setSpacing(2)
        text.setContentsMargins(0, 0, 0, 0)
        text.addStretch(1)
        text.addWidget(self.value_lbl)
        text.addWidget(title_lbl)
        text.addWidget(self.sub_lbl)
        text.addStretch(1)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(13)
        lay.addWidget(chip, 0, Qt.AlignVCenter)
        lay.addLayout(text, 1)

    def set_value(self, value, sub: str = "") -> None:
        self.value_lbl.setText(str(value))
        self.sub_lbl.setText(sub)
