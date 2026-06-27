"""Native macOS keyboard tap — timing only, no character decoding.

Why this exists: pynput's macOS listener decodes each keycode to a character
using Carbon Text-Input-Source APIs *on its own background thread*. macOS 26
forbids that (it asserts those calls must run on the main thread) and **hard-
crashes the process** (`_dispatch_assert_queue_fail` via `TSMGetInputSource…`)
the moment the hook initialises — i.e. right after you press Arm.

DuckHound only needs to know *when* a key was pressed, never *which* one, so we
install a `CGEventTap` on the **main run loop** that records timing only. No
Carbon, no background thread, no crash. Needs Input Monitoring permission; if
it's not granted, `CGEventTapCreate` returns NULL and we report "blind" rather
than crashing.
"""
from __future__ import annotations


class MacKeyTap:
    """A CGEventTap delivering key-down timing to ``on_press`` on the main thread.

    Set ``suppress=True`` to swallow keystrokes (used by Lockdown).
    """

    def __init__(self, on_press, suppress: bool = False) -> None:
        self._on_press = on_press
        self._suppress = suppress
        self._tap = None
        self._source = None
        self._cb = None  # keep a strong ref so the callback isn't GC'd

    def start(self) -> bool:
        from Quartz import (CFMachPortCreateRunLoopSource, CFRunLoopAddSource,
                            CFRunLoopGetMain, CGEventMaskBit, CGEventTapCreate,
                            CGEventTapEnable, kCFRunLoopCommonModes,
                            kCGEventKeyDown, kCGEventTapOptionDefault,
                            kCGEventTapOptionListenOnly, kCGHeadInsertEventTap,
                            kCGSessionEventTap)

        mask = CGEventMaskBit(kCGEventKeyDown)
        option = (kCGEventTapOptionDefault if self._suppress
                  else kCGEventTapOptionListenOnly)

        def callback(proxy, type_, event, refcon):
            # Any non-keydown delivery here is a tap-disabled notification
            # (timeout / user input) — just re-enable and pass through.
            if type_ != kCGEventKeyDown:
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
            return False  # Input Monitoring not granted
        self._source = CFMachPortCreateRunLoopSource(None, self._tap, 0)
        CFRunLoopAddSource(CFRunLoopGetMain(), self._source, kCFRunLoopCommonModes)
        CGEventTapEnable(self._tap, True)
        return True

    def stop(self) -> None:
        try:
            from Quartz import (CFRunLoopGetMain, CFRunLoopRemoveSource,
                                CGEventTapEnable, kCFRunLoopCommonModes)
            if self._tap is not None:
                CGEventTapEnable(self._tap, False)
            if self._source is not None:
                CFRunLoopRemoveSource(CFRunLoopGetMain(), self._source,
                                      kCFRunLoopCommonModes)
        except Exception:
            pass
        self._tap = None
        self._source = None
        self._cb = None
