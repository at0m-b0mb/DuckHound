"""Settings — detection sensitivity, automatic responses, general behavior."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QDoubleSpinBox, QFrame, QHBoxLayout, QLabel,
                               QScrollArea, QSpinBox, QVBoxLayout, QWidget)

from ...config import Settings
from ..components.card import Card
from ..components.toggle import Toggle
from ..theme import COLORS


class SettingsPage(QWidget):
    settings_changed = Signal(object)  # Settings

    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self._toggles: dict[str, Toggle] = {}
        self._spins: dict[str, object] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(16)

        title = QLabel("Settings")
        title.setProperty("role", "h1")
        sub = QLabel("Tune how aggressively DuckHound detects and responds.")
        sub.setProperty("role", "muted")
        head = QVBoxLayout()
        head.setSpacing(2)
        head.addWidget(title)
        head.addWidget(sub)
        root.addLayout(head)

        inner = QVBoxLayout()
        inner.setSpacing(16)
        inner.setAlignment(Qt.AlignTop)
        inner.addWidget(self._sensitivity_card())
        inner.addWidget(self._response_card())
        inner.addWidget(self._general_card())
        inner.addWidget(self._privacy_note())

        container = QWidget()
        container.setLayout(inner)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(scroll, 1)

    # -- cards ---------------------------------------------------------- #
    def _sensitivity_card(self) -> Card:
        card = Card("Detection Sensitivity", "scan")
        card.add(self._spin_row(
            "Human-speed ceiling", "Keystrokes closer than this look automated.",
            "fast_interval_ms", self.settings.fast_interval_ms, 5, 120, " ms"))
        card.add(_divider())
        card.add(self._spin_row(
            "Burst run length", "Fast keys in a row before it trips.",
            "burst_run_length", self.settings.burst_run_length, 5, 60, " keys"))
        card.add(_divider())
        card.add(self._dspin_row(
            "Robotic-timing threshold",
            "Lower = stricter. Machine timing has near-zero jitter.",
            "robotic_cv_threshold", self.settings.robotic_cv_threshold, 0.05, 0.6))
        return card

    def _response_card(self) -> Card:
        card = Card("Automatic Response", "shield")
        card.add(self._toggle_row(
            "Alert me", "In-app banner + system notification.",
            "notify", self.settings.notify))
        card.add(_divider())
        card.add(self._toggle_row(
            "Play alarm sound", "Audible alert on detection.",
            "play_sound", self.settings.play_sound))
        card.add(_divider())
        card.add(self._toggle_row(
            "Lock the screen", "Immediately lock the workstation when attacked.",
            "lock_screen", self.settings.lock_screen, danger=True))
        card.add(_divider())
        card.add(self._toggle_row(
            "Block injected keystrokes", "Swallow input during an attack (best-effort).",
            "block_keystrokes", self.settings.block_keystrokes, danger=True))
        card.add(_divider())
        card.add(self._toggle_row(
            "Flag device for de-authorization",
            "Surface the exact command to cut the device's USB power.",
            "deauthorize_device", self.settings.deauthorize_device, danger=True))
        return card

    def _general_card(self) -> Card:
        card = Card("General", "gear")
        card.add(self._toggle_row(
            "Start monitoring on launch", "Arm DuckHound the moment it opens.",
            "autostart_monitor", self.settings.autostart_monitor))
        card.add(_divider())
        card.add(self._toggle_row(
            "Trust the built-in keyboard", "Never flag the internal keyboard.",
            "trust_internal_keyboard", self.settings.trust_internal_keyboard))
        card.add(_divider())
        card.add(self._toggle_row(
            "Minimize to tray", "Keep guarding in the background.",
            "minimize_to_tray", self.settings.minimize_to_tray))
        return card

    def _privacy_note(self) -> QFrame:
        f = QFrame()
        f.setProperty("card", "soft")
        lay = QHBoxLayout(f)
        lay.setContentsMargins(16, 12, 16, 12)
        lbl = QLabel(
            "🔒  DuckHound is 100% local. It measures keystroke <b>timing</b> "
            "only — never which keys you press — and sends nothing off your device.")
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:12px;")
        lay.addWidget(lbl)
        return f

    # -- row builders --------------------------------------------------- #
    def _label_block(self, title: str, desc: str) -> QVBoxLayout:
        t = QLabel(title)
        t.setStyleSheet("font-size:14px; font-weight:700;")
        d = QLabel(desc)
        d.setStyleSheet(f"color:{COLORS['text_faint']}; font-size:12px;")
        d.setWordWrap(True)
        box = QVBoxLayout()
        box.setSpacing(2)
        box.addWidget(t)
        box.addWidget(d)
        return box

    def _toggle_row(self, title, desc, key, value, danger=False) -> QFrame:
        frame = QFrame()
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(self._label_block(title, desc), 1)
        tog = Toggle(value)
        tog.toggled_value.connect(lambda _on: self._emit())
        self._toggles[key] = tog
        lay.addWidget(tog, 0, Qt.AlignVCenter)
        return frame

    def _spin_row(self, title, desc, key, value, lo, hi, suffix="") -> QFrame:
        frame = QFrame()
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(self._label_block(title, desc), 1)
        spin = QSpinBox()
        spin.setRange(lo, hi)
        spin.setValue(int(value))
        spin.setSuffix(suffix)
        spin.setFixedWidth(110)
        spin.valueChanged.connect(lambda _v: self._emit())
        self._spins[key] = spin
        lay.addWidget(spin, 0, Qt.AlignVCenter)
        return frame

    def _dspin_row(self, title, desc, key, value, lo, hi) -> QFrame:
        frame = QFrame()
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(self._label_block(title, desc), 1)
        spin = QDoubleSpinBox()
        spin.setRange(lo, hi)
        spin.setSingleStep(0.01)
        spin.setDecimals(2)
        spin.setValue(float(value))
        spin.setFixedWidth(110)
        spin.valueChanged.connect(lambda _v: self._emit())
        self._spins[key] = spin
        lay.addWidget(spin, 0, Qt.AlignVCenter)
        return frame

    # -- collect / emit ------------------------------------------------- #
    def collect(self) -> Settings:
        s = self.settings
        for key, tog in self._toggles.items():
            setattr(s, key, tog.isChecked())
        for key, spin in self._spins.items():
            setattr(s, key, spin.value())
        return s

    def _emit(self) -> None:
        s = self.collect()
        s.save()
        self.settings_changed.emit(s)


def _divider() -> QFrame:
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet(f"background:{COLORS['stroke_soft']};")
    return line
