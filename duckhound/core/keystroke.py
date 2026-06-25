"""Keystroke-injection detector.

The defining trait of a Rubber Ducky / BadUSB attack is *how* it types: a real
attacker tool replays a payload through an emulated keyboard far faster — and
far more regularly — than a human hand ever could. DuckHound watches the global
keystroke stream and scores each rolling window of keypresses on two axes:

  1. Speed     — inter-keystroke intervals well below human reach.
  2. Regularity — machine timing has almost no jitter; humans are noisy.

A burst that is both *too fast* and *too regular* is flagged. The analyzer is
deliberately pure-Python and dependency-free so it can be unit-tested and reused
by the GUI, the CLI, and the simulator alike.
"""
from __future__ import annotations

import statistics
import time
from collections import deque
from dataclasses import dataclass


@dataclass
class Verdict:
    is_attack: bool
    score: int                 # 0-100 confidence
    cps: float                 # characters per second over the window
    mean_ms: float             # mean inter-keystroke interval
    cv: float                  # coefficient of variation (stdev / mean)
    run_length: int            # consecutive fast keystrokes
    reason: str = ""


class KeystrokeAnalyzer:
    """Sliding-window timing analysis over a stream of keypress timestamps."""

    def __init__(
        self,
        fast_interval_ms: float = 30.0,
        burst_run_length: int = 18,
        robotic_cv_threshold: float = 0.28,
        window: int = 40,
    ) -> None:
        self.fast_interval_ms = fast_interval_ms
        self.burst_run_length = burst_run_length
        self.robotic_cv_threshold = robotic_cv_threshold
        self.window = window
        self._intervals: deque[float] = deque(maxlen=window)
        self._last_ts: float | None = None
        self._fast_run = 0

    def reset(self) -> None:
        self._intervals.clear()
        self._last_ts = None
        self._fast_run = 0

    def update_thresholds(
        self, fast_interval_ms: float, burst_run_length: int, robotic_cv_threshold: float
    ) -> None:
        self.fast_interval_ms = fast_interval_ms
        self.burst_run_length = burst_run_length
        self.robotic_cv_threshold = robotic_cv_threshold

    def feed(self, ts: float | None = None) -> Verdict:
        """Record one keypress (monotonic seconds) and re-score the window."""
        ts = time.monotonic() if ts is None else ts
        if self._last_ts is not None:
            interval_ms = (ts - self._last_ts) * 1000.0
            # Ignore long human pauses — they reset the burst, not the stats.
            if interval_ms <= 1000.0:
                self._intervals.append(interval_ms)
            if interval_ms <= self.fast_interval_ms:
                self._fast_run += 1
            else:
                self._fast_run = 0
        self._last_ts = ts
        return self._score()

    # ------------------------------------------------------------------ #
    def _score(self) -> Verdict:
        n = len(self._intervals)
        if n < 4:
            return Verdict(False, 0, 0.0, 0.0, 0.0, self._fast_run)

        data = list(self._intervals)
        mean_ms = statistics.fmean(data)
        stdev = statistics.pstdev(data) if n > 1 else 0.0
        cv = (stdev / mean_ms) if mean_ms > 0 else 1.0
        cps = 1000.0 / mean_ms if mean_ms > 0 else 0.0

        # --- Speed component: how far below the human ceiling are we? ----
        # 0 at the threshold, 1 when twice as fast (or faster).
        speed = _clamp((self.fast_interval_ms - mean_ms) / self.fast_interval_ms)

        # --- Regularity component: machine timing has near-zero jitter ---
        regular = _clamp((self.robotic_cv_threshold - cv) / self.robotic_cv_threshold)

        # --- Sustained-run component: a long unbroken fast run is damning -
        run = _clamp(self._fast_run / max(self.burst_run_length, 1))

        # Weighted blend, emphasising that an attack must be BOTH fast and
        # sustained; regularity sharpens confidence but can't trip it alone.
        raw = 0.45 * speed + 0.25 * regular + 0.30 * run
        score = int(round(raw * 100))

        is_attack = (
            self._fast_run >= self.burst_run_length
            and mean_ms <= self.fast_interval_ms
            and cv <= self.robotic_cv_threshold * 1.6
        )
        if is_attack:
            score = max(score, 80)

        reason = ""
        if is_attack:
            reason = (
                f"{cps:.0f} keys/s sustained for {self._fast_run} keystrokes "
                f"with machine-like timing (jitter {cv:.0%})"
            )

        return Verdict(is_attack, min(score, 100), cps, mean_ms, cv, self._fast_run, reason)


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))
