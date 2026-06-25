# How DuckHound works

A technical look at how DuckHound detects and stops BadUSB / Rubber Ducky
keystroke-injection attacks.

## The threat model

A Rubber Ducky (or any BadUSB gadget — Digispark, Raspberry Pi Pico, a Flipper Zero in
BadUSB mode, a re-flashed flash drive) registers itself on the USB bus as a **Human
Interface Device (HID) keyboard**. To the operating system it is indistinguishable from
a real keyboard, which is exactly why signature-based antivirus rarely stops it.

Once enumerated, it replays a stored payload as a stream of keystrokes — opening a run
dialog or terminal, downloading a stage-2, granting itself persistence — typically in
well under a second.

You cannot tell a malicious "keyboard" from a real one by **what** it is. You *can* tell
by **how it behaves**.

## Two behavioural signatures

### 1. Keystroke timing (primary)

DuckHound installs a global keypress hook (`pynput`) and records only the **monotonic
timestamp** of each press — never the key itself. It keeps a sliding window of
inter-keystroke intervals and continuously scores it.

- **Speed** — humans top out around 12–15 keystrokes/second in short bursts (~120 WPM is
  ~10/s). Injection tools run at 200–3000+/second. Intervals consistently below the
  *human-speed ceiling* (default **30 ms**) are "fast".
- **Regularity** — a human hand produces noisy, variable timing. A microcontroller
  produces near-identical gaps. DuckHound measures the **coefficient of variation**
  (`stdev / mean`); machine input sits well below the *robotic-timing threshold*
  (default **0.28**).
- **Sustained run** — one fast keypress means nothing (key-repeat, a gamer mashing). A
  long unbroken run of fast keys is the tell. Default trip point: **18 keystrokes**.

The window score blends all three:

```
speed     = clamp((ceiling − mean_interval) / ceiling)
regular   = clamp((cv_threshold − cv) / cv_threshold)
run       = clamp(fast_run_length / burst_run_length)

score     = 0.45·speed + 0.25·regular + 0.30·run        # 0–100
```

A threat is **confirmed** only when input is *both* superhumanly fast *and* sustained:

```
is_attack = (fast_run ≥ burst_run_length)
            and (mean_interval ≤ ceiling)
            and (cv ≤ cv_threshold · 1.6)
```

This AND-logic is deliberate: it keeps fast human typists and stuck keys from raising
false alarms, while a real injection burst trips it within ~18–20 keystrokes
(milliseconds).

### 2. Device correlation (amplifier)

In parallel, DuckHound polls the USB bus and diffs successive snapshots to learn when
devices arrive and leave. The signature of a Rubber Ducky is a **brand-new keyboard that
starts typing almost immediately**. When a typing burst is attributed to an input device
that appeared within the *grace window* (default **12 s**), the severity is escalated to
**critical**.

Internal/built-in keyboards and user-trusted devices are exempt.

## Responding to an attack

When a threat is confirmed, the `Responder` runs every countermeasure you've enabled:

| Response | What it does | Platform notes |
|----------|--------------|----------------|
| **Alert** | In-app toast + native OS notification | `osascript` / `notify-send` / PowerShell |
| **Sound** | Audible alarm | Qt system beep |
| **Lock screen** | Immediately locks the workstation | `CGSession` / `loginctl` / `LockWorkStation` |
| **Block keystrokes** | Best-effort suppression of injected input | where the hook supports it |
| **De-authorize** | Surfaces the exact command to cut the device's USB authorization | `/sys/.../authorized`, `pnputil` (needs privilege) |

Every response actually taken is recorded on the threat event and shown in the log, so
you always know precisely what defended you.

## Cross-platform enumeration backends

`duckhound/core/backends/` provides one `enumerate()` implementation per OS, each
dependency-light and **non-fatal** — if a backend can't run, it returns an empty list
and the keystroke detector (the primary defense) keeps working everywhere.

- **macOS** — `system_profiler SPUSBDataType -json`, walked recursively.
- **Linux** — reads `/sys/bus/usb/devices`, classifying via interface descriptors
  (`bInterfaceClass 03` = HID, protocol `01` = keyboard).
- **Windows** — `Get-PnpDevice` over the USB/HID classes, VID/PID parsed from the
  instance id.

## Why timing, not content?

Logging keystroke **content** would make DuckHound a keylogger — the very thing you're
defending against. By measuring only the **time between** keystrokes, DuckHound can prove
an attack is underway without ever knowing what was typed. It's both more private and
more robust: the timing signature holds no matter what payload the Ducky carries.
