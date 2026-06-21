"""Find hitch windows in the frame-time series.

First version is statistical: a frame is a candidate when its duration
exceeds median + k*MAD, with the frame budget (16.6 ms at 60 fps) as a
floor. Returns HitchWindow(first_frame, last_frame, peak_duration_us,
severity).

Planned replacement: Chronos-Bolt behind the same interface.
"""
from dataclasses import dataclass
from statistics import median


@dataclass
class HitchWindow:
    first_frame: int
    last_frame: int
    peak_dur_us: int
    severity: float


def hitch_threshold_us(trace, k=3.0):
    """Duration above which a frame counts as a hitch.

    max(median + k*MAD, budget): the budget floor stops normal sub-budget
    jitter from being flagged when the frame times are very steady (MAD ~ 0).
    """
    durations = [f.dur_us for f in trace.frames]
    if not durations:
        return trace.budget_us
    med = median(durations)
    mad = median([abs(d - med) for d in durations])
    return max(med + k * mad, trace.budget_us)


def find_hitches(trace, k=3.0):
    """Return hitch windows in frame order; consecutive hitch frames merge."""
    threshold = hitch_threshold_us(trace, k)
    windows = []
    run = None  # [first_index, last_index, peak_dur_us]
    for f in trace.frames:
        if f.dur_us > threshold:
            if run is None:
                run = [f.index, f.index, f.dur_us]
            else:
                run[1] = f.index
                run[2] = max(run[2], f.dur_us)
        elif run is not None:
            windows.append(_window(run, trace.budget_us))
            run = None
    if run is not None:
        windows.append(_window(run, trace.budget_us))
    return windows


def _window(run, budget_us):
    first, last, peak = run
    return HitchWindow(first, last, peak, peak / budget_us)
