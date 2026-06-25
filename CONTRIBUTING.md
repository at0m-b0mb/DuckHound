# Contributing to DuckHound

Thanks for your interest in making USB defense better for everyone! 🛡️

## Getting set up

```bash
git clone https://github.com/at0m-b0mb/DuckHound.git
cd DuckHound
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest
```

Run the app in the no-permissions demo mode while you work:

```bash
python run.py --demo
```

## Before you open a PR

```bash
python -m compileall -q duckhound        # nothing should fail to compile
pytest -q tests                          # all tests green
```

If you change the UI, refresh the screenshots:

```bash
QT_QPA_PLATFORM=offscreen QT_SCALE_FACTOR=2 python scripts/capture_screenshots.py
```

## Guidelines

- **Detection logic** lives in `duckhound/core/` and must stay free of Qt imports so it
  remains testable and reusable by the CLI. Add a test for any change to scoring.
- **UI** lives in `duckhound/ui/`. Use the palette and the `rgba()` helper in
  `ui/theme.py` for any translucent colour — never raw 8-digit hex (Qt parses it as
  `#AARRGGBB`).
- Keep it **local-first**: no network calls, no telemetry, and never log keystroke
  *content* — timing only.
- New platform behaviour should degrade gracefully (return empty / no-op) on hosts that
  don't support it, never crash.

## Good first issues

See the roadmap in the [README](README.md#-roadmap) — Linux `pyudev` hotplug events, a
system-tray guard, and packaged installers are all great starting points.
