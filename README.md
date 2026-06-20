# GamePerf-AI

Takes a profiler trace from a game, finds CPU frame hitches and suggests
likely causes, with the evidence to check them against.

Trace format: Chrome Tracing JSON (one "frame" span per frame on the main
thread). Pipeline stages, in order: ingest, detect, analyze, retrieve,
reason — see the docstrings in pipeline/.

Part of my CM3070 final project (BSc Computer Science, University of London).

## Development

    python -m venv .venv
    .venv\Scripts\activate
    pip install -e .[dev]
    pytest

Python 3.10+. The reason stage needs a local Ollama with qwen2.5:7b-instruct.

Licensed under BUSL 1.1 (converts to Apache 2.0 in 2030), see LICENSE.
