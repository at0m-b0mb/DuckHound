"""Arc gauge showing the live threat level (0-100) with smooth easing."""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ..theme import COLORS


class ThreatMeter(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(180, 150)
        self._target = 0.0
        self._value = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(24)
        self._timer.timeout.connect(self._ease)
        self._timer.start()

    def set_value(self, v: float) -> None:
        self._target = max(0.0, min(100.0, v))

    def _ease(self) -> None:
        if abs(self._value - self._target) < 0.4:
            self._value = self._target
        else:
            self._value += (self._target - self._value) * 0.18
            self.update()

    def _color(self) -> QColor:
        v = self._value
        if v < 30:
            return QColor(COLORS["ok"])
        if v < 60:
            return QColor(COLORS["warn"])
        if v < 80:
            return QColor("#FB923C")
        return QColor(COLORS["critical"])

    def _label(self) -> str:
        v = self._value
        if v < 12:
            return "SECURE"
        if v < 30:
            return "WATCHING"
        if v < 60:
            return "ELEVATED"
        if v < 80:
            return "HIGH"
        return "CRITICAL"

    def paintEvent(self, _ev) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        side = min(w, h * 1.25)
        m = 16
        rect = QRectF((w - side) / 2 + m, h - side + m,
                      side - 2 * m, side - 2 * m)
        start, span = 220 * 16, -260 * 16

        # Track.
        p.setPen(QPen(QColor(COLORS["surface3"]), 12, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, start, span)

        # Value arc.
        frac = self._value / 100.0
        p.setPen(QPen(self._color(), 12, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, start, int(span * frac))

        # Numeral.
        p.setPen(QColor(COLORS["text"]))
        f = QFont(); f.setPointSize(30); f.setBold(True)
        p.setFont(f)
        num_rect = QRectF(rect.left(), rect.center().y() - 34, rect.width(), 46)
        p.drawText(num_rect, Qt.AlignCenter, f"{int(round(self._value))}")

        # Status word.
        p.setPen(self._color())
        f2 = QFont(); f2.setPointSize(10); f2.setBold(True)
        f2.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        p.setFont(f2)
        lab_rect = QRectF(rect.left(), rect.center().y() + 6, rect.width(), 22)
        p.drawText(lab_rect, Qt.AlignCenter, self._label())
        p.end()
