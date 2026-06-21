"""Turn a hitch window into an evidence bundle.

Self-time per span name across the window vs the same spans in nearby
normal frames, top offenders ranked by regression. Bundle is plain JSON:
window, offenders (span, self_time_us, baseline_us, ratio), frame_context
(median_us, budget_us).
"""
from statistics import median

TOP_OFFENDERS = 5
BASELINE_FRAMES = 10


def _self_times(spans):
    """span name -> total self-time (dur minus direct children) over `spans`."""
    totals = {}
    for s in spans:
        child_dur = sum(
            c.dur_us for c in spans
            if c is not s and c.depth == s.depth + 1
            and s.start_us <= c.start_us and c.end_us <= s.end_us
        )
        totals[s.name] = totals.get(s.name, 0) + (s.dur_us - child_dur)
    return totals


def _accumulate(trace, frame_indices):
    totals = {}
    for idx in frame_indices:
        for name, st in _self_times(trace.spans_by_frame.get(idx, [])).items():
            totals[name] = totals.get(name, 0) + st
    return totals


def _baseline_frames(trace, window, n=BASELINE_FRAMES):
    """The nearest <=n non-window frames, fanning out before/after the window."""
    last = len(trace.frames) - 1
    before, after = window.first_frame - 1, window.last_frame + 1
    picked = []
    while len(picked) < n and (before >= 0 or after <= last):
        if before >= 0:
            picked.append(before)
            before -= 1
        if len(picked) < n and after <= last:
            picked.append(after)
            after += 1
    return picked


def build_evidence(trace, window):
    """Return a JSON-serializable evidence bundle for one hitch window."""
    durations = [f.dur_us for f in trace.frames]
    median_us = int(median(durations)) if durations else 0

    hitch = _accumulate(trace, range(window.first_frame, window.last_frame + 1))
    base_frames = _baseline_frames(trace, window)
    base_count = max(len(base_frames), 1)
    base_totals = _accumulate(trace, base_frames)
    baseline = {name: total / base_count for name, total in base_totals.items()}

    offenders = []
    for name, hitch_self in hitch.items():
        base = baseline.get(name, 0.0)
        offenders.append({
            "span": name,
            "self_time_us": int(hitch_self),
            "baseline_us": int(round(base)),
            "ratio": round(hitch_self / (base + 1), 2),
            "regression_us": int(round(hitch_self - base)),
        })
    offenders.sort(key=lambda o: o["regression_us"], reverse=True)

    return {
        "window": {
            "first_frame": window.first_frame,
            "last_frame": window.last_frame,
            "peak_us": window.peak_dur_us,
            "severity": round(window.severity, 2),
        },
        "frame_context": {"median_us": median_us, "budget_us": trace.budget_us},
        "offenders": offenders[:TOP_OFFENDERS],
    }
