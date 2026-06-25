"""Slide-in alert banner shown when a threat fires."""
from __future__ import annotations

from PySide6.QtCore import (QEasingCurve, QPoint, QPropertyAnimation, Qt,
                            QTimer)
from PySide6.QtWidgets import (QGraphicsDropShadowEffect, QHBoxLayout, QFrame,
                               QLabel, QPushButton, QVBoxLayout)

from PySide6.QtGui import QColor

from .. import icons
from ..theme import COLORS, SEVERITY, rgba


class Toast(QFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setFixedWidth(360)
        self.setObjectName("Toast")
        self._host = parent

        self.icon = QLabel()
        self.icon.setFixedSize(38, 38)
        self.icon.setAlignment(Qt.AlignCenter)

        self.title = QLabel("Threat detected")
        self.title.setStyleSheet("font-size: 14px; font-weight: 800;")
        self.detail = QLabel("")
        self.detail.setWordWrap(True)
        self.detail.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")

        close = QPushButton("✕")
        close.setFixedSize(24, 24)
        close.setCursor(Qt.PointingHandCursor)
        close.setStyleSheet(
            "QPushButton{background:transparent;border:none;color:#7C8AA5;"
            "font-size:14px;} QPushButton:hover{color:#fff;}")
        close.clicked.connect(self.dismiss)

        text = QVBoxLayout()
        text.setSpacing(3)
        head = QHBoxLayout()
        head.addWidget(self.title, 1)
        head.addWidget(close)
        text.addLayout(head)
        text.addWidget(self.detail)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 12, 12)
        lay.setSpacing(12)
        lay.addWidget(self.icon, 0, Qt.AlignTop)
        lay.addLayout(text, 1)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 170))
        shadow.setOffset(0, 12)
        self.setGraphicsEffect(shadow)

        self._anim = QPropertyAnimation(self, b"pos", self)
        self._anim.setDuration(280)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.dismiss)
        self.hide()

    def popup(self, title: str, detail: str, severity: str = "critical") -> None:
        color = SEVERITY.get(severity, COLORS["critical"])
        self.setStyleSheet(
            f"#Toast {{ background: {COLORS['surface2']}; "
            f"border: 1px solid {rgba(color, 0.40)}; border-left: 4px solid {color};"
            f"border-radius: 14px; }}")
        self.icon.setPixmap(icons.pixmap("alert", color, 22))
        self.icon.setStyleSheet(
            f"background: {rgba(color, 0.12)}; border-radius: 11px;")
        self.title.setText(title)
        self.detail.setText(detail)
        self.adjustSize()
        self.show()
        self.raise_()
        self._reposition(animate=True)
        self._hide_timer.start(6000)

    def _reposition(self, animate: bool = False) -> None:
        if not self._host:
            return
        margin = 22
        x = self._host.width() - self.width() - margin
        y_to = margin + 6
        if animate:
            self.move(x, -self.height())
            self._anim.stop()
            self._anim.setStartValue(QPoint(x, -self.height()))
            self._anim.setEndValue(QPoint(x, y_to))
            self._anim.start()
        else:
            self.move(x, y_to)

    def dismiss(self) -> None:
        self._hide_timer.stop()
        self.hide()
