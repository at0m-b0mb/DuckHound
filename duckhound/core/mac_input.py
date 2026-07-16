"""Native macOS keyboard tap — timing only, no character decoding.

Why this exists: pynput's macOS listener decodes each keycode to a character
using Carbon Text-Input-Source APIs *on its own background thread*. macOS 26
forbids that (it asserts those calls must run on the main thread) and **hard-
crashes the process** the moment the hook initialises — i.e. right after Arm.

DuckHound only needs to know *when* a key was pressed, never *which* one, so we
install a `CGEventTap` that records timing only. No Carbon, no crash.

Both modes run the tap on a **dedicated thread with its own CFRunLoop** so the
callback fires immediately regardless of what the GUI/main thread is doing
(rendering, a modal lockdown dialog, a subprocess) — which is essential for the
*suppress* mode to reliably block injected keystrokes instead of leaking them
when the main thread is busy. The callback never touches Qt objects (detection
just emits a thread-safe Qt signal; suppression just swallows the event), so a
background thread is safe here.
"""
from __future__ import annotations

import threading


class MacKeyTap:
    """A CGEventTap delivering key-down timing to ``on_press``.

    ``suppress=True`` swallows keystrokes (used by Lockdown to freeze input).
    The tap runs on its own thread; ``on_press`` must be thread-safe (e.g. emit
    a queued Qt signal) — do NOT touch Qt widgets/timers from it directly.
    """

    def __init__(self, on_press, suppress: bool = False) -> None:
        self._on_press = on_press
        self._suppress = suppress
        self._tap = None
        self._source = None
        self._runloop = None
        self._cb = None  # strong ref so the callback isn't GC'd
        self._thread = None
        self._ready = threading.Event()
        self._ok = False

    def start(self) -> bool:
        self._thread = threading.Thread(target=self._run, name="DuckHoundTap",
                                        daemon=True)
        self._thread.start()
        self._ready.wait(timeout=2.5)
        return self._ok

    def _run(self) -> None:
        from Quartz import (CFMachPortCreateRunLoopSource, CFRunLoopAddSource,
                            CFRunLoopGetCurrent, CFRunLoopRun, CGEventMaskBit,
                            CGEventTapCreate, CGEventTapEnable,
                            kCFRunLoopCommonModes, kCGEventKeyDown,
                            kCGEventTapOptionDefault, kCGEventTapOptionListenOnly,
                            kCGHeadInsertEventTap, kCGSessionEventTap)

        mask = CGEventMaskBit(kCGEventKeyDown)
        option = (kCGEventTapOptionDefault if self._suppress
                  else kCGEventTapOptionListenOnly)

        def callback(proxy, type_, event, refcon):
            if type_ != kCGEventKeyDown:        # tap-disabled notification
                try:
                    CGEventTapEnable(self._tap, True)
                except Exception:
                    pass
                return event
            try:
                self._on_press()
            except Exception:
                pass
            return None if self._suppress else event

        self._cb = callback
        self._tap = CGEventTapCreate(
            kCGSessionEventTap, kCGHeadInsertEventTap, option, mask, callback, None)
        if not self._tap:
            self._ok = False
            self._ready.set()                    # permission not granted
            return
        self._runloop = CFRunLoopGetCurrent()
        self._source = CFMachPortCreateRunLoopSource(None, self._tap, 0)
        CFRunLoopAddSource(self._runloop, self._source, kCFRunLoopCommonModes)
        CGEventTapEnable(self._tap, True)
        self._ok = True
        self._ready.set()
        CFRunLoopRun()                           # blocks this thread until stopped

    def stop(self) -> None:
        try:
            from Quartz import (CFRunLoopStop, CGEventTapEnable)
            if self._tap is not None:
                CGEventTapEnable(self._tap, False)
            if self._runloop is not None:
                CFRunLoopStop(self._runloop)     # ends CFRunLoopRun → thread exits
        except Exception:
            pass
        self._tap = None
        self._source = None
        self._runloop = None
        self._cb = None
