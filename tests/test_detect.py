import json
import os

from pipeline.ingest import Frame, Trace, load_trace
from pipeline.detect import find_hitches, hitch_threshold_us

FIX = os.path.join("fixtures", "synthetic", "gc-spike.json")


def _truth():
    with open(FIX.replace(".json", ".truth.json"), encoding="utf-8") as f:
        return json.load(f)


def _trace(durations, budget_us=16667):
    frames = [Frame(i, i * 20000, d) for i, d in enumerate(durations)]
    spans = {i: [] for i in range(len(durations))}
    return Trace(frames=frames, spans_by_frame=spans, budget_us=budget_us, source="synthetic")


def test_one_window_on_gc_spike():
    assert len(find_hitches(load_trace(FIX))) == 1


def test_window_covers_ground_truth_frame():
    t = load_trace(FIX)
    hitch = _truth()["hitch_frame"]
    w = find_hitches(t)[0]
    assert w.first_frame <= hitch <= w.last_frame
    assert w.severity > 1.0  # peak is above the frame budget


def test_flat_trace_has_no_hitches():
    assert find_hitches(_trace([14000] * 50)) == []


def test_budget_floor_suppresses_subbudget_outlier():
    durs = [10000] * 50
    durs[25] = 10800  # a relative outlier, but still well under budget
    t = _trace(durs)
    assert hitch_threshold_us(t) == 16667  # floor wins (MAD ~ 0)
    assert find_hitches(t) == []


def test_consecutive_hitches_merge_into_one_window():
    durs = [14000] * 50
    durs[20], durs[21] = 40000, 38000
    w = find_hitches(_trace(durs))
    assert len(w) == 1
    assert (w[0].first_frame, w[0].last_frame) == (20, 21)
    assert w[0].peak_dur_us == 40000
