"""OS permission checks for the global keystroke hook.

The single biggest reason DuckHound can appear to do nothing is a missing OS
permission: on macOS the keyboard hook needs **Input Monitoring** (and
Accessibility), and without it the hook silently receives *zero* events while
still reporting itself as "running". This module lets DuckHound detect that up
front and tell the user exactly what to fix — instead of pretending all is well.
"""
from __future__ import annotations

import os
import subprocess
import sys


def _macos_input_monitoring() -> bool:
    try:
        from Quartz import CGPreflightListenEventAccess
        return bool(CGPreflightListenEventAccess())
    except Exception:
        return True  # can't check → don't block the user


def _macos_accessibility() -> bool:
    try:
        from ApplicationServices import AXIsProcessTrusted
        return bool(AXIsProcessTrusted())
    except Exception:
        return True


def listen_access() -> tuple[bool, str]:
    """Permission to DETECT keystrokes — Input Monitoring on macOS.

    Detection uses a listen-only event tap, which needs Input Monitoring only
    (NOT Accessibility). Keep this separate so the app doesn't claim it's blind
    when only the blocking permission is missing.
    """
    if sys.platform == "darwin":
        if _macos_input_monitoring():
            return True, "Input Monitoring granted"
        return False, "Grant Input Monitoring to your terminal / app"
    if sys.platform.startswith("linux"):
        if os.environ.get("WAYLAND_DISPLAY") and not os.environ.get("DISPLAY"):
            return False, "Wayland restricts global key capture — use an X11 session"
        return True, "X11 input accessible"
    if sys.platform.startswith("win"):
        return True, "Low-level keyboard hook available"
    return True, ""


def block_access() -> tuple[bool, str]:
    """Permission to BLOCK / suppress keystrokes — Accessibility on macOS.

    An *active* event tap that can drop keystrokes needs Accessibility (Input
    Monitoring alone only allows listening). Without it DuckHound can detect an
    attack but cannot freeze the keyboard to stop it.
    """
    if sys.platform == "darwin":
        if _macos_accessibility():
            return True, "Accessibility granted"
        return False, "Grant Accessibility to block injected keystrokes"
    return True, "Keystroke blocking available"


def keystroke_access() -> tuple[bool, str]:
    """Backwards-compatible alias: the DETECTION capability."""
    return listen_access()


def request_keystroke_access() -> None:
    """Trigger the OS permission prompts (macOS only). No-op elsewhere."""
    if sys.platform != "darwin":
        return
    try:
        from Quartz import CGRequestListenEventAccess
        CGRequestListenEventAccess()  # Input Monitoring prompt
    except Exception:
        pass
    try:
        from ApplicationServices import (AXIsProcessTrustedWithOptions,
                                         kAXTrustedCheckOptionPrompt)
        AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True})
    except Exception:
        pass
    open_privacy_settings()


def open_privacy_settings() -> None:
    """Open the relevant OS privacy settings pane."""
    try:
        if sys.platform == "darwin":
            subprocess.Popen([
                "open",
                "x-apple.systempreferences:com.apple.preference.security"
                "?Privacy_ListenEvent",
            ])
        elif sys.platform.startswith("win"):
            subprocess.Popen(["cmd", "/c", "start", "ms-settings:privacy"])
    except Exception:
        pass


def host_app_hint() -> str:
    """Best guess at which app the user must grant access to."""
    if sys.platform != "darwin":
        return ""
    term = os.environ.get("TERM_PROGRAM", "")
    return {
        "Apple_Terminal": "Terminal",
        "iTerm.app": "iTerm",
        "vscode": "Visual Studio Code",
    }.get(term, "your terminal (or the app you launched DuckHound from)")
