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

    def respond(self, title: str, detail: str) -> list[str]:
        """Run every enabled response and return human-readable labels."""
        taken: list[str] = []
        s = self.settings
        if s.notify and self.notify(title, detail):
            taken.append("Alerted")
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
                # Works on modern macOS without extra privileges.
                subprocess.run([
                    "/System/Library/CoreServices/Menu Extras/User.menu/Contents/"
                    "Resources/CGSession", "-suspend"
                ], timeout=5)
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
