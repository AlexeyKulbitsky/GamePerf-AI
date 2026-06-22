# Arkanoid — instrumented sample game

A small but complete Godot 4.5 game (bricks, ball physics, power-ups), wired to
`ChromeTracer` so it emits a real GamePerf-AI trace. Where `tools/godot/` runs a
*synthetic* per-frame workload, this is an actual playable game traced at its
real subsystems — the worked example behind the "drop into a real game" note in
`tools/godot/README.md`.

## What's instrumented

- `chrome_tracer.gd` — the tracer (autoload `ChromeTracer`), with an `enabled`
  flag so it is a no-op during normal play and only records while capturing.
- `trace_session.gd` — the capture harness (autoload `TraceSession`). Inert
  unless launched with `--trace-capture`. It brackets each physics frame, drives
  a tiny autopilot through the real input actions so baseline frames contain
  real gameplay physics, and at the chosen frame plays a **spawn wave**.
- `ball.gd` — `move_and_collide` wrapped as a `Physics` span.
- `game.gd` — the brick-grid build and the multi-ball spawn wrapped as
  `Bricks.instantiate` / `Balls.instantiate` spans.

These are the only edits to the original game; everything else is unchanged.

## The planted hitch is real, just amplified

The spawn wave instantiates `brick.tscn` in a loop until the frame's work
crosses the target duration, then frees them. That is genuine instantiation +
scene-insertion cost landing in one frame — the engine's *spawn-burst*
bottleneck — dialled up so the spike clears the 16.7 ms budget floor and
reproduces on any machine. Nothing is faked: there is no synthetic `GC.Collect`
span (Godot's memory is reference-counted, so a stop-the-world GC pause would
misrepresent the engine) and no hand-authored timing.

## Recapture the trace

From the repo root, import once, then capture:

    GODOT=/path/to/Godot_v4.5.1-stable_console.exe

    "$GODOT" --headless --path examples/arkanoid --import
    "$GODOT" --headless --path examples/arkanoid -- --trace-capture \
        --out "$PWD/fixtures/real/arkanoid-capture.json" \
        --frames 240 --hitch 150 --hitch-us 30000

Then run the pipeline on it:

    python -m pipeline.run fixtures/real/arkanoid-capture.json --out examples/arkanoid-report.md

The committed `fixtures/real/arkanoid-capture.json` and `examples/arkanoid-report.md`
were produced exactly this way. Flags: `--frames` total frames to record,
`--hitch` the frame the spawn wave fires on, `--hitch-us` its target duration.

## Play it normally

    "$GODOT" --path examples/arkanoid

Arrow keys / A-D move, Space launches, Enter or R restart. With no
`--trace-capture` flag the tracer stays off and the game is untouched.
