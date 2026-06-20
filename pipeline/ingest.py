"""Parse Chrome Tracing JSON into a frame series + span tree.

Accepts the array form or {"traceEvents": [...]}. Only complete events
("ph": "X", ts/dur in microseconds) are used. Frames are delimited by a
span named "frame" on the main thread.

Gives back frames (index, start_us, duration_us) and per-frame spans
(name, start_us, duration_us, depth).
"""
import bisect
import json
from collections import Counter
from dataclasses import dataclass

FRAME_NAME = "frame"
DEFAULT_BUDGET_US = 16667  # 60 fps


@dataclass
class Frame:
    index: int
    start_us: int
    dur_us: int


@dataclass
class Span:
    name: str
    start_us: int
    dur_us: int
    depth: int
    tid: int

    @property
    def end_us(self):
        return self.start_us + self.dur_us


@dataclass
class Trace:
    frames: list
    spans_by_frame: dict
    budget_us: int = DEFAULT_BUDGET_US
    source: str = ""


def _raw_events(raw):
    if isinstance(raw, dict):
        return raw.get("traceEvents", [])
    return raw


def _most_common(values):
    return Counter(values).most_common(1)[0][0]


def _assign_depths(spans):
    """Set each span's depth from start/end containment (proper nesting)."""
    spans.sort(key=lambda s: (s.start_us, -s.dur_us))
    open_ends = []  # ancestor end times, innermost last
    for s in spans:
        while open_ends and open_ends[-1] <= s.start_us:
            open_ends.pop()
        s.depth = len(open_ends)
        open_ends.append(s.end_us)


def load_trace(path, budget_us=DEFAULT_BUDGET_US):
    """Read a Chrome Tracing file and return a Trace."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    events = [e for e in _raw_events(raw)
              if e.get("ph") == "X" and "ts" in e and "dur" in e and "name" in e]

    frame_events = [e for e in events if e["name"] == FRAME_NAME]
    if not frame_events:
        raise ValueError(f"{path}: no {FRAME_NAME!r} spans found")

    main_tid = _most_common(e.get("tid", 0) for e in frame_events)
    frame_events = [e for e in frame_events if e.get("tid", 0) == main_tid]
    frame_events.sort(key=lambda e: e["ts"])
    frames = [Frame(i, e["ts"], e["dur"]) for i, e in enumerate(frame_events)]

    spans_by_frame = {f.index: [] for f in frames}
    starts = [f.start_us for f in frames]
    for e in events:
        if e["name"] == FRAME_NAME:
            continue
        idx = bisect.bisect_right(starts, e["ts"]) - 1
        if idx < 0:
            continue  # before the first frame
        frame = frames[idx]
        if e["ts"] >= frame.start_us + frame.dur_us:
            continue  # in a gap between frames (not expected in well-formed traces)
        spans_by_frame[frame.index].append(
            Span(e["name"], e["ts"], e["dur"], 0, e.get("tid", main_tid)))

    for spans in spans_by_frame.values():
        _assign_depths(spans)

    return Trace(frames=frames, spans_by_frame=spans_by_frame,
                 budget_us=budget_us, source=path)
