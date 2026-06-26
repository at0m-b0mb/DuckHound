"""A cross-platform audible alarm for confirmed attacks.

Generates a short two-tone siren WAV once (pure stdlib, no numpy) and plays it
with the OS's native player. Falls back to the system beep if anything fails.
"""
from __future__ import annotations

import math
import struct
import subprocess
import sys
import threading
import wave
from pathlib import Path

from ..config import _config_dir

_WAV = _config_dir() / "alarm.wav"


def _generate(path: Path) -> None:
    rate = 44100
    dur = 1.1
    n = int(rate * dur)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = bytearray()
        for i in range(n):
            t = i / rate
            freq = 1320.0 if int(t * 7) % 2 == 0 else 880.0  # alternating siren
            env = min(1.0, t * 12) * min(1.0, (dur - t) * 6)   # fade in/out
            val = int(0.55 * env * 32767 * math.sin(2 * math.pi * freq * t))
            frames += struct.pack("<h", max(-32768, min(32767, val)))
        w.writeframes(bytes(frames))


def _path() -> Path:
    if not _WAV.exists():
        try:
            _generate(_WAV)
        except Exception:
            pass
    return _WAV


def play() -> None:
    """Play the alarm without blocking the GUI thread."""
    threading.Thread(target=_play_blocking, daemon=True).start()


def _play_blocking() -> None:
    path = _path()
    try:
        if sys.platform == "darwin":
            subprocess.run(["afplay", str(path)], timeout=6)
            return
        if sys.platform.startswith("win"):
            import winsound
            winsound.PlaySound(str(path), winsound.SND_FILENAME)
            return
        for player in ("paplay", "aplay"):
            try:
                subprocess.run([player, str(path)], timeout=6)
                return
            except Exception:
                continue
    except Exception:
        pass
    try:  # last resort
        from PySide6.QtWidgets import QApplication
        QApplication.beep()
    except Exception:
        pass
