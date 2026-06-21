import json
import os

from pipeline.ingest import load_trace
from pipeline.detect import find_hitches
from pipeline.analyze import build_evidence

FIX = os.path.join("fixtures", "synthetic", "gc-spike.json")


def _bundle():
    t = load_trace(FIX)
    return build_evidence(t, find_hitches(t)[0])


def test_injected_span_is_top_offender():
    b = _bundle()
    top = b["offenders"][0]
    assert top["span"] == "GC.Collect"
    assert top["regression_us"] > 0
    assert top["baseline_us"] == 0  # GC never runs in normal frames


def test_bundle_is_json_serializable():
    b = _bundle()
    assert json.loads(json.dumps(b)) == b


def test_bundle_shape():
    b = _bundle()
    assert set(b) == {"window", "frame_context", "offenders"}
    assert b["window"]["first_frame"] == 120
    assert b["frame_context"]["budget_us"] == 16667
    assert 1 <= len(b["offenders"]) <= 5


def test_self_time_excludes_children():
    # Render (7431-ish) contains DrawCalls (~5201); its self-time must be
    # much smaller than its wall time, and DrawCalls a separate offender.
    b = _bundle()
    names = {o["span"] for o in b["offenders"]}
    assert {"Render", "DrawCalls"} <= names
    render = next(o for o in b["offenders"] if o["span"] == "Render")
    drawcalls = next(o for o in b["offenders"] if o["span"] == "DrawCalls")
    assert render["self_time_us"] < drawcalls["self_time_us"]
