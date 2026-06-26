"""Left navigation rail with brand mark and section buttons."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (QButtonGroup, QFrame, QLabel, QPushButton,
                               QVBoxLayout, QWidget)

from ... import __version__
from .. import icons
from ..theme import COLORS, rgba


class NavButton(QPushButton):
    def __init__(self, label: str, icon_name: str, parent=None) -> None:
        super().__init__(label, parent)
        self.icon_name = icon_name
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setIconSize(QSize(20, 20))
        self.setFixedHeight(46)
        self._refresh(False)
        self.toggled.connect(self._refresh)

    def _refresh(self, on: bool) -> None:
        col = COLORS["bg"] if on else COLORS["text_dim"]
        self.setIcon(icons.icon(self.icon_name, col, 20))
        if on:
            self.setStyleSheet(
                f"QPushButton{{text-align:left; padding-left:14px; border:none;"
                f"border-radius:12px; font-size:14px; font-weight:800;"
                f"color:{COLORS['bg']};"
                f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 {COLORS['accent']}, stop:1 #38BDF8);}}")
        else:
            self.setStyleSheet(
                f"QPushButton{{text-align:left; padding-left:14px; border:none;"
                f"border-radius:12px; font-size:14px; font-weight:600;"
                f"color:{COLORS['text_dim']}; background: transparent;}}"
                f"QPushButton:hover{{background:{COLORS['surface2']};"
                f"color:{COLORS['text']};}}")


class Sidebar(QFrame):
    navigate = Signal(int)

    SECTIONS = [
        ("Dashboard", "radar"),
        ("Protection", "shield"),
        ("Devices", "usb"),
        ("Threats", "alert"),
        ("Settings", "gear"),
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(232)
        self.setStyleSheet(
            f"background: {rgba('surface', 0.45)};"
            f"border-right: 1px solid {COLORS['glass_brd']};")

        # Brand.
        mark = QLabel()
        mark.setPixmap(icons.pixmap("shield", COLORS["accent"], 30))
        mark.setFixedSize(44, 44)
        mark.setAlignment(Qt.AlignCenter)
        mark.setStyleSheet(
            f"background: {rgba('accent', 0.10)};"
            f"border: 1px solid {rgba('accent', 0.28)}; border-radius: 13px;")
        name = QLabel("DuckHound")
        name.setStyleSheet("font-size:18px; font-weight:800;")
        sub = QLabel("USB DEFENSE")
        sub.setStyleSheet(
            f"color:{COLORS['accent']}; font-size:9px; font-weight:800;"
            f"letter-spacing:2px;")
        brand_txt = QVBoxLayout()
        brand_txt.setSpacing(0)
        brand_txt.addWidget(name)
        brand_txt.addWidget(sub)
        brand = QFrame()
        bl = QVBoxLayout(brand)
        bl.setContentsMargins(6, 4, 6, 4)
        bl.setSpacing(10)
        from PySide6.QtWidgets import QHBoxLayout
        h = QHBoxLayout()
        h.setSpacing(11)
        h.addWidget(mark)
        h.addLayout(brand_txt)
        h.addStretch(1)
        bl.addLayout(h)

        # Nav.
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        nav = QVBoxLayout()
        nav.setSpacing(6)
        for i, (label, ic) in enumerate(self.SECTIONS):
            btn = NavButton(label, ic)
            self.group.addButton(btn, i)
            nav.addWidget(btn)
            if i == 0:
                btn.setChecked(True)
        self.group.idClicked.connect(self.navigate.emit)

        # Footer.
        ver = QLabel(f"v{__version__}  ·  local-only")
        ver.setStyleSheet(f"color:{COLORS['text_faint']}; font-size:11px;")
        ver.setAlignment(Qt.AlignCenter)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 20, 16, 16)
        lay.setSpacing(18)
        lay.addWidget(brand)
        lay.addLayout(nav)
        lay.addStretch(1)
        lay.addWidget(ver)

    def select(self, index: int) -> None:
        btn = self.group.button(index)
        if btn:
            btn.setChecked(True)
