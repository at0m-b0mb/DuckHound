"""Backend contract + a do-nothing fallback."""
from __future__ import annotations

from ..models import Device


class Backend:
    name = "base"
    supported = False

    def enumerate(self) -> list[Device]:
        """Return the current set of connected USB/HID devices."""
        raise NotImplementedError


class NullBackend(Backend):
    """Used on unsupported hosts or when platform libraries are missing.

    Device enumeration is unavailable, but DuckHound's keystroke-injection
    detector — the primary defense — still runs fully.
    """

    name = "unavailable"
    supported = False

    def enumerate(self) -> list[Device]:
        return []
