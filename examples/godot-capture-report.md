# Frame hitch diagnosis

Hitch at frame 120: peak 39.0 ms (2.3x the 16.7 ms budget; median frame 14.0 ms).

## Hypotheses (verify, do not trust)

### 1. A managed-memory garbage collector runs a collection on the main thread, pausing all gameplay code (stop-the-world) until it finishes. — confidence 90%
- pattern: `gc-spike`
- evidence: `GC.Collect`
- confirm: Verify that GC.Collect is indeed the runtime's garbage collector and check if hitches recur as allocations accumulate. Correlate with managed allocations per frame.
- fix: Pool and reuse objects to cut per-frame managed allocations, avoid allocating in hot loops (boxing, closures, LINQ, temporary arrays), and schedule incremental or generational GC where the runtime supports it.

## Evidence (top offenders by self-time regression)

| span | self-time (µs) | baseline (µs) | regression (µs) |
|---|---:|---:|---:|
| `GC.Collect` | 25004 | 0 | 25004 |
| `Update` | 3001 | 3001 | 0 |
| `Render` | 2002 | 2002 | 0 |
| `Physics` | 4000 | 4001 | -1 |
| `DrawCalls` | 5000 | 5001 | -1 |
