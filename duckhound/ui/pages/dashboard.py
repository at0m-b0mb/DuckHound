"""Dashboard — radar, live threat meter, headline stats and recent activity."""
from __future__ import annotations

import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QVBoxLayout, QWidget)

from .. import icons
from ..components.card import Card
from ..components.radar import Radar
from ..components.stat_card import StatCard
from ..components.threat_meter import ThreatMeter
from ..theme import COLORS, SEVERITY, rgba


class DashboardPage(QWidget):
    toggle_monitor = Signal()
    grant_access_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(18)

        self.perm_bar = self._build_perm_bar()
        self.perm_bar.setVisible(False)
        root.addWidget(self.perm_bar)
        root.addLayout(self._build_header())
        root.addLayout(self._build_stats())
        root.addLayout(self._build_main(), 1)

    # -- permission warning bar ---------------------------------------- #
    def _build_perm_bar(self) -> QFrame:
        bar = QFrame()
        warn = COLORS["warn"]
        bar.setStyleSheet(
            f"background:{rgba(warn, 0.12)}; border:1px solid {rgba(warn, 0.45)};"
            f"border-radius:14px;")
        icon = QLabel()
        icon.setPixmap(icons.pixmap("alert", warn, 22))
        icon.setFixedSize(38, 38)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"background:{rgba(warn, 0.14)}; border-radius:11px;")

        self.perm_lbl = QLabel("Keystroke monitoring is blocked.")
        self.perm_lbl.setWordWrap(True)
        self.perm_lbl.setStyleSheet("font-size:13px; font-weight:600;")

        grant = QPushButton("Grant Access")
        grant.setProperty("accent", "true")
        grant.setCursor(Qt.PointingHandCursor)
        grant.clicked.connect(self.grant_access_requested.emit)

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(12)
        lay.addWidget(icon)
        lay.addWidget(self.perm_lbl, 1)
        lay.addWidget(grant)
        return bar

    def set_permission(self, ok: bool, detail: str) -> None:
        if ok:
            self.perm_bar.setVisible(False)
            return
        self.perm_lbl.setText(
            f"<b>Keystroke monitoring is blocked</b> — {detail}. "
            "DuckHound cannot see injected keystrokes until this is fixed.")
        self.perm_bar.setVisible(True)

    # -- header --------------------------------------------------------- #
    def _build_header(self) -> QHBoxLayout:
        title = QLabel("Security Overview")
        title.setProperty("role", "h1")
        self.status_lbl = QLabel("Initializing…")
        self.status_lbl.setProperty("role", "muted")

        left = QVBoxLayout()
        left.setSpacing(2)
        left.addWidget(title)
        left.addWidget(self.status_lbl)

        self.live_dot = QLabel("●")
        self.live_dot.setStyleSheet(f"color:{COLORS['text_faint']}; font-size:13px;")
        self.live_lbl = QLabel("PAUSED")
        self.live_lbl.setStyleSheet(
            f"color:{COLORS['text_dim']}; font-weight:800; letter-spacing:1px;"
            f"font-size:12px;")
        pill = QFrame()
        pill.setStyleSheet(
            f"background:{COLORS['surface2']}; border:1px solid {COLORS['stroke']};"
            f"border-radius:13px;")
        pl = QHBoxLayout(pill)
        pl.setContentsMargins(12, 7, 14, 7)
        pl.setSpacing(8)
        pl.addWidget(self.live_dot)
        pl.addWidget(self.live_lbl)

        self.toggle_btn = QPushButton("  Arm Monitoring")
        self.toggle_btn.setProperty("accent", "true")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setIcon(icons.icon("power", "#04222B", 18))
        self.toggle_btn.clicked.connect(self.toggle_monitor.emit)

        row = QHBoxLayout()
        row.addLayout(left)
        row.addStretch(1)
        row.addWidget(pill)
        row.addWidget(self.toggle_btn)
        return row

    # -- stat cards ----------------------------------------------------- #
    def _build_stats(self) -> QHBoxLayout:
        self.card_devices = StatCard("Connected Devices", "usb", "accent")
        self.card_blocked = StatCard("Threats Blocked", "shield", "ok")
        self.card_keys = StatCard("Keystrokes Analyzed", "activity", "accent2")
        self.card_uptime = StatCard("Watching For", "scan", "warn")
        row = QHBoxLayout()
        row.setSpacing(16)
        for c in (self.card_devices, self.card_blocked, self.card_keys, self.card_uptime):
            row.addWidget(c)
        return row

    # -- main area ------------------------------------------------------ #
    def _build_main(self) -> QHBoxLayout:
        # Radar card.
        radar_card = Card("Live Radar", "radar")
        self.radar = Radar()
        radar_card.add(self.radar)
        legend = QHBoxLayout()
        legend.setSpacing(16)
        for txt, col in (("Trusted", COLORS["ok"]), ("New", COLORS["warn"]),
                         ("Blocked", COLORS["critical"])):
            d = QLabel("●  " + txt)
            d.setStyleSheet(f"color:{col}; font-size:12px; font-weight:600;")
            legend.addWidget(d)
        legend.addStretch(1)
        radar_card.add(legend)

        # Right column.
        meter_card = Card("Threat Level", "alert")
        self.meter = ThreatMeter()
        meter_card.add(self.meter)
        self.signal_lbl = QLabel("0 keys/sec")
        self.signal_lbl.setAlignment(Qt.AlignCenter)
        self.signal_lbl.setStyleSheet(
            f"color:{COLORS['text_dim']}; font-size:13px; font-weight:600;")
        meter_card.add(self.signal_lbl)

        self.activity_card = Card("Recent Activity", "bell")
        self.activity_box = QVBoxLayout()
        self.activity_box.setSpacing(8)
        self.empty_lbl = QLabel("No threats yet — you're protected.")
        self.empty_lbl.setProperty("role", "muted")
        self.activity_box.addWidget(self.empty_lbl)
        self.activity_card.add(self.activity_box)
        self.activity_card.body().addStretch(1)

        right = QVBoxLayout()
        right.setSpacing(16)
        right.addWidget(meter_card)
        right.addWidget(self.activity_card, 1)

        row = QHBoxLayout()
        row.setSpacing(16)
        row.addWidget(radar_card, 3)
        rc = QWidget()
        rc.setLayout(right)
        rc.setMinimumWidth(300)
        row.addWidget(rc, 2)
        return row

    # -- updates -------------------------------------------------------- #
    def set_status(self, text: str) -> None:
        self.status_lbl.setText(text)

    def set_monitoring(self, on: bool) -> None:
        if on:
            self.live_dot.setStyleSheet(f"color:{COLORS['ok']}; font-size:13px;")
            self.live_lbl.setText("LIVE")
            self.live_lbl.setStyleSheet(
                f"color:{COLORS['ok']}; font-weight:800; letter-spacing:1px;"
                f"font-size:12px;")
            self.toggle_btn.setText("  Pause Monitoring")
            self.toggle_btn.setProperty("accent", None)
            self.toggle_btn.setProperty("ghost", "true")
            self.toggle_btn.setIcon(icons.icon("power", COLORS["text"], 18))
        else:
            self.live_dot.setStyleSheet(f"color:{COLORS['text_faint']}; font-size:13px;")
            self.live_lbl.setText("PAUSED")
            self.live_lbl.setStyleSheet(
                f"color:{COLORS['text_dim']}; font-weight:800; letter-spacing:1px;"
                f"font-size:12px;")
            self.toggle_btn.setText("  Arm Monitoring")
            self.toggle_btn.setProperty("ghost", None)
            self.toggle_btn.setProperty("accent", "true")
            self.toggle_btn.setIcon(icons.icon("power", "#04222B", 18))
        self.toggle_btn.style().unpolish(self.toggle_btn)
        self.toggle_btn.style().polish(self.toggle_btn)

    def set_stats(self, s: dict) -> None:
        self.card_devices.set_value(s["devices"], f"{s['input_devices']} input · HID")
        self.card_blocked.set_value(s["blocked"], f"{s['threats']} detected total")
        self.card_keys.set_value(f"{s['keys_analyzed']:,}", "timing fingerprinted")
        self.card_uptime.set_value(_fmt_uptime(s["uptime_s"]),
                                   s["backend"] if s["backend_ok"] else "keystroke-only")

    def set_level(self, level: float, cps: float) -> None:
        self.meter.set_value(level)
        self.radar.set_level(level)
        if cps > 0:
            self.signal_lbl.setText(f"{cps:,.0f} keys/sec")
        elif level < 1:
            self.signal_lbl.setText("0 keys/sec")

    def set_devices(self, devices) -> None:
        self.radar.set_devices(devices)

    def on_threat(self, ev) -> None:
        self.radar.ping(ev.severity.value in ("high", "critical"))
        if self.empty_lbl is not None:
            self.empty_lbl.setParent(None)
            self.empty_lbl = None
        row = _activity_row(ev)
        self.activity_box.insertWidget(0, row)
        while self.activity_box.count() > 5:
            item = self.activity_box.takeAt(self.activity_box.count() - 1)
            if item.widget():
                item.widget().setParent(None)


def _activity_row(ev) -> QFrame:
    color = SEVERITY.get(ev.severity.value, COLORS["accent"])
    f = QFrame()
    f.setStyleSheet(
        f"background:{COLORS['surface2']}; border:1px solid {COLORS['stroke_soft']};"
        f"border-left:3px solid {color}; border-radius:10px;")
    lay = QHBoxLayout(f)
    lay.setContentsMargins(12, 8, 12, 8)
    dot = QLabel("●")
    dot.setStyleSheet(f"color:{color}; font-size:11px;")
    txt = QVBoxLayout()
    txt.setSpacing(1)
    t = QLabel(ev.device_name)
    t.setStyleSheet("font-size:13px; font-weight:700;")
    s = QLabel(f"{ev.severity.value.title()} · {ev.time_str}")
    s.setStyleSheet(f"color:{COLORS['text_faint']}; font-size:11px;")
    txt.addWidget(t)
    txt.addWidget(s)
    score = QLabel(f"{ev.score}")
    score.setStyleSheet(f"color:{color}; font-size:18px; font-weight:800;")
    lay.addWidget(dot)
    lay.addLayout(txt, 1)
    lay.addWidget(score)
    return f


def _fmt_uptime(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    return f"{seconds // 3600}h {seconds % 3600 // 60}m"
