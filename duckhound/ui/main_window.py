"""MainWindow — Aurora-Glass shell wiring the engine to the UI."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QRadialGradient
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMenu, QStackedWidget,
                               QSystemTrayIcon, QWidget)

from .. import APP_NAME, TAGLINE
from ..config import Settings
from ..core import alarm, health
from ..core.engine import DetectionEngine
from . import icons
from .components.lockdown_dialog import LockdownDialog
from .components.sidebar import Sidebar
from .components.toast import Toast
from .pages.dashboard import DashboardPage
from .pages.devices import DevicesPage
from .pages.protection import ProtectionPage
from .pages.settings import SettingsPage
from .pages.threats import ThreatsPage
from .theme import COLORS, build_qss

# Page indices (must match the sidebar SECTIONS order).
P_DASH, P_PROTECT, P_DEVICES, P_THREATS, P_SETTINGS = range(5)


class MainWindow(QWidget):
    def __init__(self, settings: Settings, demo: bool = False) -> None:
        super().__init__()
        self.setObjectName("Root")
        self.setWindowTitle(f"{APP_NAME} — {TAGLINE}")
        self.setMinimumSize(1180, 780)
        self.resize(1320, 850)
        self.setWindowIcon(icons.icon("shield", COLORS["accent"], 64))

        self.settings = settings
        self.engine = DetectionEngine(settings, demo=demo)
        self._really_quit = False

        self.dashboard = DashboardPage()
        self.protection = ProtectionPage()
        self.devices = DevicesPage()
        self.threats = ThreatsPage()
        self.settings_page = SettingsPage(settings)

        self.stack = QStackedWidget()
        for page in (self.dashboard, self.protection, self.devices,
                     self.threats, self.settings_page):
            self.stack.addWidget(page)

        self.sidebar = Sidebar()
        self.sidebar.navigate.connect(self.stack.setCurrentIndex)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.sidebar)
        lay.addWidget(self.stack, 1)

        self.toast = Toast(self)
        self.lockdown_dialog = LockdownDialog(self)
        self.lockdown_dialog.approved.connect(self.engine.approve_lockdown)
        self.lockdown_dialog.blocked.connect(self._on_lockdown_block)
        self.lockdown_dialog.force_unlock.connect(self.engine.release_lockdown)
        self._lockdown_device = None

        self._build_tray()
        self._wire()
        self._prime()

        # Keep the protection score fresh (catches permissions granted outside).
        self._health_timer = QTimer(self)
        self._health_timer.setInterval(4000)
        self._health_timer.timeout.connect(self._refresh_protection)
        self._health_timer.start()

        if settings.autostart_monitor:
            self.engine.start()

    # ------------------------------------------------------------------ #
    # Aurora backdrop
    # ------------------------------------------------------------------ #
    def paintEvent(self, _ev) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        base = QLinearGradient(0, 0, 0, r.height())
        base.setColorAt(0.0, QColor(COLORS["bg_grad_a"]))
        base.setColorAt(1.0, QColor(COLORS["bg"]))
        p.fillRect(r, base)
        self._glow(p, r.width() * 0.10, r.height() * -0.05,
                   r.width() * 0.55, COLORS["accent"], 32)
        self._glow(p, r.width() * 0.98, r.height() * 0.20,
                   r.width() * 0.50, COLORS["accent2"], 40)
        self._glow(p, r.width() * 0.55, r.height() * 1.05,
                   r.width() * 0.65, COLORS["accent3"], 30)
        p.end()

    @staticmethod
    def _glow(p, cx, cy, radius, color, alpha) -> None:
        g = QRadialGradient(cx, cy, radius)
        c0 = QColor(color); c0.setAlpha(alpha)
        c1 = QColor(color); c1.setAlpha(0)
        g.setColorAt(0.0, c0)
        g.setColorAt(1.0, c1)
        p.fillRect(p.window(), g)

    # ------------------------------------------------------------------ #
    # System tray
    # ------------------------------------------------------------------ #
    def _build_tray(self) -> None:
        self.tray = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(icons.icon("shield", COLORS["accent"], 22), self)
        self.tray.setToolTip(f"{APP_NAME} — {TAGLINE}")
        menu = QMenu()
        self.tray_toggle = menu.addAction("Arm monitoring", self.engine.toggle)
        menu.addAction("Lock now", self._on_panic)
        menu.addSeparator()
        menu.addAction("Open DuckHound", self._show_window)
        menu.addAction("Quit", self._quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()
        QApplication.instance().setQuitOnLastWindowClosed(False)

    def _on_tray_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._show_window()

    def _show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit(self) -> None:
        self._really_quit = True
        self.engine.stop()
        QApplication.instance().quit()

    # ------------------------------------------------------------------ #
    def _wire(self) -> None:
        e = self.engine
        e.monitoring_changed.connect(self.dashboard.set_monitoring)
        e.monitoring_changed.connect(self._on_monitoring_changed)
        e.status_text.connect(self.dashboard.set_status)
        e.stats_changed.connect(self.dashboard.set_stats)
        e.activity.connect(self.dashboard.set_level)
        e.devices_changed.connect(self.dashboard.set_devices)
        e.devices_changed.connect(self.devices.set_devices)
        e.threat_detected.connect(self._on_threat)
        e.permission_status.connect(self.dashboard.set_permission)
        e.permission_status.connect(lambda *_: self._refresh_protection())
        e.lockdown_engaged.connect(self._on_lockdown_engaged)
        e.lockdown_released.connect(self._on_lockdown_released)
        e.allowlist_changed.connect(self.devices.set_allowlist)
        e.allowlist_changed.connect(lambda *_: self._refresh_protection())

        self.dashboard.toggle_monitor.connect(e.toggle)
        self.dashboard.panic_lock.connect(self._on_panic)
        self.dashboard.open_protection.connect(
            lambda: self._navigate(P_PROTECT))
        self.devices.trust_requested.connect(e.trust_device)
        self.devices.block_requested.connect(e.block_device)
        self.devices.untrust_requested.connect(e.untrust_device)
        self.devices.trust_all_requested.connect(e.trust_all_current)
        self.devices.rescan_requested.connect(e.enumerate_once)
        self.protection.fix_requested.connect(self._on_fix)
        self.protection.fix_all_requested.connect(self._on_fix_all)
        self.settings_page.settings_changed.connect(e.apply_settings)
        self.settings_page.settings_changed.connect(
            lambda *_: self._refresh_protection())

    def _navigate(self, index: int) -> None:
        self.sidebar.select(index)
        self.stack.setCurrentIndex(index)

    # -- protection score ----------------------------------------------- #
    def _refresh_protection(self) -> None:
        report = health.assess(self.engine.monitoring, self.settings)
        self.dashboard.set_report(report)
        self.protection.set_report(report)

    def _on_monitoring_changed(self, on: bool) -> None:
        if self.tray is not None:
            self.tray_toggle.setText("Pause monitoring" if on else "Arm monitoring")
        self._refresh_protection()

    def _on_fix(self, key: str) -> None:
        s = self.settings
        if key == "armed":
            self.engine.start()
        elif key == "lockdown":
            s.lockdown_new_keyboards = True
            s.save()
        elif key == "lock":
            s.lock_on_lockdown = True
            s.save()
        elif key == "perm":
            self.engine.request_access()
        elif key == "baseline":
            self.engine.trust_all_current()
        elif key == "autostart":
            s.autostart_monitor = True
            s.save()
        self._refresh_protection()

    def _on_fix_all(self) -> None:
        for chk in health.assess(self.engine.monitoring, self.settings).failing:
            if chk.fixable:
                self._on_fix(chk.key)

    def _on_panic(self) -> None:
        locked = self.engine.responder.lock_screen()
        self.dashboard.set_status(
            "🔒 Screen locked" if locked else "Lock unavailable — check settings")

    # -- lockdown ------------------------------------------------------- #
    def _on_lockdown_engaged(self, device, reason: str) -> None:
        self._lockdown_device = device
        name = device.name if device else "an unknown input device"
        self.lockdown_dialog.prompt(name, reason)
        if self.tray is not None:
            self.tray.showMessage("DuckHound — Lockdown",
                                  f"{reason}", QSystemTrayIcon.Critical, 5000)

    def _on_lockdown_block(self) -> None:
        if self._lockdown_device is not None:
            self.engine.block_device(self._lockdown_device.key)
        name = self._lockdown_device.name if self._lockdown_device else "the device"
        self.lockdown_dialog.show_blocked(name)

    def _on_lockdown_released(self) -> None:
        self.lockdown_dialog.hide()
        self._lockdown_device = None

    # -- priming -------------------------------------------------------- #
    def _prime(self) -> None:
        if not self.engine.demo:
            from ..core import permissions
            ok, detail = permissions.keystroke_access()
            self.dashboard.set_permission(ok, detail)
            self.engine.enumerate_once()
        self.dashboard.set_stats(self.engine.snapshot_stats())
        self.dashboard.set_devices(self.engine.device_list())
        self.dashboard.set_monitoring(self.engine.monitoring)
        self.devices.set_devices(self.engine.device_list())
        self.devices.set_allowlist(self.engine.trusted_list())
        self.threats.set_events(list(self.engine.events))
        for ev in reversed(self.engine.events):
            self.dashboard.on_threat(ev)
        self._refresh_protection()

    def _on_threat(self, ev) -> None:
        self.dashboard.on_threat(ev)
        self.threats.add_event(ev)
        self.devices.set_devices(self.engine.device_list())
        self.toast.popup(ev.title, ev.detail, ev.severity.value)
        if self.settings.play_sound:
            alarm.play()
        if self.tray is not None:
            self.tray.showMessage("DuckHound — Threat detected", ev.detail,
                                  QSystemTrayIcon.Critical, 6000)

    # ------------------------------------------------------------------ #
    def resizeEvent(self, ev) -> None:
        super().resizeEvent(ev)
        if self.toast.isVisible():
            self.toast._reposition(animate=False)

    def closeEvent(self, ev) -> None:
        # Keep guarding in the background if a tray is available.
        if (self.tray is not None and self.settings.minimize_to_tray
                and not self._really_quit):
            ev.ignore()
            self.hide()
            self.tray.showMessage(
                "DuckHound is still protecting you",
                "Monitoring continues in the background. Quit from the tray icon.",
                QSystemTrayIcon.Information, 4000)
            return
        self.engine.stop()
        super().closeEvent(ev)


def build_window(settings: Settings, demo: bool = False) -> MainWindow:
    app = QApplication.instance()
    if app is not None:
        app.setStyleSheet(build_qss())
    return MainWindow(settings, demo=demo)
