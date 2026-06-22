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
activate line is `source .venv/bin/activate`. The package itself is
stdlib-only — nothing to compile, no heavy deps.

The `reason` stage talks to a local [Ollama](https://ollama.com) running
`qwen2.5:7b-instruct`. Once Ollama's installed:

    ollama pull qwen2.5:7b-instruct

It's a ~4.7 GB Q4 model that runs comfortably on an 8 GB GPU. You only need it
for the full run — the `--no-llm` path below skips it entirely.

## Running the tests

    pytest

Everything's tiny and offline (the tests never call the model), so it's quick.
Green means the wired-up stages are behaving.

## Trying it out

Make a synthetic trace with one planted hitch:

    python tools/make_fixture.py --scenario gc-spike --out fixtures/synthetic/gc-spike.json

It drops a `*.truth.json` next to the trace recording where the hitch is and
what caused it — handy for checking the pipeline got it right. Other scenarios
for `--scenario`: physics-burst, sync-asset-load, shader-compile, n2-collision,
spawn-burst, alloc-churn, serialization-stall, event-storm, scene-tree-traversal.

Now run the whole thing on it:

    python -m pipeline.run fixtures/synthetic/gc-spike.json

You get back a markdown report: the hitch (frame 120, ~40 ms against a 16.7 ms
budget), a couple of ranked hypotheses from the model — each one citing the
evidence spans it leaned on — and the offender table underneath. There's a
saved example at `examples/gc-spike-report.md` if you just want to see the shape.
Add `--out report.md` to write to a file instead of stdout.

No Ollama handy? Skip the model and dump the evidence + KB matches instead:

    python -m pipeline.run fixtures/synthetic/gc-spike.json --no-llm

## What's actually doing the work

Since this is a prototype, worth being straight about it: detection is plain
stats (median + MAD) standing in for a time-series model, and retrieval is BM25
over a 10-entry knowledge base standing in for embeddings. The one real model in
the loop right now is the LLM in the reason stage — swapping the placeholders for
proper models is the rest of the project.

The traces are plain Chrome Tracing JSON, so you can also drag them into
`chrome://tracing` or the Perfetto UI and eyeball the frames yourself.

## License

BUSL 1.1, converts to Apache 2.0 in 2030 — see LICENSE.
