"""Protection page — the score, the checklist, and one-click fixes."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from .. import icons
from ..components.card import Card
from ..components.status_hero import ScoreRing
from ..theme import COLORS, rgba

_LEVEL_TEXT = {
    "protected": ("You're protected", "ok",
                  "Every safeguard is active. A Rubber Ducky or Flipper Zero is "
                  "detected the instant it connects and stopped before it can type."),
    "at_risk": ("Almost there", "warn",
                "Core defences are on, but finish the items below to be fully covered."),
    "exposed": ("Not protected yet", "critical",
                "Important safeguards are off. Fix the items below — it takes seconds."),
}


class ProtectionPage(QWidget):
    fix_requested = Signal(str)
    fix_all_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(16)

        title = QLabel("Protection")
        title.setProperty("role", "h1")
        self.subtitle = QLabel("How ready DuckHound is to stop an attack.")
        self.subtitle.setProperty("role", "muted")
        head = QVBoxLayout()
        head.setSpacing(2)
        head.addWidget(title)
        head.addWidget(self.subtitle)
        root.addLayout(head)

        # Score banner
        banner = QFrame()
        banner.setProperty("card", "true")
        self.ring = ScoreRing()
        self.level_lbl = QLabel("—")
        self.level_lbl.setStyleSheet("font-size:24px; font-weight:800;")
        self.level_sub = QLabel("")
        self.level_sub.setWordWrap(True)
        self.level_sub.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:13px;")
        self.fix_all = QPushButton("  Fix everything")
        self.fix_all.setProperty("accent", "true")
        self.fix_all.setCursor(Qt.PointingHandCursor)
        self.fix_all.setMinimumHeight(40)
        self.fix_all.setIcon(icons.icon("check", "#051018", 18))
        self.fix_all.clicked.connect(self.fix_all_requested.emit)
        txt = QVBoxLayout()
        txt.setSpacing(5)
        txt.addStretch(1)
        txt.addWidget(self.level_lbl)
        txt.addWidget(self.level_sub)
        txt.addWidget(self.fix_all, 0, Qt.AlignLeft)
        txt.addStretch(1)
        bl = QHBoxLayout(banner)
        bl.setContentsMargins(22, 18, 22, 18)
        bl.setSpacing(22)
        bl.addWidget(self.ring, 0, Qt.AlignVCenter)
        bl.addLayout(txt, 1)
        root.addWidget(banner)

        # Checklist
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

    def set_report(self, report) -> None:
        name, ckey, blurb = _LEVEL_TEXT[report.level]
        col = COLORS[ckey]
        self.ring.set(report.score, QColor(col))
        self.level_lbl.setText(name)
        self.level_lbl.setStyleSheet(f"font-size:24px; font-weight:800; color:{col};")
        self.level_sub.setText(blurb)
        self.fix_all.setVisible(report.level != "protected")
        self.subtitle.setText(
            f"{report.passing} of {len(report.checks)} safeguards active")

        while self.list_box.count():
            it = self.list_box.takeAt(0)
            if it.widget():
                it.widget().setParent(None)
        for chk in report.checks:
            self.list_box.addWidget(self._row(chk))

    def _row(self, chk) -> QFrame:
        col = COLORS["ok"] if chk.ok else COLORS["warn"]
        row = QFrame()
        row.setProperty("card", "soft")
        icon = QLabel("✓" if chk.ok else "!")
        icon.setFixedSize(34, 34)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            f"color:{col}; background:{rgba(col, 0.14)}; border-radius:10px;"
            f"font-size:16px; font-weight:800;")
        name = QLabel(chk.label)
        name.setStyleSheet("font-size:14px; font-weight:700;")
        detail = QLabel(chk.detail)
        detail.setWordWrap(True)
        detail.setStyleSheet(f"color:{COLORS['text_faint']}; font-size:12px;")
        txt = QVBoxLayout()
        txt.setSpacing(2)
        txt.addWidget(name)
        txt.addWidget(detail)
        lay = QHBoxLayout(row)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(12)
        lay.addWidget(icon, 0, Qt.AlignTop)
        lay.addLayout(txt, 1)
        if not chk.ok and chk.fixable:
            fix = QPushButton("Fix")
            fix.setProperty("accent", "true")
            fix.setCursor(Qt.PointingHandCursor)
            fix.clicked.connect(lambda: self.fix_requested.emit(chk.key))
            lay.addWidget(fix, 0, Qt.AlignVCenter)
        elif chk.ok:
            done = QLabel("Active")
            done.setStyleSheet(
                f"color:{COLORS['ok']}; font-size:11px; font-weight:700;"
                f"background:{rgba('ok', 0.12)}; border-radius:8px; padding:4px 10px;")
            lay.addWidget(done, 0, Qt.AlignVCenter)
        return row
