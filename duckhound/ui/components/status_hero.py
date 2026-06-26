"""The dashboard's status hero — protection score ring + state + key actions."""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout, QWidget)

from .. import icons
from ..theme import COLORS, rgba

_LEVEL = {
    "protected": ("PROTECTED", "ok"),
    "at_risk":   ("AT RISK", "warn"),
    "exposed":   ("EXPOSED", "critical"),
    "attack":    ("UNDER ATTACK", "critical"),
}


class ScoreRing(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(150, 150)
        self._target = 0.0
        self._value = 0.0
        self._color = QColor(COLORS["ok"])
        self._timer = QTimer(self)
        self._timer.setInterval(24)
        self._timer.timeout.connect(self._ease)
        self._timer.start()

    def set(self, score: float, color: QColor) -> None:
        self._target = max(0.0, min(100.0, score))
        self._color = color

    def _ease(self) -> None:
        if abs(self._value - self._target) < 0.4:
            self._value = self._target
        else:
            self._value += (self._target - self._value) * 0.16
        self.update()

    def paintEvent(self, _ev) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        m = 12
        rect = QRectF(m, m, self.width() - 2 * m, self.height() - 2 * m)
        p.setPen(QPen(QColor(COLORS["surface3"]), 11, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 90 * 16, -360 * 16)
        # glow + value arc
        glow = QColor(self._color); glow.setAlpha(60)
        p.setPen(QPen(glow, 15, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 90 * 16, int(-360 * 16 * self._value / 100))
        p.setPen(QPen(self._color, 11, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 90 * 16, int(-360 * 16 * self._value / 100))
        p.setPen(QColor(COLORS["text"]))
        f = QFont(); f.setPointSize(33); f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(rect.left(), rect.center().y() - 32, rect.width(), 48),
                   Qt.AlignCenter, f"{int(round(self._value))}")
        p.setPen(QColor(COLORS["text_faint"]))
        f2 = QFont(); f2.setPointSize(8); f2.setBold(True)
        f2.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        p.setFont(f2)
        p.drawText(QRectF(rect.left(), rect.center().y() + 12, rect.width(), 20),
                   Qt.AlignCenter, "SCORE")
        p.end()


class StatusHero(QFrame):
    toggle_monitor = Signal()
    panic_lock = Signal()
    open_protection = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("card", "true")
        self.setMinimumHeight(168)
        self._attack = False
        self._level = "exposed"

        self.ring = ScoreRing()

        self.state_lbl = QLabel("EXPOSED")
        self.state_lbl.setStyleSheet("font-size:30px; font-weight:800;")
        self.sub_lbl = QLabel("Checking protection…")
        self.sub_lbl.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:13px;")
        self.chips = QHBoxLayout()
        self.chips.setSpacing(7)
        self.chips.setContentsMargins(0, 4, 0, 0)
        chips_row = QHBoxLayout()
        chips_row.addLayout(self.chips)
        chips_row.addStretch(1)

        mid = QVBoxLayout()
        mid.setSpacing(4)
        mid.addStretch(1)
        mid.addWidget(self.state_lbl)
        mid.addWidget(self.sub_lbl)
        mid.addLayout(chips_row)
        mid.addStretch(1)

        self.arm_btn = QPushButton("  Arm")
        self.arm_btn.setProperty("accent", "true")
        self.arm_btn.setCursor(Qt.PointingHandCursor)
        self.arm_btn.setMinimumHeight(42)
        self.arm_btn.setIcon(icons.icon("power", "#051018", 18))
        self.arm_btn.clicked.connect(self.toggle_monitor.emit)

        self.panic_btn = QPushButton("  Lock Now")
        self.panic_btn.setProperty("danger", "true")
        self.panic_btn.setCursor(Qt.PointingHandCursor)
        self.panic_btn.setMinimumHeight(42)
        self.panic_btn.setIcon(icons.icon("lock", COLORS["danger"], 18))
        self.panic_btn.clicked.connect(self.panic_lock.emit)

        self.fix_btn = QPushButton("Finish setup")
        self.fix_btn.setProperty("ghost", "true")
        self.fix_btn.setCursor(Qt.PointingHandCursor)
        self.fix_btn.clicked.connect(self.open_protection.emit)

        actions = QVBoxLayout()
        actions.setSpacing(8)
        actions.addStretch(1)
        actions.addWidget(self.arm_btn)
        actions.addWidget(self.panic_btn)
        actions.addWidget(self.fix_btn)
        actions.addStretch(1)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(22, 16, 22, 16)
        lay.setSpacing(22)
        lay.addWidget(self.ring, 0, Qt.AlignVCenter)
        lay.addLayout(mid, 1)
        lay.addLayout(actions, 0)

    # -- updates -------------------------------------------------------- #
    def set_report(self, report) -> None:
        self._level = report.level
        self._refresh(report)

    def set_monitoring(self, on: bool) -> None:
        self.arm_btn.setText("  Pause" if on else "  Arm")
        self.arm_btn.setProperty("accent", None if on else "true")
        self.arm_btn.setProperty("ghost", "true" if on else None)
        self.arm_btn.setIcon(icons.icon(
            "power", COLORS["text"] if on else "#051018", 18))
        self.arm_btn.style().unpolish(self.arm_btn)
        self.arm_btn.style().polish(self.arm_btn)

    def flash_attack(self, on: bool) -> None:
        self._attack = on
        self.state_lbl.setText("UNDER ATTACK" if on else _LEVEL[self._level][0])
        col = COLORS["critical"] if on else COLORS[_LEVEL[self._level][1]]
        self.state_lbl.setStyleSheet(
            f"font-size:30px; font-weight:800; color:{col};")

    def _refresh(self, report) -> None:
        name, ckey = _LEVEL["attack" if self._attack else report.level]
        col = COLORS[ckey]
        self.fix_btn.setVisible(report.level != "protected")
        self.ring.set(report.score, QColor(col))
        self.state_lbl.setText(name)
        self.state_lbl.setStyleSheet(f"font-size:30px; font-weight:800; color:{col};")
        if report.level == "protected":
            self.sub_lbl.setText(f"All {len(report.checks)} safeguards active — "
                                 "a Ducky / Flipper gets stopped on sight.")
        else:
            self.sub_lbl.setText(
                f"{report.passing} of {len(report.checks)} safeguards active — "
                "finish setup to be fully protected.")
        # rebuild chips
        while self.chips.count():
            it = self.chips.takeAt(0)
            if it.widget():
                it.widget().setParent(None)
        for chk in report.checks:
            self.chips.addWidget(_chip(chk.label, chk.ok))


def _chip(label: str, ok: bool) -> QLabel:
    col = COLORS["ok"] if ok else COLORS["text_faint"]
    mark = "✓" if ok else "✗"
    short = label.split(" ")[0] if " " in label else label
    lbl = QLabel(f"{mark} {short}")
    lbl.setToolTip(label)
    lbl.setStyleSheet(
        f"color:{col}; background:{rgba(col, 0.12)}; border-radius:8px;"
        f"padding:3px 8px; font-size:10px; font-weight:700;")
    return lbl
