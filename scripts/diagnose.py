#!/usr/bin/env python3
"""DuckHound self-test — tells you exactly why detection might not be working.

Run:  python scripts/diagnose.py
It checks permissions, the USB backend, the lock method, and then runs a live
6-second keystroke capture so you can confirm the hook actually sees input.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from duckhound.core import permissions                  # noqa: E402
from duckhound.core.backends import get_backend         # noqa: E402
from duckhound.core.keystroke import KeystrokeAnalyzer  # noqa: E402

G, R, Y, C, B, D, X = (
    "\033[92m", "\033[91m", "\033[93m", "\033[96m", "\033[1m", "\033[2m", "\033[0m")


def ok(b):
    return f"{G}PASS{X}" if b else f"{R}FAIL{X}"


def main() -> int:
    print(f"\n{B}{C}DuckHound self-test{X}  ·  {sys.platform}  ·  Python "
          f"{sys.version.split()[0]}\n" + "─" * 56)

    # 1. Permission
    granted, detail = permissions.keystroke_access()
    print(f"[{ok(granted)}] Keystroke-hook permission")
    print(f"        {D}{detail}{X}")
    if not granted:
        host = permissions.host_app_hint()
        print(f"        {Y}→ Grant access to: {B}{host}{X}")
        if sys.platform == "darwin":
            print(f"        {Y}  System Settings → Privacy & Security →{X}")
            print(f"        {Y}  • Input Monitoring   • Accessibility{X}")

    # 2. USB backend
    backend = get_backend()
    devices = []
    try:
        devices = backend.enumerate()
    except Exception as e:
        print(f"        backend error: {e}")
    print(f"[{ok(backend.supported)}] USB enumeration backend: {C}{backend.name}{X}")
    inputs = [d for d in devices if d.is_input]
    print(f"        {D}{len(devices)} device(s), {len(inputs)} input/HID{X}")
    for d in inputs[:6]:
        flag = "internal" if d.is_internal else "EXTERNAL"
        print(f"        {D}· {d.name[:38]:38} [{d.vidpid}] {flag}{X}")

    # 3. Lock capability (dry — we don't actually lock)
    lock_ok = sys.platform.startswith(("linux", "win")) or (
        sys.platform == "darwin"
        and Path("/System/Library/CoreServices/ScreenSaverEngine.app").exists())
    print(f"[{ok(lock_ok)}] Screen-lock response available")

    # 4. Live capture — the real proof
    print("─" * 56)
    print(f"{B}Live keystroke test:{X} type normally for 6 seconds…")
    analyzer = KeystrokeAnalyzer()
    seen = {"n": 0, "attack": False, "peak": 0}
    try:
        from pynput import keyboard

        def on_press(_k):
            seen["n"] += 1
            v = analyzer.feed()
            seen["peak"] = max(seen["peak"], v.score)
            if v.is_attack:
                seen["attack"] = True

        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        for i in range(6, 0, -1):
            print(f"  {C}{i}{X} … (keys captured: {seen['n']})", end="\r", flush=True)
            time.sleep(1)
        listener.stop()
        print(" " * 50, end="\r")
    except Exception as e:
        print(f"  {R}listener error: {e}{X}")

    print(f"[{ok(seen['n'] > 0)}] Captured {B}{seen['n']}{X} keystrokes "
          f"(peak threat score {seen['peak']})")

    # Verdict
    print("─" * 56)
    if seen["n"] == 0 and not granted:
        print(f"{R}{B}✗ The hook is BLIND.{X} It received no keystrokes because the OS")
        print(f"  permission is missing. {B}This is why your Flipper went undetected.{X}")
        print(f"  Fix the permission above, fully quit the app, and relaunch.")
    elif seen["n"] == 0:
        print(f"{Y}No keystrokes captured — did you type during the test?{X}")
    else:
        print(f"{G}{B}✓ The hook works.{X} DuckHound can see keystrokes and will flag")
        print(f"  injection bursts. Run {C}python run.py{X} and arm monitoring.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
