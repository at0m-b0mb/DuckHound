"""Platform-specific USB enumeration backends.

Each backend exposes ``enumerate() -> list[Device]``. The engine diffs
successive snapshots to learn when devices arrive or leave. Backends never
raise on a host they don't support — they degrade to an empty list so the rest
of DuckHound (keystroke analysis, UI) keeps working everywhere.
"""
from __future__ import annotations

import sys

from .base import Backend, NullBackend


def get_backend() -> Backend:
    try:
        if sys.platform.startswith("linux"):
            from .linux import LinuxBackend
            return LinuxBackend()
        if sys.platform == "darwin":
            from .macos import MacBackend
            return MacBackend()
        if sys.platform.startswith("win"):
            from .windows import WindowsBackend
            return WindowsBackend()
    except Exception:
        pass
    return NullBackend()
