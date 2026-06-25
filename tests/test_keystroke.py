"""Tests for the keystroke-injection detector — the core of DuckHound."""
import random

from duckhound.core import simulator
from duckhound.core.keystroke import KeystrokeAnalyzer


def _run(analyzer, intervals):
    t, last = 0.0, None
    for iv in intervals:
        t += iv
        last = analyzer.feed(t)
    return last


def test_fast_human_is_not_flagged():
    """Even a quick, noisy human typist must never trip the detector."""
    random.seed(1)
    a = KeystrokeAnalyzer()
    flagged = False
    t = 0.0
    for iv in simulator.human_intervals(150):
        t += iv
        v = a.feed(t)
        flagged = flagged or v.is_attack
    assert not flagged
    assert v.cps < 25


def test_injection_is_flagged_fast():
    """A Rubber Ducky burst must be caught within a couple dozen keystrokes."""
    random.seed(2)
    a = KeystrokeAnalyzer()
    fired_at = None
    t, keys = 0.0, 0
    for iv in simulator.injection_intervals(80, mean_ms=4.0):
        t += iv
        keys += 1
        v = a.feed(t)
        if v.is_attack and fired_at is None:
            fired_at = keys
    assert fired_at is not None
    assert fired_at <= 30
    assert v.score >= 80
    assert v.cps > 100


def test_reset_clears_state():
    random.seed(3)
    a = KeystrokeAnalyzer()
    _run(a, simulator.injection_intervals(40, mean_ms=3.0))
    a.reset()
    v = a.feed(0.0)
    assert v.run_length == 0
    assert v.score == 0
    assert not v.is_attack


def test_threshold_tightening_changes_outcome():
    """Relaxing the run-length requirement should make detection earlier."""
    random.seed(4)
    strict = KeystrokeAnalyzer(burst_run_length=40)
    loose = KeystrokeAnalyzer(burst_run_length=10)
    intervals = list(simulator.injection_intervals(25, mean_ms=4.0))
    sv = _run(strict, intervals)
    lv = _run(loose, intervals)
    # With only 25 keys, the loose analyzer fires while the strict one hasn't yet.
    assert lv.is_attack
    assert not sv.is_attack
