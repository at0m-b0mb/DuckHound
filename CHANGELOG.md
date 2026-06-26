# Changelog

All notable changes to DuckHound are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.5] — 2026-06-26

### Fixed
- **Connected devices are now visible before you arm.** The list used to be empty until
  monitoring started; the app now does an initial scan at launch (`engine.enumerate_once`)
  and the Devices page has a **Rescan** button to refresh on demand — so you can always
  see, trust and revoke keyboards.
- **No more spurious lockdowns.** Lockdown now fires only for a genuinely *first-seen
  keyboard* (tracked in `_ever_seen`) — not a mouse, and not a Logitech receiver that
  flickers in and out of `ioreg`, which could make arming feel broken.
- **Smoother arming** — USB poll relaxed from 400ms to 800ms to reduce UI jank from the
  `ioreg` subprocess on the main thread.

## [1.0.4] — 2026-06-26

### Added
- **Persistent device allow-list.** Approve your real keyboards once and only *unknown*
  devices ever trigger a lock. The Devices page now has an **Allow-list** card with a
  one-click **"Trust all connected"** baseline button, friendly device names, and
  **Revoke** on every trusted entry; trusting persists across restarts
  (`trusted_devices` + `trusted_labels`). Engine gains `untrust_device`,
  `trust_all_current`, `trusted_list` and an `allowlist_changed` signal.

### Note
- A device on the allow-list is intentionally skipped by detection and Lockdown. If a
  Ducky/Flipper ever stops triggering, check the Allow-list and **Revoke** it — approving
  the lockdown prompt for an attacker device whitelists it.

## [1.0.3] — 2026-06-25

### Added / Changed
- **macOS detection that actually works on Apple Silicon.** The USB backend now uses
  `ioreg` over `IOHIDInterface` (fast, no permission, classifies keyboards by HID usage)
  instead of `system_profiler SPUSBDataType`, which returned nothing on Apple Silicon.
  A Rubber Ducky / Flipper is now spotted the instant it enumerates.
- **Neutralize without keystroke permissions.** Lockdown can now **lock the screen** when
  an untrusted keyboard appears (new `lock_on_lockdown`, on by default). Screen-locking
  needs no Input Monitoring / Accessibility grant, and the injected keystrokes land
  harmlessly on the lock screen. (Enable *System Settings → Lock Screen → "Require
  password immediately"* so the lock demands a password.)
- **Faster polling** (~0.9s on macOS/Linux) so a rogue device is caught within ~1s.
- `python run.py --grant` (trigger the macOS permission prompts) and `--doctor` (self-test).

### Note
- This release un-trusts all devices on first run if you had previously trusted a
  BadUSB-capable gadget by mistake — re-approve real keyboards via the Lockdown dialog.

## [1.0.2] — 2026-06-25

### Added
- **🔒 Lockdown mode** (on by default) — when an untrusted keyboard is connected, or a
  keystroke-injection burst is detected, DuckHound freezes *all* keyboard input and shows
  a mouse-only modal to Approve (trust) or Block. Approving trusts the device and
  unfreezes; blocking keeps it frozen until the device is unplugged. A 30-second failsafe
  and auto-release-on-unplug guarantee you can never be locked out by a bug. Only devices
  that appear *after* monitoring is armed trigger it, so your existing keyboard is safe.

## [1.0.1] — 2026-06-25

### Fixed
- **Blind keyboard hook.** On macOS the global hook needs Input Monitoring /
  Accessibility; without it `pynput` reported `running` while receiving zero
  keystrokes, so real attacks (e.g. a Flipper Zero) went undetected. DuckHound now
  preflights the permission, shows a dismissable warning banner with a **Grant Access**
  button, and runs an 8-second watchdog that flags a hook receiving no input.
- **Screen lock on modern macOS.** The old `CGSession` path was removed in recent macOS;
  lock now falls back through ScreenSaverEngine → Ctrl-Cmd-Q → display sleep.

### Added
- `duckhound/core/permissions.py` — cross-platform permission preflight/prompt.
- **Keystroke blocking** response — briefly suppresses input to neutralize the rest of an
  injected payload.
- `scripts/diagnose.py` — a self-test that confirms whether the hook can actually see
  keystrokes (live capture), plus the USB backend and lock capability.
- README **Troubleshooting** section.

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

[1.0.5]: https://github.com/at0m-b0mb/DuckHound/releases/tag/v1.0.5
[1.0.4]: https://github.com/at0m-b0mb/DuckHound/releases/tag/v1.0.4
[1.0.3]: https://github.com/at0m-b0mb/DuckHound/releases/tag/v1.0.3
[1.0.2]: https://github.com/at0m-b0mb/DuckHound/releases/tag/v1.0.2
[1.0.1]: https://github.com/at0m-b0mb/DuckHound/releases/tag/v1.0.1
[1.0.0]: https://github.com/at0m-b0mb/DuckHound/releases/tag/v1.0.0
