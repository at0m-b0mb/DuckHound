# Changelog

All notable changes to DuckHound are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] — 2026-06-25

### Added
- **Keystroke-injection detection engine** (`core/keystroke.py`) — scores rolling
  windows of keystroke timing on speed, regularity (timing jitter) and sustained run
  length to distinguish machine injection from human typing.
- **Cross-platform USB/HID enumeration** with native backends for macOS
  (`system_profiler`), Linux (`sysfs`) and Windows (`Get-PnpDevice`), degrading
  gracefully when unavailable.
- **Active responses** — alert, alarm, screen-lock, keystroke blocking and device
  de-authorization, each configurable.
- **SOC-style dashboard** — animated radar, eased threat meter, device roster, forensic
  threat log and a live-tunable settings page, in a hand-painted dark Qt theme.
- **Headless CLI** monitor (`--cli`) and a no-permissions **simulation mode** (`--demo`).
- Banner, logo and real in-app screenshots; full README and `docs/HOW_IT_WORKS.md`.
- Unit tests for the detector and settings persistence; GitHub Actions CI.

### Security & privacy
- DuckHound measures keystroke **timing only**, never key content, and performs no
  network access or telemetry.

[1.0.0]: https://github.com/at0m-b0mb/DuckHound/releases/tag/v1.0.0
