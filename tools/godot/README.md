# Godot tracer + capture harness

`chrome_tracer.gd` is a tiny Chrome Tracing writer. `capture.gd` + `capture.tscn`
are a headless harness that runs a representative per-frame workload through it
and writes a real engine trace (real `Time.get_ticks_usec` timing, real
scheduler jitter — not hand-authored JSON).

## Capture a trace (headless)

From the GamePerf-AI repo root:

    godot --headless --path tools/godot -- --out C:/abs/path/trace.json --frames 200 --hitch 120

The first invocation just imports the project; run it once more to actually
capture. Output is Chrome Tracing JSON that GamePerf-AI ingests directly — the
committed sample is `fixtures/real/godot-capture.json`.

## Drop into a real game (e.g. Arkanoid)

1. Copy `chrome_tracer.gd` into the game project.
2. Project Settings → Autoload: add it as `ChromeTracer`.
3. Bracket each frame and wrap the work you care about:

       func _process(delta):
           ChromeTracer.frame_begin()
           ChromeTracer.begin("AI"); run_ai(); ChromeTracer.end()
           ChromeTracer.begin("Spawn"); spawn(); ChromeTracer.end()
           ChromeTracer.frame_end()

   Call `ChromeTracer.flush("user://trace.json")` when you're done capturing.
4. (Optional) add `hitch_injector.gd` as a node to plant a known `GC.Collect`
   hitch for ground truth while testing, then remove it for a real capture.
