"""Generate synthetic Chrome Tracing fixtures with a planted, known hitch.

Each fixture is a normal ~14 ms/frame trace (comfortably under the 16.6 ms
budget) with exactly one injected spike whose span name maps to a KB hitch
pattern. A sidecar ``<trace>.truth.json`` records the ground-truth hitch frame
and cause id, so the evaluation harness can score detection and hypothesis
accuracy. Deterministic: a fixed RNG seed makes regeneration byte-stable.

    python tools/make_fixture.py --scenario gc-spike --out fixtures/synthetic/gc-spike.json
"""
import argparse
import json
import os
import random

PID = 1
MAIN_TID = 1
NUM_FRAMES = 200
HITCH_FRAME = 120
BUDGET_US = 16667

# scenario id (== KB entry id) -> (planted span name, spike duration in us).
# The span names are chosen so their tokens overlap the KB entry's symptoms,
# which is what lets the retriever connect measured evidence to a pattern.
SCENARIOS = {
    "gc-spike":             ("GC.Collect", 25000),
    "physics-burst":        ("Physics2DServer.flush_queries", 22000),
    "sync-asset-load":      ("ResourceLoader.load", 30000),
    "shader-compile":       ("ShaderCompiler.compile", 28000),
    "n2-collision":         ("Collision.broadphase", 20000),
    "spawn-burst":          ("Spawner.spawn_wave", 21000),
    "alloc-churn":          ("Heap.alloc", 18000),
    "serialization-stall":  ("Serializer.write", 24000),
    "event-storm":          ("SignalBus.emit", 19000),
    "scene-tree-traversal": ("SceneTree.propagate", 23000),
}

# Lexical-gap probes: the planted span is a synonym that shares NO tokens with
# the KB entry's symptoms, so keyword/BM25 retrieval can't match it but a
# semantic retriever can. id -> (span name, spike us, true cause_kb_id).
LEXGAP = {
    "lexgap-spawn":  ("WaveSpawner.deploy", 21000, "spawn-burst"),
    "lexgap-gc":     ("MemoryReclaimer.sweep", 25000, "gc-spike"),
    "lexgap-shader": ("PipelineCache.prime", 28000, "shader-compile"),
    "lexgap-asset":  ("TextureStreamer.fetch", 30000, "sync-asset-load"),
}


def resolve(scenario):
    """(span name, spike us, cause_kb_id) for a scenario or lexgap probe."""
    if scenario in SCENARIOS:
        span, dur = SCENARIOS[scenario]
        return span, dur, scenario
    span, dur, cause = LEXGAP[scenario]
    return span, dur, cause


def _x(events, name, ts, dur, tid=MAIN_TID):
    """Append a complete ('X') event in microseconds."""
    events.append({"name": name, "ph": "X", "ts": int(ts), "dur": int(dur),
                   "pid": PID, "tid": tid})


def build_trace(scenario, seed=0):
    """Return a Chrome Tracing dict for one scenario."""
    rng = random.Random(seed)
    spike_name, spike_dur, _cause = resolve(scenario)
    events = []

    # A non-'X' metadata event: ingest must ignore it.
    events.append({"name": "thread_name", "ph": "M", "pid": PID, "tid": MAIN_TID,
                   "args": {"name": "MainThread"}})

    ts = 1_000_000  # arbitrary 1 s offset
    for i in range(NUM_FRAMES):
        frame_start = ts
        cursor = frame_start

        # Normal per-frame work: three sequential top-level (depth 0) spans.
        upd = 3000 + rng.randint(-300, 300)
        _x(events, "Update", cursor, upd); cursor += upd

        phys = 4000 + rng.randint(-400, 400)
        _x(events, "Physics", cursor, phys); cursor += phys

        rend = 7000 + rng.randint(-500, 500)
        _x(events, "Render", cursor, rend)
        # A nested child (depth 1) fully inside Render, to exercise self-time.
        draw = int(rend * 0.7)
        _x(events, "DrawCalls", cursor + (rend - draw) // 2, draw)
        cursor += rend

        # Inject the spike in exactly one frame, as a depth-0 sibling.
        if i == HITCH_FRAME:
            _x(events, spike_name, cursor, spike_dur)
            cursor += spike_dur

        # The frame delimiter span spans all of this frame's work.
        _x(events, "frame", frame_start, cursor - frame_start)
        ts = cursor  # next frame is contiguous

    return {"traceEvents": events, "displayTimeUnit": "ms"}


def truth_path(out):
    base = out[:-5] if out.endswith(".json") else out
    return base + ".truth.json"


def main():
    ap = argparse.ArgumentParser(description="Generate a synthetic hitch trace.")
    ap.add_argument("--scenario", required=True, choices=sorted(SCENARIOS) + sorted(LEXGAP))
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    _span, _dur, cause = resolve(args.scenario)
    trace = build_trace(args.scenario, seed=args.seed)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(trace, f, indent=2)

    with open(truth_path(args.out), "w", encoding="utf-8") as f:
        json.dump({"hitch_frame": HITCH_FRAME, "cause_kb_id": cause}, f, indent=2)

    print(f"wrote {args.out} ({NUM_FRAMES} frames, hitch at {HITCH_FRAME}: {args.scenario} -> {cause})")


if __name__ == "__main__":
    main()
