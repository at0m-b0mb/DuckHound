"""Headless terminal monitor: ``python run.py --cli``.

A no-GUI guardian for servers, kiosks and SSH sessions. Uses the same
detection core as the app: global keystroke timing + USB diffing.
"""
from __future__ import annotations

import sys
import time

from . import APP_NAME, TAGLINE, __version__
from .config import Settings
from .core.backends import get_backend
from .core.keystroke import KeystrokeAnalyzer
from .core.responder import Responder

C = {
    "cyan": "\033[96m", "red": "\033[91m", "yellow": "\033[93m",
    "green": "\033[92m", "dim": "\033[2m", "bold": "\033[1m", "rst": "\033[0m",
}


def _banner() -> None:
    print(f"""{C['cyan']}{C['bold']}
   ___           _   _  _                       _
  |   \\ _  _ __ | |_| || |___ _  _ _ _  __| |
  | |) | || / _||  _| __ / _ \\ || | ' \\/ _` |
  |___/ \\_,_\\__| \\__|_||_\\___/\\_,_|_||_\\__,_|
{C['rst']}  {APP_NAME} v{__version__} — {TAGLINE}
  {C['dim']}Ctrl-C to quit{C['rst']}
""")


def main() -> int:
    settings = Settings.load()
    _banner()
    backend = get_backend()
    responder = Responder(settings)
    analyzer = KeystrokeAnalyzer(
        settings.fast_interval_ms, settings.burst_run_length,
        settings.robotic_cv_threshold,
    )
    known: set[str] = set()

    def log(tag: str, color: str, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        print(f"{C['dim']}{ts}{C['rst']} {color}{tag:>9}{C['rst']}  {msg}")

    log("backend", C["cyan"],
        f"{backend.name} ({'live' if backend.supported else 'keystroke-only'})")

    def on_key(_key) -> None:
        v = analyzer.feed()
        if v.is_attack:
            log("THREAT", C["red"] + C["bold"],
                f"{C['bold']}{v.reason}{C['rst']}")
            actions = responder.respond("BadUSB detected", v.reason)
            if actions:
                log("response", C["green"], ", ".join(actions))
            analyzer.reset()

    try:
        from pynput import keyboard
        listener = keyboard.Listener(on_press=on_key)
        listener.start()
        log("hook", C["green"], "keystroke-injection monitor active")
    except Exception as exc:
        log("hook", C["yellow"], f"keystroke hook unavailable ({exc})")
        listener = None

    try:
        while True:
            snap = {d.key: d for d in backend.enumerate()}
            for key, dev in snap.items():
                if key not in known:
                    known.add(key)
                    tag = "device+"
                    if dev.is_input and not dev.is_internal:
                        log(tag, C["yellow"],
                            f"new input device: {C['bold']}{dev.name}{C['rst']} "
                            f"[{dev.vidpid}] — watching")
                    else:
                        log(tag, C["dim"], f"{dev.name} [{dev.vidpid}]")
            time.sleep(2.5)
    except KeyboardInterrupt:
        print(f"\n{C['dim']}DuckHound stopped.{C['rst']}")
        if listener:
            listener.stop()
        return 0


if __name__ == "__main__":
    sys.exit(main())
