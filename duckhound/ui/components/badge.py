"""Small pill label for device state / severity."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel

from ..theme import SEVERITY, STATE_COLOR, rgba


def _pill(text: str, hex_color: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setStyleSheet(
        f"color: {hex_color};"
        f"background: {rgba(hex_color, 0.14)};"
        f"border: 1px solid {rgba(hex_color, 0.40)};"
        f"border-radius: 9px; padding: 3px 9px;"
        f"font-size: 10px; font-weight: 800; letter-spacing: 1px;"
    )
    return lbl


def state_badge(state: str) -> QLabel:
    return _pill(state, STATE_COLOR.get(state, "#60A5FA"))


def severity_badge(sev: str) -> QLabel:
    return _pill(sev, SEVERITY.get(sev, "#60A5FA"))
