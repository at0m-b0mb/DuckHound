"""MainWindow — assembles the shell and wires the engine to the UI."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QStackedWidget,
                               QWidget)

from .. import APP_NAME, TAGLINE
from ..config import Settings
from ..core.engine import DetectionEngine
from . import icons
from .components.sidebar import Sidebar
from .components.toast import Toast
from .pages.dashboard import DashboardPage
from .pages.devices import DevicesPage
from .pages.settings import SettingsPage
from .pages.threats import ThreatsPage
from .theme import build_qss


class MainWindow(QWidget):
    def __init__(self, settings: Settings, demo: bool = False) -> None:
        super().__init__()
        self.setObjectName("Root")
        self.setWindowTitle(f"{APP_NAME} — {TAGLINE}")
        self.setMinimumSize(1160, 760)
        self.resize(1280, 820)
        self.setWindowIcon(icons.icon("shield", "#22D3EE", 64))

        self.settings = settings
        self.engine = DetectionEngine(settings, demo=demo)

        # Pages.
        self.dashboard = DashboardPage()
        self.devices = DevicesPage()
        self.threats = ThreatsPage()
        self.settings_page = SettingsPage(settings)

        self.stack = QStackedWidget()
        for page in (self.dashboard, self.devices, self.threats, self.settings_page):
            self.stack.addWidget(page)

        self.sidebar = Sidebar()
        self.sidebar.navigate.connect(self.stack.setCurrentIndex)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.sidebar)
        lay.addWidget(self.stack, 1)

        self.toast = Toast(self)

        self._wire()
        self._prime()

        if settings.autostart_monitor:
            self.engine.start()

    # ------------------------------------------------------------------ #
    def _wire(self) -> None:
        e = self.engine
        e.monitoring_changed.connect(self.dashboard.set_monitoring)
        e.status_text.connect(self.dashboard.set_status)
        e.stats_changed.connect(self.dashboard.set_stats)
        e.activity.connect(self.dashboard.set_level)
        e.devices_changed.connect(self.dashboard.set_devices)
        e.devices_changed.connect(self.devices.set_devices)
        e.threat_detected.connect(self._on_threat)

        self.dashboard.toggle_monitor.connect(e.toggle)
        self.devices.trust_requested.connect(e.trust_device)
        self.devices.block_requested.connect(e.block_device)
        self.settings_page.settings_changed.connect(e.apply_settings)

    def _prime(self) -> None:
        self.dashboard.set_stats(self.engine.snapshot_stats())
        self.dashboard.set_devices(self.engine.device_list())
        self.dashboard.set_monitoring(self.engine.monitoring)
        self.devices.set_devices(self.engine.device_list())
        self.threats.set_events(list(self.engine.events))
        for ev in reversed(self.engine.events):
            self.dashboard.on_threat(ev)

    def _on_threat(self, ev) -> None:
        self.dashboard.on_threat(ev)
        self.threats.add_event(ev)
        self.devices.set_devices(self.engine.device_list())
        self.toast.popup(ev.title, ev.detail, ev.severity.value)
        if self.settings.play_sound:
            QApplication.beep()

    # ------------------------------------------------------------------ #
    def resizeEvent(self, ev) -> None:
        super().resizeEvent(ev)
        if self.toast.isVisible():
            self.toast._reposition(animate=False)

    def closeEvent(self, ev) -> None:
        self.engine.stop()
        super().closeEvent(ev)


def build_window(settings: Settings, demo: bool = False) -> MainWindow:
    app = QApplication.instance()
    if app is not None:
        app.setStyleSheet(build_qss())
    win = MainWindow(settings, demo=demo)
    return win
