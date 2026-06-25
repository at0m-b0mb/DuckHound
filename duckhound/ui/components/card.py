"""A titled card container with an optional icon and header-right slot."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QVBoxLayout,
                               QWidget)

from .. import icons
from ..theme import COLORS


class Card(QFrame):
    def __init__(self, title: str = "", icon_name: str = "",
                 accent: str = "accent", parent=None) -> None:
        super().__init__(parent)
        self.setProperty("card", "true")
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(18, 16, 18, 18)
        self._lay.setSpacing(14)

        self.header = QHBoxLayout()
        self.header.setSpacing(10)
        if icon_name:
            chip = QLabel()
            chip.setPixmap(icons.pixmap(icon_name, COLORS.get(accent, accent), 18))
            chip.setAlignment(Qt.AlignCenter)
            self.header.addWidget(chip)
        if title:
            lbl = QLabel(title)
            lbl.setProperty("role", "h2")
            self.header.addWidget(lbl)
        self.header.addStretch(1)
        if title or icon_name:
            self._lay.addLayout(self.header)

    def add_header_widget(self, w: QWidget) -> None:
        self.header.addWidget(w)

    def body(self) -> QVBoxLayout:
        return self._lay

    def add(self, w) -> None:
        if isinstance(w, QWidget):
            self._lay.addWidget(w)
        else:
            self._lay.addLayout(w)
