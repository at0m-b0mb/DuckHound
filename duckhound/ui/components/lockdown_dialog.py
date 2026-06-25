"""Mouse-only modal shown while the keyboard is frozen by Lockdown mode."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QDialog, QGraphicsDropShadowEffect, QHBoxLayout,
                               QFrame, QLabel, QPushButton, QVBoxLayout)
from PySide6.QtGui import QColor

from .. import icons
from ..theme import COLORS, rgba


class LockdownDialog(QDialog):
    approved = Signal()
    blocked = Signal()
    force_unlock = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        crit = COLORS["critical"]
        panel = QFrame(self)
        panel.setObjectName("Panel")
        panel.setStyleSheet(
            f"#Panel{{background:{COLORS['surface']};"
            f"border:1px solid {rgba(crit, 0.55)};"
            f"border-top:4px solid {crit}; border-radius:18px;}}")
        panel.setFixedWidth(440)
        shadow = QGraphicsDropShadowEffect(panel)
        shadow.setBlurRadius(60)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 18)
        panel.setGraphicsEffect(shadow)

        icon = QLabel()
        icon.setPixmap(icons.pixmap("lock", crit, 30))
        icon.setFixedSize(56, 56)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"background:{rgba(crit, 0.14)}; border-radius:16px;")

        title = QLabel("KEYBOARD LOCKDOWN")
        title.setStyleSheet(
            f"color:{crit}; font-size:20px; font-weight:800; letter-spacing:1px;")

        self.body = QLabel()
        self.body.setWordWrap(True)
        self.body.setStyleSheet(
            f"color:{COLORS['text_dim']}; font-size:13px; line-height:1.5;")

        self.btn_approve = QPushButton("  It's mine — Approve")
        self.btn_approve.setProperty("accent", "true")
        self.btn_approve.setCursor(Qt.PointingHandCursor)
        self.btn_approve.setIcon(icons.icon("check", "#04222B", 18))
        self.btn_approve.clicked.connect(self.approved.emit)

        self.btn_block = QPushButton("  Block it")
        self.btn_block.setProperty("danger", "true")
        self.btn_block.setCursor(Qt.PointingHandCursor)
        self.btn_block.setIcon(icons.icon("x", crit, 18))
        self.btn_block.clicked.connect(self.blocked.emit)

        self.btn_unlock = QPushButton("Force unlock")
        self.btn_unlock.setProperty("ghost", "true")
        self.btn_unlock.setCursor(Qt.PointingHandCursor)
        self.btn_unlock.clicked.connect(self.force_unlock.emit)
        self.btn_unlock.setVisible(False)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        btns.addWidget(self.btn_approve, 1)
        btns.addWidget(self.btn_block, 1)
        btns.addWidget(self.btn_unlock, 1)

        lay = QVBoxLayout(panel)
        lay.setContentsMargins(26, 24, 26, 24)
        lay.setSpacing(14)
        top = QHBoxLayout()
        top.setSpacing(14)
        top.addWidget(icon)
        head = QVBoxLayout()
        head.setSpacing(2)
        head.addWidget(title)
        hint = QLabel("Use your mouse — typing is frozen")
        hint.setStyleSheet(f"color:{COLORS['text_faint']}; font-size:12px;")
        head.addWidget(hint)
        top.addLayout(head, 1)
        lay.addLayout(top)
        lay.addWidget(self.body)
        lay.addLayout(btns)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(panel)

    def prompt(self, device_name: str, reason: str) -> None:
        self.btn_approve.setVisible(True)
        self.btn_block.setVisible(True)
        self.btn_unlock.setVisible(False)
        self.body.setText(
            f"<b style='color:{COLORS['text']};'>{reason}.</b><br><br>"
            f"DuckHound froze <b>all keyboard input</b> because "
            f"<b>{device_name}</b> behaves like a BadUSB / Rubber Ducky. "
            "Approve it only if you just plugged in this keyboard yourself.")
        self._center()
        self.show()
        self.raise_()

    def show_blocked(self, device_name: str) -> None:
        self.btn_approve.setVisible(False)
        self.btn_block.setVisible(False)
        self.btn_unlock.setVisible(True)
        self.body.setText(
            f"<b style='color:{COLORS['critical']};'>Blocked.</b> The keyboard "
            f"stays frozen. <b>Unplug {device_name}</b> to be safe — input "
            "restores automatically once it's removed, or use Force unlock.")
        self._center()

    def _center(self) -> None:
        self.adjustSize()
        if self.parent():
            geo = self.parent().geometry()
            self.move(geo.center().x() - self.width() // 2,
                      geo.center().y() - self.height() // 2)
