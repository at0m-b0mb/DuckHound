"""Animated SOC-style radar — the dashboard centrepiece.

A rotating sweep over concentric rings, with a blip for every connected device
and an expanding red 'ping' whenever a threat fires. The sweep accelerates and
reddens as the live threat level climbs, so the screen *feels* the attack.
"""
from __future__ import annotations

import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QColor, QConicalGradient, QPainter, QPainterPath,
                           QPen, QRadialGradient)
from PySide6.QtWidgets import QWidget

from ..theme import COLORS


class Radar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self._angle = 0.0
        self._level = 0.0
        self._blips: dict[str, dict] = {}
        self._pings: list[dict] = []
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    # -- public API ----------------------------------------------------- #
    def set_level(self, level: float) -> None:
        self._level = max(0.0, min(100.0, level))

    def set_devices(self, devices) -> None:
        keys = set()
        for d in devices:
            keys.add(d.key)
            b = self._blips.get(d.key)
            ang, rad = _placement(d.key)
            color = {
                "blocked": COLORS["critical"], "suspect": COLORS["warn"],
                "new": COLORS["warn"], "trusted": COLORS["ok"],
            }.get(getattr(d.state, "value", "known"), COLORS["accent"])
            if b is None:
                self._blips[d.key] = {"ang": ang, "rad": rad, "color": color,
                                      "name": d.name}
            else:
                b["color"] = color
        for k in list(self._blips):
            if k not in keys:
                self._blips.pop(k, None)

    def ping(self, critical: bool = True) -> None:
        self._pings.append({"t": time.monotonic(),
                            "color": COLORS["critical"] if critical else COLORS["accent"]})

    # -- animation ------------------------------------------------------ #
    def _tick(self) -> None:
        speed = 2.2 + (self._level / 100.0) * 7.0
        self._angle = (self._angle + speed) % 360
        now = time.monotonic()
        self._pings = [p for p in self._pings if now - p["t"] < 1.4]
        self.update()

    # -- paint ---------------------------------------------------------- #
    def paintEvent(self, _ev) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        side = min(w, h)
        cx, cy = w / 2.0, h / 2.0
        R = side / 2.0 - 10
        center = QPointF(cx, cy)

        # Backdrop glow.
        bg = QRadialGradient(center, R)
        hot = self._level / 100.0
        bg.setColorAt(0.0, QColor(20 + int(40 * hot), 30, 44))
        bg.setColorAt(1.0, QColor(COLORS["bg_grad_b"]))
        p.setBrush(bg)
        p.setPen(Qt.NoPen)
        p.drawEllipse(center, R, R)

        circle = QPainterPath()
        circle.addEllipse(center, R, R)
        p.save()
        p.setClipPath(circle)

        # Rings + cross.
        ring_pen = QPen(QColor(255, 255, 255, 16), 1.0)
        p.setPen(ring_pen)
        p.setBrush(Qt.NoBrush)
        for i in range(1, 5):
            r = R * i / 4.0
            p.drawEllipse(center, r, r)
        p.drawLine(QPointF(cx - R, cy), QPointF(cx + R, cy))
        p.drawLine(QPointF(cx, cy - R), QPointF(cx, cy + R))

        # Sweep wedge.
        sweep_col = _mix(QColor(COLORS["accent"]), QColor(COLORS["critical"]), hot)
        grad = QConicalGradient(center, -self._angle)
        c0 = QColor(sweep_col); c0.setAlpha(0)
        c1 = QColor(sweep_col); c1.setAlpha(160)
        grad.setColorAt(0.0, c1)
        grad.setColorAt(0.18, QColor(sweep_col.red(), sweep_col.green(), sweep_col.blue(), 30))
        grad.setColorAt(0.30, c0)
        grad.setColorAt(1.0, c0)
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(center, R, R)

        # Leading edge line.
        rad = math.radians(self._angle)
        edge = QPointF(cx + R * math.cos(rad), cy - R * math.sin(rad))
        lp = QPen(QColor(sweep_col.red(), sweep_col.green(), sweep_col.blue(), 220), 1.6)
        p.setPen(lp)
        p.drawLine(center, edge)

        # Threat ping rings.
        now = time.monotonic()
        for ping in self._pings:
            t = (now - ping["t"]) / 1.4
            pr = R * t
            col = QColor(ping["color"]); col.setAlpha(int(180 * (1 - t)))
            p.setPen(QPen(col, 2.0))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(center, pr, pr)

        # Device blips, brightened as the sweep passes them.
        for b in self._blips.values():
            ang = b["ang"]
            br = R * b["rad"]
            bx = cx + br * math.cos(math.radians(ang))
            by = cy - br * math.sin(math.radians(ang))
            delta = (self._angle - ang) % 360
            glow = max(0.0, 1.0 - delta / 70.0) if delta < 70 else 0.0
            base = QColor(b["color"])
            dot = QColor(base)
            dot.setAlpha(120 + int(135 * glow))
            if glow > 0.05:
                halo = QColor(base); halo.setAlpha(int(70 * glow))
                p.setBrush(halo); p.setPen(Qt.NoPen)
                p.drawEllipse(QPointF(bx, by), 9, 9)
            p.setBrush(dot); p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(bx, by), 3.4, 3.4)

        p.restore()

        # Center hub.
        hub = QColor(COLORS["accent"]) if hot < 0.5 else _mix(
            QColor(COLORS["accent"]), QColor(COLORS["critical"]), hot)
        p.setBrush(QColor(hub.red(), hub.green(), hub.blue(), 60))
        p.setPen(Qt.NoPen)
        p.drawEllipse(center, 7, 7)
        p.setBrush(hub)
        p.drawEllipse(center, 3, 3)
        p.end()


def _placement(key: str):
    h = abs(hash(key))
    ang = h % 360
    rad = 0.30 + ((h // 360) % 1000) / 1000.0 * 0.6
    return ang, rad


def _mix(a: QColor, b: QColor, t: float) -> QColor:
    t = max(0.0, min(1.0, t))
    return QColor(
        int(a.red() + (b.red() - a.red()) * t),
        int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t),
    )
