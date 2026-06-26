"""Persisted user settings for DuckHound."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


def _config_dir() -> Path:
    """Per-user config directory, following OS conventions."""
    import os
    import sys

    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA", str(Path.home()))
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    d = Path(base) / "DuckHound"
    d.mkdir(parents=True, exist_ok=True)
    return d


CONFIG_PATH = _config_dir() / "config.json"


@dataclass
class Settings:
    # --- Detection sensitivity ---------------------------------------------
    # Max plausible human typing speed. Sustained input faster than this is
    # treated as machine injection. Humans top out ~12-15 chars/sec in bursts.
    fast_interval_ms: int = 30          # keystrokes closer than this are "fast"
    burst_run_length: int = 18          # how many fast keys in a row trips it
    robotic_cv_threshold: float = 0.28  # coeff. of variation below = machine-like
    new_device_grace_s: float = 12.0    # a keyboard typing within Ns of being
    #                                     plugged in is highly suspicious

    # --- Response when a threat is confirmed -------------------------------
    notify: bool = True                 # show in-app + OS notification
    play_sound: bool = True             # audible alert
    lock_screen: bool = False           # lock the workstation immediately
    block_keystrokes: bool = False      # try to swallow injected keystrokes
    deauthorize_device: bool = False    # Linux/Windows: cut power/authorization
    lockdown_new_keyboards: bool = True  # react when an untrusted keyboard appears
    lock_on_lockdown: bool = True        # lock the screen (no special permission!)
    #                                      vs. freeze keystrokes (needs Accessibility)

    # --- General -----------------------------------------------------------
    autostart_monitor: bool = True      # begin monitoring on launch
    minimize_to_tray: bool = True
    trust_internal_keyboard: bool = True  # don't flag the built-in keyboard

    trusted_devices: list[str] = field(default_factory=list)  # allow-listed keys
    trusted_labels: dict = field(default_factory=dict)        # key -> friendly name

    def save(self) -> None:
        CONFIG_PATH.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls) -> "Settings":
        if CONFIG_PATH.exists():
            try:
                data = json.loads(CONFIG_PATH.read_text())
                known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
                return cls(**known)
            except Exception:
                pass
        return cls()
