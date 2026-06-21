# GamePerf-AI

Takes a profiler trace from a game, finds CPU frame hitches and suggests
likely causes, with the evidence to check them against.

Trace format: Chrome Tracing JSON (one "frame" span per frame on the main
thread). Pipeline stages, in order: ingest, detect, analyze, retrieve,
reason — see the docstrings in pipeline/.

Part of my CM3070 final project (BSc Computer Science, University of London).

## Getting set up

You'll need Python 3.10+. From the repo root:

    python -m venv .venv
    .venv\Scripts\activate
    pip install -e .[dev]

That installs the package in editable mode plus pytest. On macOS/Linux the
activate line is `source .venv/bin/activate`.

The `reason` stage talks to a local Ollama running `qwen2.5:7b-instruct`, but
you only need that once the whole pipeline runs end to end — not for anything
below.

## Running the tests

    pytest

Everything's tiny and offline, so it's quick. If that's green, the stages
that are wired up so far are behaving.

## Kicking the tyres

There's no one-command CLI yet (coming once all five stages are in). For now
you can make a sample trace and poke at it stage by stage.

Generate a synthetic trace with one planted hitch:

    python tools/make_fixture.py --scenario gc-spike --out fixtures/synthetic/gc-spike.json

It drops a `*.truth.json` next to the trace recording where the hitch is and
what caused it — handy for checking the pipeline got it right. Other
scenarios you can pass to `--scenario`: physics-burst, sync-asset-load,
shader-compile, n2-collision, spawn-burst, alloc-churn, serialization-stall,
event-storm, scene-tree-traversal.

Then run it through what's built so far (ingest → detect → analyze):

    python -c "import json; from pipeline.ingest import load_trace; from pipeline.detect import find_hitches; from pipeline.analyze import build_evidence; t = load_trace('fixtures/synthetic/gc-spike.json'); print(json.dumps(build_evidence(t, find_hitches(t)[0]), indent=2))"

You should see a hitch window around frame 120 with `GC.Collect` sitting at
the top of the offender list — that's the planted spike being found and
isolated from the normal per-frame work.

The traces are plain Chrome Tracing JSON, so you can also drag them into
`chrome://tracing` or the Perfetto UI and eyeball the frames yourself.

## License

BUSL 1.1, converts to Apache 2.0 in 2030 — see LICENSE.
