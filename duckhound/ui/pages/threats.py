"""Threats page — chronological log of detections with full forensics."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QScrollArea,
                               QVBoxLayout, QWidget)

from .. import icons
from ..components.badge import severity_badge
from ..theme import COLORS, SEVERITY, rgba


class ThreatsPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(16)

        title = QLabel("Threat Log")
        title.setProperty("role", "h1")
        self.subtitle = QLabel("Every detection, with the evidence behind it.")
        self.subtitle.setProperty("role", "muted")
        head = QVBoxLayout()
        head.setSpacing(2)
        head.addWidget(title)
        head.addWidget(self.subtitle)
        root.addLayout(head)

        self.list_box = QVBoxLayout()
        self.list_box.setSpacing(12)
        self.list_box.setAlignment(Qt.AlignTop)
        container = QWidget()
        container.setLayout(self.list_box)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(scroll, 1)

        self.empty = QLabel("Nothing has tried to attack you yet. 🛡")
        self.empty.setAlignment(Qt.AlignCenter)
        self.empty.setStyleSheet(
            f"color:{COLORS['text_faint']}; font-size:14px; padding:40px;")
        self.list_box.addWidget(self.empty)

    def set_events(self, events) -> None:
        while self.list_box.count():
            item = self.list_box.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        if not events:
            self.list_box.addWidget(self.empty)
            self.subtitle.setText("Every detection, with the evidence behind it.")
            return
        self.subtitle.setText(f"{len(events)} detection(s) recorded")
        for ev in events:
            self.list_box.addWidget(_threat_card(ev))

    def add_event(self, ev) -> None:
        if self.empty is not None and self.empty.parent() is not None:
            self.empty.setParent(None)
        self.list_box.insertWidget(0, _threat_card(ev))


def _chip(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"background:{COLORS['surface3']}; color:{COLORS['text_dim']};"
        f"border-radius:8px; padding:4px 9px; font-size:11px; font-weight:600;")
    return lbl


def _threat_card(ev) -> QFrame:
    color = SEVERITY.get(ev.severity.value, COLORS["accent"])
    card = QFrame()
    card.setProperty("card", "true")
    card.setStyleSheet(
        f"QFrame[card='true']{{background:{COLORS['surface']};"
        f"border:1px solid {COLORS['stroke_soft']};"
        f"border-left:4px solid {color}; border-radius:14px;}}")
    lay = QVBoxLayout(card)
    lay.setContentsMargins(18, 14, 18, 16)
    lay.setSpacing(10)

    icon = QLabel()
    icon.setPixmap(icons.pixmap("alert", color, 20))
    icon.setFixedSize(36, 36)
    icon.setAlignment(Qt.AlignCenter)
    icon.setStyleSheet(f"background:{rgba(color, 0.10)}; border-radius:11px;")

    title = QLabel(ev.title)
    title.setStyleSheet("font-size:15px; font-weight:800;")
    when = QLabel(ev.time_str)
    when.setStyleSheet(f"color:{COLORS['text_faint']}; font-size:12px;")
    titles = QVBoxLayout()
    titles.setSpacing(1)
    titles.addWidget(title)
    titles.addWidget(when)

    head = QHBoxLayout()
    head.setSpacing(12)
    head.addWidget(icon)
    head.addLayout(titles, 1)
    head.addWidget(severity_badge(ev.severity.value), 0, Qt.AlignTop)
    lay.addLayout(head)

    detail = QLabel(ev.detail)
    detail.setWordWrap(True)
    detail.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:13px;")
    lay.addWidget(detail)

    if ev.metrics:
        chips = QHBoxLayout()
        chips.setSpacing(8)
        m = ev.metrics
        if "keys_per_sec" in m:
            chips.addWidget(_chip(f"⚡ {m['keys_per_sec']:.0f} keys/s"))
        if "mean_interval_ms" in m:
            chips.addWidget(_chip(f"⏱ {m['mean_interval_ms']:.1f} ms gap"))
        if "jitter_cv" in m:
            chips.addWidget(_chip(f"📉 {m['jitter_cv']:.0%} jitter"))
        if "run_length" in m:
            chips.addWidget(_chip(f"🔁 {m['run_length']} key run"))
        chips.addStretch(1)
        lay.addLayout(chips)

    if ev.actions:
        resp = QHBoxLayout()
        resp.setSpacing(8)
        tag = QLabel("RESPONSE")
        tag.setStyleSheet(
            f"color:{COLORS['text_faint']}; font-size:10px; font-weight:800;"
            f"letter-spacing:1px;")
        resp.addWidget(tag)
        for a in ev.actions:
            pill = QLabel("✓ " + a)
            pill.setStyleSheet(
                f"color:{COLORS['ok']}; background:{rgba('ok', 0.12)};"
                f"border-radius:8px; padding:3px 9px; font-size:11px; font-weight:700;")
            resp.addWidget(pill)
        resp.addStretch(1)
        lay.addLayout(resp)

    return card
