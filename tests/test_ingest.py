import json
import os

from pipeline.ingest import load_trace

FIX = os.path.join("fixtures", "synthetic", "gc-spike.json")


def _truth():
    with open(FIX.replace(".json", ".truth.json"), encoding="utf-8") as f:
        return json.load(f)


def test_loads_all_frames():
    t = load_trace(FIX)
    assert len(t.frames) == 200


def test_frame_starts_are_monotonic():
    t = load_trace(FIX)
    starts = [f.start_us for f in t.frames]
    assert all(b > a for a, b in zip(starts, starts[1:]))


def test_injected_frame_is_the_largest():
    t = load_trace(FIX)
    peak = max(range(len(t.frames)), key=lambda i: t.frames[i].dur_us)
    assert peak == _truth()["hitch_frame"]


def test_spans_assigned_with_sane_depth():
    t = load_trace(FIX)
    hitch = _truth()["hitch_frame"]
    spans = t.spans_by_frame[hitch]
    names = {s.name for s in spans}
    assert "GC.Collect" in names
    assert names >= {"Update", "Physics", "Render", "DrawCalls"}
    assert all(s.depth >= 0 for s in spans)
    # DrawCalls is nested one level inside Render.
    draw = next(s for s in spans if s.name == "DrawCalls")
    assert draw.depth == 1


def test_accepts_raw_array_form(tmp_path):
    events = [
        {"name": "frame", "ph": "X", "ts": 0, "dur": 1000, "pid": 1, "tid": 1},
        {"name": "Work", "ph": "X", "ts": 100, "dur": 500, "pid": 1, "tid": 1},
        {"name": "thread_name", "ph": "M", "pid": 1, "tid": 1, "args": {}},
    ]
    p = tmp_path / "raw.json"
    p.write_text(json.dumps(events), encoding="utf-8")
    t = load_trace(str(p))
    assert len(t.frames) == 1
    assert [s.name for s in t.spans_by_frame[0]] == ["Work"]
