# Frame hitch diagnosis

Hitch at frame 120: peak 39.7 ms (2.4x the 16.7 ms budget; median frame 14.0 ms).

## Hypotheses (verify, do not trust)

### 1. A managed-memory garbage collector runs a collection on the main thread, pausing all gameplay code (stop-the-world) until it finishes. — confidence 90%
- pattern: `gc-spike`
- evidence: `GC.Collect`
- confirm: Verify that GC.Collect is indeed the runtime's collector and check for recurring hitches as allocations accumulate. Correlate with managed allocations per frame.
- fix: Pool and reuse objects to cut per-frame managed allocations, avoid allocating in hot loops, and schedule incremental or generational GC where supported.

### 2. The physics engine resolves an unusually large batch of active bodies, contacts or queries in a single step, so the physics flush overruns the frame budget. — confidence 30%
- evidence: `Physics`
- confirm: Compare the active rigid-body and contact count in the hitch frame against neighbours; check for a burst of newly woken or spawned bodies.
- fix: Cap or stagger the number of bodies activated per frame, use simpler collision shapes and sleeping thresholds, or move heavy queries off the hot path.

## Evidence (top offenders by self-time regression)

| span | self-time (µs) | baseline (µs) | regression (µs) |
|---|---:|---:|---:|
| `GC.Collect` | 25000 | 0 | 25000 |
| `DrawCalls` | 5201 | 4963 | 238 |
| `Physics` | 4181 | 4055 | 126 |
| `Render` | 2230 | 2128 | 102 |
| `Update` | 3075 | 2992 | 83 |
