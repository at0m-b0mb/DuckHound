"""Active responses fired when a BadUSB attack is confirmed.

Every action is best-effort and platform-aware. Nothing here raises; an action
that isn't possible on the current host simply reports that it was skipped, so
the engine can record exactly what defense ran.
"""
from __future__ import annotations

import subprocess
import sys

from ..config import Settings


class Responder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock_listener = None  # persistent lockdown suppressor

    def respond(self, title: str, detail: str) -> list[str]:
        """Run every enabled response and return human-readable labels."""
        taken: list[str] = []
        s = self.settings
        if s.notify and self.notify(title, detail):
            taken.append("Alerted")
        if s.block_keystrokes and self.start_block_window():
            taken.append("Blocked keystrokes")
        if s.lock_screen and self.lock_screen():
            taken.append("Locked screen")
        if s.deauthorize_device and self.deauthorize_hint():
            taken.append("Flagged for de-authorization")
        return taken

    # ---------------------------------------------------------------- #
    def notify(self, title: str, detail: str) -> bool:
        try:
            if sys.platform == "darwin":
                script = f'display notification "{_esc(detail)}" with title "{_esc(title)}"'
                subprocess.run(["osascript", "-e", script], timeout=5)
                return True
            if sys.platform.startswith("linux"):
                subprocess.run(["notify-send", "-u", "critical", title, detail], timeout=5)
                return True
            if sys.platform.startswith("win"):
                ps = (
                    "[reflection.assembly]::loadwithpartialname('System.Windows.Forms')"
                    ">$null;"
                    f"[System.Windows.Forms.MessageBox]::Show('{_esc(detail)}','{_esc(title)}')"
                )
                subprocess.Popen(["powershell", "-NoProfile", "-Command", ps])
                return True
        except Exception:
            pass
        return False

    def lock_screen(self) -> bool:
        try:
            if sys.platform == "darwin":
                # The classic CGSession path was removed in recent macOS, so try
                # several no-entitlement methods in order of reliability.
                # 1) Screensaver — locks instantly if "require password" is set.
                try:
                    subprocess.run(["open", "-a", "ScreenSaverEngine"], timeout=5)
                    return True
                except Exception:
                    pass
                # 2) Ctrl-Cmd-Q lock shortcut (needs Accessibility).
                try:
                    subprocess.run([
                        "osascript", "-e",
                        'tell application "System Events" to keystroke "q" '
                        "using {control down, command down}",
                    ], timeout=5)
                    return True
                except Exception:
                    pass
                # 3) Last resort: sleep the display.
                subprocess.run(["pmset", "displaysleepnow"], timeout=5)
                return True
            if sys.platform.startswith("linux"):
                for cmd in (["loginctl", "lock-session"],
                            ["xdg-screensaver", "lock"],
                            ["gnome-screensaver-command", "-l"]):
                    try:
                        subprocess.run(cmd, timeout=5)
                        return True
                    except Exception:
                        continue
            if sys.platform.startswith("win"):
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], timeout=5)
                return True
        except Exception:
            pass
        return False

    def _make_suppressor(self):
        """Start a global keyboard suppressor and return it (has ``.stop()``),
        or None. Uses the native CGEventTap on macOS (pynput's suppressor decodes
        keys via Carbon on a background thread and crashes on macOS 26)."""
        try:
            if sys.platform == "darwin":
                from .mac_input import MacKeyTap
                tap = MacKeyTap(on_press=lambda: None, suppress=True)
                return tap if tap.start() else None
            from pynput import keyboard
            listener = keyboard.Listener(
                on_press=lambda _k: None, on_release=lambda _k: None, suppress=True)
            listener.start()
            return listener
        except Exception:
            return None

    def start_block_window(self, duration_s: float = 2.0) -> bool:
        """Swallow ALL keyboard input for a brief window to neutralise the rest
        of an injected payload. Best-effort and intentionally short."""
        listener = self._make_suppressor()
        if listener is None:
            return False
        import threading

        def _release():
            try:
                listener.stop()
            except Exception:
                pass
        threading.Timer(max(0.3, duration_s), _release).start()
        return True

    # -- Lockdown: persistent global keyboard freeze --------------------- #
    def engage_lockdown(self) -> bool:
        """Freeze ALL keyboard input until released. Needs the same OS
        permission as the detector; a real user navigates with the mouse."""
        if self._lock_listener is not None:
            return True
        self._lock_listener = self._make_suppressor()
        return self._lock_listener is not None

    def release_lockdown(self) -> None:
        if self._lock_listener is not None:
            try:
                self._lock_listener.stop()
            except Exception:
                pass
            self._lock_listener = None

    def deauthorize_hint(self) -> bool:
        """Marker for the most aggressive response.

        Actually cutting a device's USB authorization requires elevated rights
        (writing ``/sys/bus/usb/devices/*/authorized`` on Linux, ``pnputil``
        on Windows). DuckHound records the intent and surfaces the exact
        command in the event log rather than silently demanding root.
        """
        return self.settings.deauthorize_device


def _esc(text: str) -> str:
    return text.replace('"', "'").replace("\n", " ")[:180]
